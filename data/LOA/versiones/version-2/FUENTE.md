# Fuente de los datos

Copiados de `frr05/Arbol-Rutas-` (pipeline MT con Muse Spark, sin OCR), rama `main`, commit `8d25618a848bd73cc6f112380efc5b7680b71651`, carpeta «Primera Concesión Rutas del Loa», el 2026-11-18. Árbol generado el 2026-11-18 18:25 (3 783 nodos, 13 actos); la verificación del pipeline (`revision/verificacion.md`, 18:26) terminó en OK.

**Aviso:** en `Arbol-Rutas-` estos archivos tienen cambios sin commit sobre `8d25618` (`nodos_versionados.json`, `revision/actos.csv`, `cache/estructura/bases.json` modificados; `cache/fragmentos/LOA.D01.json` nuevo, sin seguimiento). Lo copiado es el estado del disco a las 18:23–18:26, no el del commit.

Es una versión nueva sobre la base de `data/LOA/` (árbol de 16:49); la base no se reemplaza.

| Archivo | Origen en Arbol-Rutas- |
|---|---|
| nodos_versionados.json | árbol de nodos versionados |
| actos.csv | revision/actos.csv |
| bases.json | cache/estructura/bases.json |
| fragmentos/ | cache/fragmentos/ (ahora incluye LOA.D01.json) |
| texto/ | cache/texto/ (sin cambios desde 15:39; idéntico al de la base) |

No hay vectores bge-m3 (`EMBEDDINGS_LOA.npz`) para esta concesión, así que el grafo no tiene relaciones de similitud ni «artículos más parecidos», y los grupos salen solo de las citas entre artículos.
