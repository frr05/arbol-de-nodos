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

## Abrir el grafo

Abre `salida/grafo_RITP.html` en el navegador. Es un solo archivo, con los datos incluidos, y no necesita servidor.

- **Clic en un nodo:** resalta todas sus conexiones y abre su ficha. La ficha muestra:
  - qué es el nodo y su ruta (parte › capítulo › artículo);
  - el acto y el documento de origen, con las páginas;
  - el texto vigente y el historial de versiones (qué acto cambió qué y cuándo);
  - sus conexiones agrupadas por tipo. Cada conexión lleva a ese nodo, y el botón «Atrás» vuelve al anterior.
- **Buscar:** por numeral (`1.8.5.1`), por acto (`Circular aclaratoria N°4`) o por una palabra del texto (`multa`).
- **Filtros:** mostrar u ocultar cada tipo de nodo y de relación, resaltar un acto o un capítulo.
- **Moverse:**
  - la rueda o el pellizco acercan y alejan;
  - arrastrar el fondo desplaza la vista;
  - arrastrar un nodo lo mueve;
  - doble clic centra un nodo.

  El enlace `#n<número>` abre el grafo con ese nodo seleccionado.

`salida/grafo_RITP.graphml` contiene el mismo grafo para Gephi o yEd, con las posiciones calculadas. `salida/resumen_RITP.md` tiene el conteo de nodos y relaciones por tipo.

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
