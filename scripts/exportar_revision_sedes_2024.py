"""Prepara CSV locales para revisión humana de sedes puntuales pendientes."""

from pathlib import Path

import pandas as pd

from scripts.match_ieeq_encartes import ENCARTES, parse_encarte


ROOT = Path(__file__).resolve().parents[1]
CARPETA = ROOT / "data/electoral/ieeq_local"


def exportar() -> tuple[Path, Path]:
    puntos = pd.read_parquet(CARPETA / "casillas_2024_puntos.parquet")
    pendientes = puntos.loc[puntos.CALIDAD.eq("revisar_domicilio_o_poligono")].copy()
    encarte = parse_encarte(ENCARTES[2024], 2024)[
        ["ID_SECCION", "CASILLA", "LOCALIDAD_NOMBRE", "DOMICILIO"]]
    pendientes = pendientes.merge(
        encarte, left_on=["ID_SECCION", "CASILLA_ETIQUETA"],
        right_on=["ID_SECCION", "CASILLA"], validate="one_to_one")
    pendientes["MOTIVO_REVISION"] = pendientes.DOMICILIO_COINCIDE.map(
        {True: "Punto fuera del polígono seccional", False: "Domicilio difiere del encarte"})
    sitios = sorted(set(zip(pendientes.ID_SECCION, pendientes.LATITUD, pendientes.LONGITUD)))
    claves = {sitio: f"SEDE-{i:02d}" for i, sitio in enumerate(sitios, 1)}
    pendientes["GRUPO_SEDE"] = [claves[clave] for clave in zip(
        pendientes.ID_SECCION, pendientes.LATITUD, pendientes.LONGITUD)]
    pendientes["MAPA_GOOGLE"] = [
        f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        for lat, lon in zip(pendientes.LATITUD, pendientes.LONGITUD)]
    pendientes["COORDENADA_EXACTA"] = ""
    pendientes["OBSERVACIONES"] = ""
    detalle = pendientes.drop(columns="CASILLA").rename(columns={
        "CASILLA_ETIQUETA": "CASILLA", "LOCALIDAD_NOMBRE": "LOCALIDAD_ENCARTE",
        "DOMICILIO": "DOMICILIO_ENCARTE", "SEDE": "SEDE_FUENTE",
        "DOMICILIO_FUENTE": "DIRECCION_FUENTE", "LATITUD": "LATITUD_FUENTE",
        "LONGITUD": "LONGITUD_FUENTE",
    })[["GRUPO_SEDE", "ID_SECCION", "CASILLA", "MOTIVO_REVISION",
        "LOCALIDAD_ENCARTE", "DOMICILIO_ENCARTE", "SEDE_FUENTE",
        "DIRECCION_FUENTE", "LATITUD_FUENTE", "LONGITUD_FUENTE",
        "MAPA_GOOGLE", "COORDENADA_EXACTA", "OBSERVACIONES"]]
    detalle = detalle.sort_values(["GRUPO_SEDE", "CASILLA"])
    grupos = detalle.groupby("GRUPO_SEDE", sort=True)
    resumen = grupos.first().reset_index()
    resumen.insert(3, "CASILLAS_DEL_GRUPO", grupos.CASILLA.agg(lambda x: ", ".join(x)).to_numpy())
    resumen.insert(4, "NUM_CASILLAS", grupos.size().to_numpy())
    resumen = resumen.drop(columns="CASILLA")
    ruta_detalle = CARPETA / "revision_manual_73_casillas_2024.csv"
    ruta_sedes = CARPETA / "revision_manual_15_sedes_2024.csv"
    detalle.to_csv(ruta_detalle, index=False, encoding="utf-8-sig")
    resumen.to_csv(ruta_sedes, index=False, encoding="utf-8-sig")
    return ruta_detalle, ruta_sedes


if __name__ == "__main__":
    for ruta in exportar():
        print(ruta)
