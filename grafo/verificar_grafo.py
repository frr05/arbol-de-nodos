"""Verifica las salidas de una concesión antes de publicarlas en GitHub Pages.

Uso:  python grafo/verificar_grafo.py <ID>

Comprueba, para cada versión de data/<ID>/ (la base y data/<ID>/versiones/*):
- que existan salida/grafo_<ID>[_ver].html, .graphml, resumen_<ID>[_ver].md y disposicion_<ID>[_ver].json;
- que los datos incrustados en el HTML se lean como JSON, sean de la concesión y del árbol copiado (mismo `generado`),
  tengan al menos tantos nodos como el árbol, todas las aristas apunten a nodos existentes y todo nodo tenga x, y finitos;
- que el GraphML se cargue con networkx y tenga los mismos nodos.
Además, que el visor con todas las versiones (index.html para RITP, salida/visor_<ID>.html para las demás) traiga
todas las versiones, y que concesiones.html enlace a ese visor. Termina con "verificación OK" o con código 1.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import networkx as nx

RAIZ = Path(__file__).resolve().parent.parent


def bloques(html: str) -> dict[str, str]:
    return dict(re.findall(r'<script id="([\w-]+)" type="application/json">(.*?)</script>', html, re.S))


def main():
    cid = sys.argv[1] if len(sys.argv) > 1 else "RITP"
    d = RAIZ / "data" / cid
    salida = RAIZ / "salida"
    errores: list[str] = []
    rutas = [("", d / "nodos_versionados.json")] + [
        (p.parent.name, p) for p in sorted((d / "versiones").glob("*/nodos_versionados.json"))]
    for nombre, ruta in rutas:
        sufijo = f"_{nombre}" if nombre else ""
        arbol = json.loads(ruta.read_text(encoding="utf-8"))
        etiqueta = f"{cid} {nombre or 'base'}"
        faltan = [f for f in (f"grafo_{cid}{sufijo}.html", f"grafo_{cid}{sufijo}.graphml", f"resumen_{cid}{sufijo}.md",
                              f"disposicion_{cid}{sufijo}.json") if not (salida / f).exists()]
        if faltan:
            errores.append(f"{etiqueta}: faltan {', '.join(faltan)}")
            continue
        html = (salida / f"grafo_{cid}{sufijo}.html").read_text(encoding="utf-8")
        if f"<title>Grafo {cid}</title>" not in html:
            errores.append(f"{etiqueta}: el título de la pestaña no es «Grafo {cid}»")
        datos = json.loads(bloques(html)["datos-0"])
        if datos["concesion"]["id"] != cid or datos.get("generado") != arbol.get("generado"):
            errores.append(f"{etiqueta}: los datos son de {datos['concesion']['id']} {datos.get('generado')}, "
                           f"no del árbol copiado ({arbol.get('generado')})")
        nodos, aristas = datos["nodos"], datos["aristas"]
        if len(nodos) < len(arbol["nodos"]):
            errores.append(f"{etiqueta}: {len(nodos)} nodos en el grafo, menos que los {len(arbol['nodos'])} del árbol")
        malas = [a for a in aristas if not (0 <= a[0] < len(nodos) and 0 <= a[1] < len(nodos))]
        if malas:
            errores.append(f"{etiqueta}: {len(malas)} aristas apuntan a nodos inexistentes")
        sin_xy = [n["i"] for n in nodos if not (math.isfinite(n.get("x", math.nan)) and math.isfinite(n.get("y", math.nan)))]
        if sin_xy:
            errores.append(f"{etiqueta}: {len(sin_xy)} nodos sin posición (p. ej. {sin_xy[0]})")
        G = nx.read_graphml(salida / f"grafo_{cid}{sufijo}.graphml")
        if G.number_of_nodes() != len(nodos):
            errores.append(f"{etiqueta}: el GraphML tiene {G.number_of_nodes()} nodos y el visor {len(nodos)}")
        print(f"{etiqueta}: {len(nodos)} nodos, {len(aristas)} relaciones, {len(datos['comunidades'])} grupos"
              + (f" · notas: {'; '.join(datos['notas'])}" if datos.get("notas") else ""))
    visor = RAIZ / ("index.html" if cid == "RITP" else f"salida/visor_{cid}.html")
    if not visor.exists():
        errores.append(f"falta {visor.relative_to(RAIZ).as_posix()}")
    else:
        b = bloques(visor.read_text(encoding="utf-8"))
        n_vers = len(json.loads(b["versiones"]))
        if n_vers != len(rutas):
            errores.append(f"{visor.name}: trae {n_vers} versiones y data/{cid} tiene {len(rutas)}")
    portada = RAIZ / "concesiones.html"
    enlace = visor.relative_to(RAIZ).as_posix()
    if not portada.exists() or f'href="{enlace}"' not in portada.read_text(encoding="utf-8"):
        errores.append(f"concesiones.html no enlaza a {enlace}")
    if errores:
        print("\n".join(["", "ERRORES:"] + [f"- {e}" for e in errores]))
        sys.exit(1)
    print("verificación OK")


if __name__ == "__main__":
    main()
