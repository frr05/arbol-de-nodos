# Árbol de nodos · grafo interactivo

Grafo completo de una concesión de obras públicas de Chile (DGC, MOP), armado a partir del **árbol de nodos versionados** que genera el proyecto MT-v3. Reúne en una sola red:
- todo el texto de las Bases de Licitación (partes, capítulos, artículos e incisos);
- los documentos y actos administrativos posteriores (circulares, decretos, convenios, resoluciones…);
- las relaciones entre todo ello.

La idea visual sigue el «Product Space» de Hidalgo y Hausmann:
- nodos de colores por categoría;
- un núcleo denso y una periferia;
- etiquetas de grupo alrededor de la red.

Hoy contiene la **Ruta Interportuaria Talcahuano – Penco (RITP)**.

## Ver en línea

Con GitHub Pages activo, el grafo se abre en **https://frr05.github.io/arbol-de-nodos/**. `index.html` es el mismo visor de `salida/grafo_RITP.html` y lo regenera el script.

Para activarlo, una sola vez:
1. Entra a *Settings → Pages* del repo.
2. En *Build and deployment*, elige *Source: Deploy from a branch*.
3. Elige *Branch: `main`* y la carpeta *`/ (root)`*, y guarda con *Save*.

La primera publicación tarda uno o dos minutos. `.nojekyll` hace que Pages sirva los archivos tal cual.

## Abrir el grafo

Abre `salida/grafo_RITP.html` en el navegador. Es un solo archivo, con los datos incluidos, y no necesita servidor.

- **Clic en un nodo:** resalta todas sus conexiones y abre su ficha. La ficha muestra:
  - qué es el nodo y su ruta (parte › capítulo › artículo);
  - el acto y el documento de origen, con las páginas;
  - el texto vigente y el historial de versiones (qué acto cambió qué y cuándo);
  - sus conexiones agrupadas por tipo. Cada conexión lleva a ese nodo, y el botón «Atrás» vuelve al anterior.
- **Leer texto completo**, botón de la ficha: abre el texto entero del artículo o capítulo, con sus subartículos, en tres vistas:
  - *vigente con cambios*: agregado y quitado, palabra por palabra, con el acto que hizo cada cambio;
  - *vigente limpio*;
  - *original de las Bases*.

  Incluye además las instrucciones y actos que tocan ese texto.
- **Buscar:** por numeral (`1.8.5.1`), por acto (`Circular aclaratoria N°4`) o por una palabra del texto (`multa`).
- **Filtros:** mostrar u ocultar cada tipo de nodo y de relación, resaltar un acto o un capítulo.
- **Moverse:**
  - la rueda o el pellizco acercan y alejan;
  - arrastrar el fondo desplaza la vista;
  - arrastrar un nodo lo mueve;
  - doble clic centra un nodo.

  El enlace `#n<número>` abre el grafo con ese nodo seleccionado.

### Indicadores

La pestaña **Indicadores** resume la red con todos los actos y muestra entre paréntesis el cambio respecto de las Bases solas. Cada nodo cuenta desde el acto de su primera versión; la estructura de las Bases, desde las Bases. Una cita entre artículos cuenta cuando existen los dos artículos. Cada fila lleva al nodo en el grafo.

| Indicador | Qué mide |
|---|---|
| Artículos más citados | Menciones desde otros artículos y desde los fragmentos de los actos |
| Capítulos citados desde más partes | Cuántos capítulos y actos distintos citan al capítulo: qué tan transversal es |
| Lo más central (cercanía) | Distancia media, en saltos de cita o modificación, a los demás artículos y actos, con el puesto en PageRank |
| Actos más transversales | Capítulos distintos que toca cada acto, con sus modificaciones, ubicaciones y menciones |
| Capítulos más modificados | Versiones creadas por actos posteriores a las Bases |
| Temas de los actos posteriores | Fragmentos agrupados por tema (obras, régimen económico, tarifas…) |

### Grupos, similares y segmentación local

- **Pestaña Grupos.** Muestra grupos de artículos que se citan entre sí o hablan de lo mismo. Se detectan con comunidades Louvain sobre las citas y la similitud de contenido, con resolución 1,3 (`--resolucion`).
  - Cada grupo lleva sus palabras más distintivas (tf-idf entre grupos), sus capítulos y sus artículos más conectados. Los demás nodos heredan el grupo de su artículo; un fragmento o acto, el del grupo que más toca.
  - El botón «por grupo», sobre el grafo, colorea los nodos con estos grupos.
  - Debajo van los **pares de artículos muy parecidos que no se citan** ni son padre e hijo: candidatos a redundancias o a reglas que conviene leer juntas.
- **En la ficha de un artículo:**
  - **Más parecidos por contenido:** los 8 artículos con mayor coseno bge-m3.
  - **Segmentar desde aquí:** PageRank personalizado sobre las relaciones visibles. Resalta los 40 nodos más ligados al nodo elegido y los ordena. Si apagas algunos tipos de relación en Filtros, la segmentación cambia.

La posición en el dibujo no es un indicador: el centro lo ocupan los nodos conectados con muchos grupos distintos (sobre todo las circulares), no necesariamente los más citados.

`salida/grafo_RITP.graphml` contiene el mismo grafo para Gephi o yEd, con las posiciones calculadas y, en cada nodo y arista, el acto desde el que existe (`acto_origen`, `acto_desde`). `salida/resumen_RITP.md` tiene el conteo de nodos y relaciones por tipo.

## Qué hay en el grafo

| Nodos | Origen |
|---|---|
| Documento PDF, acto administrativo | `actos` del árbol y `actos.csv` |
| Fragmento de un acto | `fragmentos/` (cortes de cada acto), cuando no es ya un nodo del árbol |
| Raíz, portada, parte, capítulo, artículo, inciso | estructura de las Bases en el árbol |
| Acto posterior, instrucción, aclaración, formalidad, tema, tabla, ficha | lo que el árbol colgó de cada artículo o tema |

| Relación | Significado |
|---|---|
| Jerarquía | padre → hijo en el árbol |
| Procedencia | documento → acto → fragmento |
| Modifica | fragmento (o acto) → nodo cuya versión creó: reemplaza, agrega o elimina un artículo, párrafo o texto |
| Ubica | fragmento → aclaración o instrucción donde quedó su texto |
| Cita | artículo → artículo de las Bases que menciona («según 1.8.5.1») |
| Cita desde un acto | fragmento → artículo de las Bases que menciona |
| Similitud | artículo ↔ artículo de contenido parecido. Coseno de los vectores bge-m3 promediados por artículo: árbol de expansión máxima más los pares más parecidos. Apagada por defecto. |

**Color:** los ocho capítulos con más nodos. Los demás capítulos van en gris, con su etiqueta igual alrededor del grafo. Los documentos y actos son cuadrados oscuros.

**Forma:**
- círculos: el texto de las Bases;
- cuadrados: los documentos, los actos y lo que proviene de ellos;
- rombos: temas, tablas y ficha.

**Tamaño:** crece con la cantidad de conexiones.

**Disposición:** se calcula una vez con ForceAtlas2 (modo LinLog, semilla fija) sobre todas las relaciones menos la similitud, y queda guardada en `salida/disposicion_RITP.json`.

## Regenerar

```bash
pip install -r requirements.txt
python grafo/armar_grafo.py RITP          # unos 4 minutos la primera vez; después reutiliza la disposición
```

El script lee `data/RITP/` y escribe todo en `salida/`. `grafo/plantilla.html` es el visor: HTML, CSS y JavaScript sin librerías externas, con un lienzo `<canvas>`.

## Datos

`data/RITP/` es una copia de los archivos del árbol estable de MT-v3 (ver `data/RITP/FUENTE.md`, con la rama y el commit):
- `nodos_versionados.json`;
- los chunks y vectores bge-m3;
- `actos.csv`;
- la estructura de las Bases;
- los fragmentos y el texto por línea.

El texto viene del OCR de los documentos públicos de la concesión, publicados por la DGC, y se mantiene literal. Puede tener errores de lectura, como «1,14» por «1.14».

`grafo/numerales.py` es una copia de `mt/numerales.py` de MT-v3, para comparar numerales igual que el pipeline (`L6.32` = `1.6.32` = `I.6.32`).
