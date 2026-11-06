"""Arma el grafo completo de una concesión desde el árbol de nodos versionados de MT-v3.

Uso:  python grafo/armar_grafo.py [RITP] [--iter 600] [--fragmento ruta.html]

Entrada: data/<ID>/ (copia de MT-v3, ver data/<ID>/FUENTE.md).
Salida:  salida/grafo_<ID>.html (visor interactivo autónomo), salida/grafo_<ID>.graphml (Gephi / yEd)
         y salida/resumen_<ID>.md (conteo de nodos y aristas por tipo).

Nodos: documentos PDF, actos, fragmentos de los actos y todos los nodos del árbol (partes, capítulos, artículos,
incisos, aclaraciones, instrucciones, actos posteriores, temas, formalidades, tablas…).
Aristas (cada tipo se puede ocultar en el visor):
  jerarquia    padre → hijo del árbol
  procedencia  documento → acto → fragmento (y acto de las Bases → raíz de las Bases)
  modifica     fragmento (o acto) → nodo cuya versión creó: reemplaza, agrega, elimina…
  ubica        fragmento → aclaración o instrucción del árbol donde quedó su texto
  cita         artículo → artículo de las Bases que menciona su texto ("según 1.8.5.1")
  cita_acto    fragmento → artículo de las Bases que menciona
  similitud    artículo ↔ artículo con contenido parecido (vectores bge-m3; árbol de expansión máxima + umbral)
La disposición se calcula aquí (ForceAtlas2 de networkx, semilla fija) con todas las aristas menos la similitud.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from numerales import citas, clave_numero  # noqa: E402  (copia de MT-v3/mt/numerales.py)

RAIZ = Path(__file__).resolve().parent.parent
MAX_TEXTO = 1500          # caracteres de texto por nodo en el visor
MAX_VERSION = 400         # caracteres por versión anterior
PESOS = {"jerarquia": 1.0, "procedencia": 0.6, "modifica": 1.5, "ubica": 1.0, "cita": 0.25, "cita_acto": 0.25}


def titulo_normal(n: dict) -> str:
    """Título con el numeral normalizado ("1,3 DEL PROYECTO" → "1.3 DEL PROYECTO"), como mt/ensamblar._titulo."""
    t, num = n.get("titulo") or "", n.get("numero")
    if n.get("tipo") not in ("parte", "capitulo", "articulo") or not num or num == "0" or num.startswith("A"):
        return t
    resto = re.sub(r"^\s*[\dIlL]{1,3}(?:\s?[.,]\s?[\dIlL]{1,3})*[.)]?\s*", "", t)
    return f"{num} {resto}".strip()


def recortar(t: str, n: int) -> str:
    t = (t or "").strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + " …"


def nombre_corto(a: dict) -> str:
    tipo = (a.get("tipo") or "").capitalize()
    num = a.get("numero")
    return f"{tipo} N°{num}" if num and num != "None" else tipo


class Grafo:
    def __init__(self, cid: str):
        self.cid = cid
        self.d = RAIZ / "data" / cid
        self.arbol = json.loads((self.d / "nodos_versionados.json").read_text(encoding="utf-8"))
        self.nodos: dict[str, dict] = {}            # id → nodo del visor
        self.aristas: list[tuple[str, str, str, str]] = []
        self.vistas: set[tuple] = set()

    # --- construcción ---------------------------------------------------------------------------------
    def nodo(self, nid: str, **datos):
        if nid not in self.nodos:
            self.nodos[nid] = {"id": nid} | datos
        return self.nodos[nid]

    def arista(self, s: str, t: str, tipo: str, op: str = ""):
        if s == t or s not in self.nodos or t not in self.nodos or (s, t, tipo) in self.vistas:
            return
        self.vistas.add((s, t, tipo))
        self.aristas.append((s, t, tipo, op or ""))

    def armar(self):
        arbol = self.arbol
        actos = arbol["actos"]
        self.actos = {a["id"]: a for a in actos}
        filas_actos = {f["acto"]: f for f in csv.DictReader(open(self.d / "actos.csv", encoding="utf-8-sig"),
                                                            delimiter=";")}
        # documentos y actos
        for a in actos:
            doc = a.get("documento") or {}
            fila = filas_actos.get(a["id"], {})
            self.nodo(doc["id"], tipo="documento", etiqueta=doc["id"].split(".")[-1], titulo=doc.get("titulo") or doc["id"],
                      texto=f"Documento PDF {doc['id']}: {doc.get('titulo') or ''}")
            pags = a.get("paginas") or []
            self.nodo(a["id"], tipo="acto", etiqueta=nombre_corto(a), titulo=a.get("nombre") or a["id"],
                      acto=a["id"], fecha=a.get("fecha"), paginas=pags,
                      texto=(f"{a.get('nombre')}. Documento {doc['id']} «{doc.get('titulo') or ''}»"
                             + (f", págs. {pags[0]}–{pags[-1]}" if pags else "")
                             + (f". Título leído: {fila.get('titulo')}" if fila.get("titulo") else "") + "."))
        # nodos del árbol
        for n in arbol["nodos"]:
            vs = n.get("versiones") or []
            vig = next((v for v in reversed(vs) if v.get("vigente")), vs[-1] if vs else {})
            acto = (vig.get("acto") or {}).get("id") if isinstance(vig.get("acto"), dict) else None
            titulo = titulo_normal(n)
            self.nodo(n["id"], tipo=n["tipo"], etiqueta=self.etiqueta(n, titulo), titulo=titulo, ruta=n.get("ruta"),
                      numero=n.get("numero"), acto=acto, fecha=vig.get("fecha_desde"), paginas=vig.get("paginas") or [],
                      texto=recortar(vig.get("texto"), MAX_TEXTO),
                      versiones=[{"acto": (v.get("acto") or {}).get("id"), "op": v.get("operacion") or v.get("relacion"),
                                  "fecha": v.get("fecha_desde"), "vigente": bool(v.get("vigente")),
                                  "texto": recortar(v.get("texto"), MAX_VERSION)} for v in vs] if len(vs) > 1 else [])
        # fragmentos de los actos (los que no son ya un nodo del árbol)
        self.frag_de_linea: dict[tuple[str, int], str] = {}
        self.fragmentos: dict[str, dict] = {}
        for ruta in sorted((self.d / "fragmentos").glob("*.json")):
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            frags = datos["fragmentos"] if isinstance(datos, dict) else datos
            doc = ruta.stem
            lineas = {ln["i"]: ln for ln in json.loads((self.d / "texto" / f"{doc}.json").read_text(
                encoding="utf-8"))["lineas"]}
            for f in frags:
                self.fragmentos[f["id"]] = f
                for i in f["lineas"]:
                    self.frag_de_linea[(doc, i)] = f["id"]
                if f["id"] not in self.nodos:
                    texto = "\n".join(lineas[i]["texto"] for i in f["lineas"] if i in lineas and not lineas[i]["marginal"])
                    a = self.actos.get(f["acto"], {})
                    self.nodo(f["id"], tipo="fragmento", etiqueta=f["id"].split(".")[-1],
                              titulo=f"{a.get('nombre', f['acto'])} · fragmento {f['id'].split('.')[-1]}",
                              acto=f["acto"], fecha=a.get("fecha"), paginas=f.get("pags") or [],
                              texto=recortar(texto, MAX_TEXTO), ajeno=bool(f.get("ajeno")))
        self.aristas_estructura()
        self.aristas_citas()
        self.grupos()

    @staticmethod
    def etiqueta(n: dict, titulo: str) -> str:
        t = n["tipo"]
        if t in ("parte", "capitulo", "articulo") and n.get("numero"):
            return n["numero"] if n["numero"] != "0" else "Portada"
        if t == "inciso":
            m = re.search(r"-i(\d+)$", n["id"])
            base = n["id"].split(":", 1)[-1].split("-")[0]
            return f"{base} ¶{m.group(1)}" if m else n["id"]
        if t in ("acto_posterior", "formalidad") and n.get("fragmento"):
            return n["fragmento"].split(".")[-1]
        return recortar(titulo, 40)

    def aristas_estructura(self):
        arbol = self.arbol
        for a in arbol["actos"]:
            self.arista(a["documento"]["id"], a["id"], "procedencia")
            if a.get("tipo") == "bases licitacion" and "BASES" in self.nodos:
                self.arista(a["id"], "BASES", "procedencia")
        for fid, f in self.fragmentos.items():
            self.arista(f["acto"], fid, "procedencia")
        modificados: set[str] = set()
        for n in arbol["nodos"]:
            if n.get("padre"):
                self.arista(n["padre"], n["id"], "jerarquia")
            if n.get("fragmento") and n["fragmento"] != n["id"]:
                self.arista(n["fragmento"], n["id"], "ubica")
            for v in n.get("versiones") or []:
                op = v.get("operacion")
                if not op:
                    continue
                origen = None
                for bloque in v.get("lineas") or []:
                    for i in bloque.get("lineas") or []:
                        origen = origen or self.frag_de_linea.get((bloque.get("doc"), i))
                origen = origen or (v.get("acto") or {}).get("id")
                if origen:
                    self.arista(origen, n["id"], "modifica", op)
                    modificados.add(n["id"])
            for campo, op in (("agregado_por", "agrega"), ("eliminado_por", "elimina")):
                quien = n.get(campo)
                if isinstance(quien, dict) and n["id"] not in modificados:
                    self.arista(quien["id"], n["id"], "modifica", op)

    def aristas_citas(self):
        nodos = {n["id"]: n for n in self.arbol["nodos"]}
        self.articulos = {clave_numero(n["numero"]): n["id"] for n in self.arbol["nodos"]
                          if n["tipo"] == "articulo" and n["id"].startswith("BL:") and n.get("numero")}

        def articulo_de(n):
            while n and n["tipo"] != "articulo":
                n = nodos.get(n.get("padre"))
            return n

        for n in self.arbol["nodos"]:
            if n["tipo"] != "inciso" or not n["id"].startswith("BL:"):
                continue
            a = articulo_de(n)
            if not a:
                continue
            for c in citas(self.nodos[n["id"]]["texto"]):
                destino = self.articulos.get(clave_numero(c))
                if destino and destino != a["id"]:
                    self.arista(a["id"], destino, "cita")
        for fid, f in self.fragmentos.items():
            for r in f.get("refs") or []:
                destino = self.articulos.get(clave_numero(r))
                if destino:
                    self.arista(fid, destino, "cita_acto")

    def grupos(self):
        """Grupo de color = capítulo de las Bases (subiendo por padres); los ocho más grandes llevan color."""
        padre = {n["id"]: n.get("padre") for n in self.arbol["nodos"]}
        for s, t, k, _ in self.aristas:
            if k == "ubica":
                padre.setdefault(t, s)
        cap = {}
        for nid, n in self.nodos.items():
            x, vistos = nid, set()
            while x and x not in vistos:
                vistos.add(x)
                if self.nodos.get(x, {}).get("tipo") == "capitulo":
                    cap[nid] = x
                    break
                x = padre.get(x)
        tam = Counter(cap.values())
        self.capitulos = [c for c, _ in tam.most_common()]
        for nid, n in self.nodos.items():
            n["capitulo"] = cap.get(nid)

    def datar(self):
        """Acto de origen (`origen`) y de eliminación (`hasta`) de cada nodo, como índice en el orden de aplicación de
        los actos, y acto desde el que existe cada arista (`desde`). Sirve para ver el grafo «hasta el acto k»."""
        orden = {a["id"]: k for k, a in enumerate(self.arbol["actos"])}
        por_id = {n["id"]: n for n in self.arbol["nodos"]}
        hijos = defaultdict(list)
        for s_, t, k, _ in self.aristas:
            if k == "jerarquia":
                hijos[s_].append(t)
        acto_id = lambda x: x.get("id") if isinstance(x, dict) else None
        propio, fin = {}, {}
        for nid, n in self.nodos.items():
            t = n["tipo"]
            if t in ("acto", "fragmento"):
                propio[nid] = orden.get(n["acto"])
            elif t == "documento":
                propio[nid] = min(orden[a["id"]] for a in self.arbol["actos"] if a["documento"]["id"] == nid)
            elif nid in por_id:
                a = por_id[nid]
                vs = a.get("versiones") or []
                k = orden.get(acto_id(a.get("agregado_por"))) if a.get("agregado_por") else None
                if k is None and vs:
                    k = orden.get(acto_id(vs[0].get("acto")))
                if k is None and (t in ("articulo", "capitulo", "parte", "portada") or nid == "BASES"):
                    k = 0                          # estructura de las Bases: existe desde ellas aunque sus incisos cambien
                if k is not None:
                    propio[nid] = k
                # la versión eliminada lleva el acto de su texto; el que la elimina está en `reemplazado_por`
                el = [orden.get(v.get("reemplazado_por")) for v in vs if v.get("relacion") == "eliminado"]
                if a.get("eliminado_por"):
                    el.append(orden.get(acto_id(a["eliminado_por"])))
                el = [x for x in el if x is not None]
                if el:
                    fin[nid] = min(el)
        memo: dict[str, int] = {}

        def origen(nid, pila=()):
            if nid in memo:
                return memo[nid]
            if nid in propio:
                r = propio[nid]
            else:                                  # sin dato propio (temas, raíces, artículos sin versiones): sus hijos
                hs = [origen(h, pila + (nid,)) for h in hijos.get(nid, []) if h not in pila]
                r = min(hs) if hs else 0
            memo[nid] = r
            return r

        for nid, n in self.nodos.items():
            n["origen"] = origen(nid)
        # lo eliminado arrastra a sus descendientes
        pila = list(fin)
        while pila:
            nid = pila.pop()
            for h in hijos.get(nid, []):
                if self.nodos[h]["tipo"] in ("instruccion", "aclaracion", "acto_posterior", "tabla"):
                    continue                       # la nota del acto que elimina sigue a la vista
                if fin.get(h, 10**9) > fin[nid]:
                    fin[h] = fin[nid]
                    pila.append(h)
        for nid, k in fin.items():
            self.nodos[nid]["hasta"] = k
        propios = ("modifica", "ubica", "cita_acto", "procedencia")
        self.desde = [self.nodos[s_]["origen"] if k in propios else max(self.nodos[s_]["origen"], self.nodos[t]["origen"])
                      for s_, t, k, _ in self.aristas]

    def similitud(self, por_nodo: float = 2.0):
        """Artículo ↔ artículo por coseno de sus vectores promedio: árbol de expansión máxima + pares sobre un umbral
        que deja unas `por_nodo` aristas por artículo en total."""
        z = np.load(self.d / f"EMBEDDINGS_{self.cid}.npz", allow_pickle=True)
        vec = dict(zip([str(i) for i in z["ids"]], z["vectores"]))
        grupos = defaultdict(list)
        for linea in (self.d / f"CHUNKS_{self.cid}.jsonl").read_text(encoding="utf-8").splitlines():
            c = json.loads(linea)
            m = c["metadatos"]
            art = (m.get("articulo") or {}).get("id")
            if m.get("vigente") and art in self.nodos and c["id"] in vec:
                grupos[art].append(vec[c["id"]])
        ids = sorted(grupos)
        if len(ids) < 3:
            return
        M = np.array([np.mean(grupos[i], axis=0) for i in ids], dtype=np.float32)
        M /= np.linalg.norm(M, axis=1, keepdims=True).clip(1e-9)
        S = M @ M.T
        n = len(ids)
        # árbol de expansión máxima (Prim)
        dentro = np.zeros(n, bool)
        dentro[0] = True
        mejor, de = S[0].copy(), np.zeros(n, int)
        pares = set()
        for _ in range(n - 1):
            cand = np.where(dentro, -np.inf, mejor)
            j = int(np.argmax(cand))
            pares.add((min(j, de[j]), max(j, de[j])))
            dentro[j] = True
            mas = S[j] > mejor
            mejor[mas], de[mas] = S[j][mas], j
        objetivo = int(por_nodo * n)
        iu = np.triu_indices(n, 1)
        orden = np.argsort(-S[iu])
        for k in orden:
            if len(pares) >= objetivo:
                break
            pares.add((int(iu[0][k]), int(iu[1][k])))
        self.umbral_similitud = float(min(S[i, j] for i, j in pares))
        for i, j in sorted(pares):
            self.arista(ids[i], ids[j], "similitud", f"{S[i, j]:.2f}")

    # --- disposición ----------------------------------------------------------------------------------
    def disponer(self, iteraciones: int):
        """Posiciones con ForceAtlas2. Se guardan en salida/disposicion_<ID>.json y se reutilizan mientras no cambien
        los nodos, las aristas ni las iteraciones (calcularlas toma unos minutos)."""
        n_aristas = sum(a[2] in PESOS for a in self.aristas)
        cache = RAIZ / "salida" / f"disposicion_{self.cid}.json"
        if cache.exists():
            guardado = json.loads(cache.read_text(encoding="utf-8"))
            if (guardado.get("iter"), guardado.get("aristas"), set(guardado.get("pos", {}))) == \
                    (iteraciones, n_aristas, set(self.nodos)):
                for nid, n in self.nodos.items():
                    n["x"], n["y"] = guardado["pos"][nid]
                print(f"  disposición reutilizada de {cache.name}")
                return
        G = nx.Graph()
        G.add_nodes_from(self.nodos)
        for s, t, k, _ in self.aristas:
            if k in PESOS:
                w = PESOS[k] + (G[s][t]["weight"] if G.has_edge(s, t) else 0)
                G.add_edge(s, t, weight=w)
        # LinLog separa más los grupos (capítulos, actos); los nodos sin aristas se acercan al centro al escalar
        pos = nx.forceatlas2_layout(G, max_iter=iteraciones, seed=7, weight="weight", scaling_ratio=2.0,
                                    gravity=1.0, linlog=True)
        xy = np.array([pos[n] for n in self.nodos], dtype=float)
        xy -= np.median(xy, axis=0)
        r = np.hypot(xy[:, 0], xy[:, 1])
        xy /= max(np.percentile(r, 98), 1e-9)
        r = np.hypot(xy[:, 0], xy[:, 1])
        lejos = r > 1.08                                   # los pocos nodos sueltos quedan en el borde, no a kilómetros
        xy[lejos] *= (1.08 / r[lejos])[:, None]
        for (nid, n), (x, y) in zip(self.nodos.items(), xy):
            n["x"], n["y"] = round(float(x), 4), round(float(-y), 4)
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps({"iter": iteraciones, "aristas": n_aristas,
                                     "pos": {nid: [n["x"], n["y"]] for nid, n in self.nodos.items()}},
                                    separators=(",", ":")), encoding="utf-8")

    # --- salidas --------------------------------------------------------------------------------------
    def datos_visor(self) -> dict:
        ids = list(self.nodos)
        idx = {nid: k for k, nid in enumerate(ids)}
        actos = list(self.actos.values())
        idx_acto = {a["id"]: k for k, a in enumerate(actos)}
        caps = self.capitulos
        idx_cap = {c: k for k, c in enumerate(caps)}
        nodos = []
        for nid in ids:
            n = self.nodos[nid]
            o = {"i": nid, "k": n["tipo"], "l": n.get("etiqueta") or nid, "t": n.get("titulo") or nid,
                 "x": n["x"], "y": n["y"]}
            for clave, campo in (("r", "ruta"), ("f", "fecha"), ("tx", "texto")):
                if n.get(campo):
                    o[clave] = n[campo]
            if n.get("paginas"):
                o["pg"] = [n["paginas"][0], n["paginas"][-1]]
            if n.get("acto") in idx_acto:
                o["a"] = idx_acto[n["acto"]]
            if n.get("capitulo") in idx_cap:
                o["g"] = idx_cap[n["capitulo"]]
            if n.get("ajeno"):
                o["aj"] = 1
            o["o"] = n.get("origen", 0)
            if n.get("hasta") is not None:
                o["h"] = n["hasta"]
            if n.get("versiones"):
                o["v"] = [[idx_acto.get(v["acto"], -1), v["op"] or "", v["fecha"] or "", 1 if v["vigente"] else 0,
                           v["texto"]] for v in n["versiones"]]
            nodos.append(o)
        aristas = [[idx[s], idx[t], k, op, d] for (s, t, k, op), d in zip(self.aristas, self.desde)]
        return {"concesion": self.arbol["concesion"], "generado": self.arbol.get("generado"),
                "actos": [{"i": a["id"], "n": a.get("nombre"), "c": nombre_corto(a), "tipo": a.get("tipo"),
                           "f": a.get("fecha"), "d": a["documento"]["id"]} for a in actos],
                "capitulos": [{"i": c, "t": self.nodos[c]["titulo"], "n": self.nodos[c].get("numero")} for c in caps],
                "nodos": nodos, "aristas": aristas, "umbral_similitud": round(getattr(self, "umbral_similitud", 0), 3)}

    def graphml(self, ruta: Path):
        orden = [a["id"] for a in self.arbol["actos"]]
        G = nx.DiGraph()
        for nid, n in self.nodos.items():
            G.add_node(nid, tipo=n["tipo"], etiqueta=n.get("etiqueta") or "", titulo=n.get("titulo") or "",
                       capitulo=n.get("capitulo") or "", acto=n.get("acto") or "", fecha=n.get("fecha") or "",
                       x=float(n["x"]) * 1000, y=float(n["y"]) * 1000, texto=(n.get("texto") or "")[:500],
                       acto_origen=orden[n.get("origen", 0)], acto_eliminado=orden[n["hasta"]] if n.get("hasta") is not None else "")
        for (s, t, k, op), d in zip(self.aristas, self.desde):
            if G.has_edge(s, t):                # GraphML simple: una arista por par, tipos unidos
                G[s][t]["tipo"] += "+" + k
            else:
                G.add_edge(s, t, tipo=k, operacion=op, acto_desde=orden[d])
        nx.write_graphml(G, ruta)
        return G

    def resumen(self) -> str:
        kn = Counter(n["tipo"] for n in self.nodos.values())
        ka = Counter(k for _, _, k, _ in self.aristas)
        ops = Counter(op for _, _, k, op in self.aristas if k == "modifica")
        lineas = [f"# Grafo {self.cid} · {self.arbol['concesion']['nombre']}", "",
                  f"Árbol generado en MT-v3 el {self.arbol.get('generado')}. Ver `data/{self.cid}/FUENTE.md`.", "",
                  f"**{len(self.nodos)} nodos** y **{len(self.aristas)} aristas**.", "", "| Tipo de nodo | Cantidad |",
                  "|---|---:|"] + [f"| {k} | {v} |" for k, v in kn.most_common()] + [
                  "", "| Tipo de arista | Cantidad |", "|---|---:|"] + [f"| {k} | {v} |" for k, v in ka.most_common()] + [
                  "", "Operaciones de las aristas `modifica`: " + ", ".join(f"{k} {v}" for k, v in ops.most_common()) + ".",
                  "", f"Similitud: umbral de coseno {getattr(self, 'umbral_similitud', 0):.3f} (árbol de expansión "
                  "máxima + los pares más parecidos, unas 2 aristas por artículo)."]
        return "\n".join(lineas) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("concesion", nargs="?", default="RITP")
    ap.add_argument("--iter", type=int, default=600)
    ap.add_argument("--fragmento", type=Path, help="escribe además el visor sin <html>/<head> (para publicarlo como artefacto)")
    args = ap.parse_args()
    g = Grafo(args.concesion)
    g.armar()
    g.similitud()
    g.datar()
    g.disponer(args.iter)
    salida = RAIZ / "salida"
    salida.mkdir(exist_ok=True)
    datos = json.dumps(g.datos_visor(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    plantilla = (Path(__file__).parent / "plantilla.html").read_text(encoding="utf-8")
    cuerpo = plantilla.replace("/*__DATOS__*/null", datos)
    if args.fragmento:
        args.fragmento.write_text(cuerpo, encoding="utf-8")
    (salida / f"grafo_{args.concesion}.html").write_text(
        "<!doctype html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n</head>\n<body>\n"
        + cuerpo + "\n</body>\n</html>\n", encoding="utf-8")
    g.graphml(salida / f"grafo_{args.concesion}.graphml")
    (salida / f"resumen_{args.concesion}.md").write_text(g.resumen(), encoding="utf-8")
    print(g.resumen())


if __name__ == "__main__":
    main()
