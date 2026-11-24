# Fuente de los datos

Copiados de `frr05/Arbol-Rutas-` (pipeline MT con Muse Spark, sin OCR), rama `nodos-spark`, commit `e67ecabe43c1f2ea067d35acf08416f2c99af135`, carpeta «Concesión Ruta Interportuaria Talcahuano _ Penco», el 2026-11-24. Árbol generado el 2026-11-24 11:56 (2111 nodos); la verificación del pipeline (`revision/verificacion.md`) terminó en OK.

| Archivo | Origen en Arbol-Rutas- |
|---|---|
| nodos_versionados.json | árbol de nodos versionados |
| actos.csv | revision/actos.csv |
| bases.json | cache/estructura/bases.json |
| fragmentos/, texto/ | cache/fragmentos/, cache/texto/ |

No hay vectores bge-m3 (`EMBEDDINGS_RITP.npz`) para esta concesión, así que el grafo no tiene relaciones de similitud ni «artículos más parecidos», y los grupos salen solo de las citas entre artículos.

Reemplaza por completo la copia anterior de RITP (rama `ver-estable-arbol` de `frr05/MT-v3`, 2026-11-06, y su versión 2026-11-11), que se quitó de `data/RITP/` y de `salida/`.
