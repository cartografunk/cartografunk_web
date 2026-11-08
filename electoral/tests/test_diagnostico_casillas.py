"""Conservación, cobertura territorial y perfiles sin replicar CPV por casilla."""

import numpy as np
import pandas as pd

from electoral.cpv import ETIQUETAS
from electoral.diagnostico_casillas import (
    cobertura, costo_hipotetico, evaluar_partido, incorporar_apoyo_minimo,
    lista_revision, perfil_cpv, preparar_casillas, proponer_esfuerzo,
)
from electoral.reparto_ieeq import COMBINACIONES, INDEPENDIENTES, PROPIOS


def _insumos():
    filas = []
    for sec, tipo, numero, pan, morena, combinacion, incluir in [
        ("22-0001", "B", 1, 40, 20, 0, True),
        ("22-0001", "C", 1, 35, 25, 0, True),
        ("22-0002", "B", 1, 20, 40, 6, True),
        ("22-0003", "E", 1, 10, 40, 0, True),
        ("22-0004", "B", 1, 10, 40, 0, True),
        ("22-0001", "S", 1, 3, 9, 0, False),
    ]:
        fila = {col: 0 for col in (*PROPIOS[2024], *COMBINACIONES[2024], *INDEPENDIENTES[2024])}
        fila.update(ID_SECCION=sec, TIPO_NORMALIZADO=tipo, ID_CASILLA=numero,
                    ID_DISTRITO_LOCAL=1, INCLUIR_SECCION=incluir, PAN=pan, MORENA=morena,
                    **{"PAN-PRI-PRD": combinacion})
        fila["TOTAL_VOTOS"] = pan + morena + combinacion
        fila["LISTA_NOMINAL"] = 100
        fila["NULOS"] = 0
        fila["NO_REGISTRADAS"] = 0
        filas.append(fila)
    casillas = pd.DataFrame(filas)
    casillas["FILA_FUENTE"] = range(1, len(casillas) + 1)
    casillas["CASILLA_ETIQUETA"] = casillas.TIPO_NORMALIZADO + casillas.ID_CASILLA.astype(str)
    cruce = pd.DataFrame({"ID_SECCION": [f"22-000{i}" for i in range(1, 5)],
                         "CATEGORIA": ["sin_cambio_cartografico_referencia"] * 3
                                      + ["dividida_o_reconfigurada"]})
    cpv = pd.DataFrame({"ID_SECCION": cruce.ID_SECCION,
                        **{col: [20, 40, 60, 80] for col in ETIQUETAS}})
    return casillas, cruce, cpv


def test_cruce_reparto_y_exclusion_especial():
    base = preparar_casillas(*_insumos())
    assert len(base) == 5
    assert base.LISTA_NOMINAL.sum() == 500
    assert base.loc[base.ID_SECCION.eq("22-0002"), "PAN"].iloc[0] == 22
    assert base.loc[base.ID_SECCION.eq("22-0004"), "pct_mujeres"].isna().all()
    assert cobertura(evaluar_partido(base, "PAN"))["secciones_cpv"] == 3


def test_perfil_cuenta_seccion_una_vez_por_clase():
    base = evaluar_partido(preparar_casillas(*_insumos()), "PAN")
    perfil = perfil_cpv(base)
    assert perfil["n_secciones_por_clase"]["ganada_solida"] == 1
    assert perfil["tabla"].loc[0, "n_secciones_ganada_solida"] == 1
    assert len(perfil["tabla"]) == 15
    assert np.isnan(perfil["tabla"].loc[0, "dif_est_ganada_solida_vs_perdida_lejana"])
    assert "perdida_lejana" in cobertura(base)["sin_cpv_por_clase"]


def test_distancia_y_accion_son_hipotesis():
    base = proponer_esfuerzo(evaluar_partido(preparar_casillas(*_insumos()), "PAN"))
    cercana = base.loc[base.ID_SECCION.eq("22-0002")].iloc[0]
    assert cercana.CLASE == "perdida_lejana"
    assert cercana.VOTOS_PARA_LIDERAR == 19  # PAN 22, MORENA 40
    assert cercana.ABSTENCION == 34
    assert cercana.ACCION_HIPOTESIS == "Observar antes de invertir"
    assert base.loc[base.ID_SECCION.eq("22-0001"), "ACCION_HIPOTESIS"].eq(
        "Presencia ligera y conservación").all()


def test_apoyo_y_costo_son_dimensiones_separadas():
    base = proponer_esfuerzo(evaluar_partido(preparar_casillas(*_insumos()), "PAN"))
    apoyo = pd.DataFrame({"ID_SECCION": ["22-0001", "22-0002"],
                          "partido": ["PAN", "PAN"], "piso_pct": [33.0, 15.0]})
    salida = costo_hipotetico(incorporar_apoyo_minimo(base, apoyo, "PAN"), 25)
    fila = salida.loc[salida.ID_SECCION.eq("22-0002")].iloc[0]
    assert fila.APOYO_MINIMO_FEDERAL_2024_PCT == 15
    assert fila.COSTO_HIPOTETICO == 475
    assert salida.loc[salida.ID_SECCION.eq("22-0001"), "COSTO_HIPOTETICO"].isna().all()
    assert pd.isna(salida.loc[salida.ID_SECCION.eq("22-0004"),
                              "APOYO_MINIMO_FEDERAL_2024_PCT"].iloc[0])


def test_votos_sobre_lista_no_crean_abstencion_aparente():
    base = preparar_casillas(*_insumos())
    base.loc[base.ID_SECCION.eq("22-0002"), "TOTAL_VOTOS"] = 120
    salida = proponer_esfuerzo(evaluar_partido(base, "PAN"))
    fila = salida.loc[salida.ID_SECCION.eq("22-0002")].iloc[0]
    assert fila.VOTOS_SOBRE_LISTA
    assert pd.isna(fila.ABSTENCION)
    assert not fila.ALCANZABLE_ABSTENCION
    assert fila.ACCION_HIPOTESIS == "Revisar votos sobre lista"


def test_encarte_aporta_localidad_de_instalacion_sin_cambiar_cpv():
    casillas, cruce, cpv = _insumos()
    encarte = casillas.loc[casillas.INCLUIR_SECCION, ["ID_SECCION", "CASILLA_ETIQUETA"]].rename(
        columns={"CASILLA_ETIQUETA": "CASILLA"}).copy()
    encarte["LOCALIDAD_INE"] = 17
    encarte["LOCALIDAD_NOMBRE"] = "LOCALIDAD DE INSTALACIÓN"
    salida = preparar_casillas(casillas, cruce, cpv, encarte)
    assert len(salida) == 5
    assert salida.LOCALIDAD_INSTALACION.eq("LOCALIDAD DE INSTALACIÓN").all()
    assert salida.loc[salida.ID_SECCION.eq("22-0004"), "pct_mujeres"].isna().all()


def test_lista_revision_explica_reglas_y_no_infiere_votos_captables():
    base = evaluar_partido(preparar_casillas(*_insumos()), "PAN")
    base.loc[base.ID_SECCION.eq("22-0002"), "CLASE"] = "perdida_competitiva"
    base.loc[base.ID_SECCION.eq("22-0001"), "CLASE"] = "ganada_ajustada"
    salida = lista_revision(costo_hipotetico(base, 25), presupuesto=500)
    assert len(salida) == 3
    assert salida.iloc[0].TIPO_REVISION == "Examinar pérdida cercana"
    assert salida.iloc[0].VOTOS_PARA_LIDERAR == 19
    assert salida.iloc[0].DENTRO_PRESUPUESTO_SUPUESTO == True
    assert "comprobar en campo" in salida.iloc[0].MOTIVO_REVISION
    assert salida.TIPO_REVISION.tolist().count("Defender ventaja cercana") == 2


def test_lista_revision_no_convierte_votos_sobre_lista_en_oportunidad():
    base = evaluar_partido(preparar_casillas(*_insumos()), "PAN")
    base.loc[base.ID_SECCION.eq("22-0002"), "VOTOS_SOBRE_LISTA"] = True
    salida = lista_revision(base)
    assert salida.loc[salida.ID_SECCION.eq("22-0002"), "TIPO_REVISION"].iloc[0] == "Revisar dato electoral"


def test_lista_revision_incluye_empate_sin_llamarlo_victoria():
    base = evaluar_partido(preparar_casillas(*_insumos()), "PAN")
    base.loc[base.ID_SECCION.eq("22-0003"), "CLASE"] = "empate"
    salida = lista_revision(base)
    fila = salida.loc[salida.ID_SECCION.eq("22-0003")].iloc[0]
    assert fila.TIPO_REVISION == "Examinar empate"
    assert "Empate partidario" in fila.MOTIVO_REVISION
