"""Renderiza 20 casos preseleccionados para revisión visual del crosswalk ECEG-2024."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pyogrio

from scripts.build_ieeq_crosswalk import CURRENT, OLD_ZIPS, OUTPUT, load_old


def render() -> None:
    eceg = load_old(OLD_ZIPS["eceg_2021_01_20"])
    current = pyogrio.read_dataframe(CURRENT, layer="SECCIONES_2024", where="ENTIDAD = 22")
    current = current.set_crs(32614, allow_override=True).to_crs(eceg.crs)
    current["ID_SECCION"] = "22-" + current.SECCION.astype(int).astype(str).str.zfill(4)
    old = eceg.set_index("ID_SECCION")
    new = current.set_index("ID_SECCION")
    sample = pd.read_csv(OUTPUT / "crosswalk_muestra_revision.csv")
    links = pd.read_parquet(OUTPUT / "crosswalk_eceg_2021_a_2024.parquet")
    fig, axes = plt.subplots(4, 5, figsize=(15, 12))
    for ax, row in zip(axes.flat, sample.itertuples(index=False)):
        section = row.ID_SECCION
        origins = links.loc[links.DESTINO.eq(section), "ORIGEN"]
        if len(origins):
            old.loc[origins].geometry.plot(ax=ax, facecolor="none", edgecolor="#1764a7", linewidth=1.3)
        new.loc[[section]].geometry.plot(ax=ax, facecolor="none", edgecolor="#df5c27", linewidth=1.3)
        ax.set_title(f"{section} · {row.CATEGORIA}\nIoU={row.IOU_MISMA_CLAVE:.4f}", fontsize=7)
        ax.set_axis_off()
    fig.suptitle("Azul: ECEG 20-ene-2021 · naranja: 2024 original", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUTPUT / "crosswalk_muestra_revision.png", dpi=150)


if __name__ == "__main__":
    render()
