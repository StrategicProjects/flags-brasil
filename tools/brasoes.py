#!/usr/bin/env python3
"""Baixa os brasões em SVG do Brasil, das UFs e dos municípios.

Fonte: propriedade P94 (imagem do brasão) do Wikidata, nos mesmos itens das
bandeiras; arquivo, autor e licença vêm do Wikimedia Commons. Só entra brasão
que existe em SVG no Commons (os rasters ficaram de fora nesta etapa).

Etapas (retomáveis):
  1. dados/fonte/brasoes.json   arquivo do Commons, autor e licença por chave
  2. originais/_brasoes/        SVG originais

Depois rode tools/gerar.py (publica em brasoes/), tools/otimizar.py e
tools/gerar.py de novo (troca por PNG os SVG que ficaram acima do teto).
Uso: python3 tools/brasoes.py [--so-metadados] [--limite N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baixar import (FONTE, ORIG, PAUSA_ORIGINAL, Limitado, baixa, etapa_listas,  # noqa: E402
                    fontes, get, limpa, nome_arquivo, sparql, svg_utf8)

ARQ = FONTE / "brasoes.json"
DEST = ORIG / "_brasoes"  # o "_" tira a pasta da lista de originais das bandeiras


def etapa_fonte() -> dict:
    if ARQ.exists():
        return json.loads(ARQ.read_text())
    ibge = json.loads((FONTE / "ibge.json").read_text())
    validas = ({"br"} | {u["sigla"].lower() for u in ibge["ufs"]}
               | {str(m["codigo"]) for m in ibge["municipios"]})
    bandeiras = fontes()
    achados: dict[str, dict] = {}

    def entra(chave: str, item: str, url: str) -> None:
        f = nome_arquivo(url)
        # só SVG; chave da lista oficial; e nada de bandeira cadastrada como brasão
        if (not f.lower().endswith(".svg") or chave not in validas
                or f in bandeiras.get(chave, {}).get("arquivos", [])):
            return
        achados.setdefault(chave, {"wikidata": item.rsplit("/", 1)[-1], "arquivos": []})
        if f not in achados[chave]["arquivos"]:
            achados[chave]["arquivos"].append(f)

    for x in sparql("SELECT ?b WHERE { wd:Q155 wdt:P94 ?b }"):
        entra("br", "Q155", x["b"])
    for x in sparql('SELECT ?item ?cod ?b WHERE { ?item wdt:P300 ?cod ; wdt:P94 ?b . '
                    'FILTER(STRSTARTS(?cod, "BR-")) }'):
        entra(x["cod"][3:].lower(), x["item"], x["b"])
    for x in sparql("SELECT ?item ?cod ?b WHERE { ?item wdt:P1585 ?cod ; wdt:P94 ?b }"):
        entra(x["cod"], x["item"], x["b"])
    for e in achados.values():
        e["arquivo"] = sorted(e.pop("arquivos"))[0]  # determinístico

    por_arquivo: dict[str, dict] = {}
    nomes = sorted({e["arquivo"] for e in achados.values()})
    for i in range(0, len(nomes), 50):
        r = json.loads(get("https://commons.wikimedia.org/w/api.php", {
            "action": "query", "format": "json", "formatversion": "2",
            "prop": "imageinfo", "titles": "|".join("File:" + f for f in nomes[i:i + 50]),
            "iiprop": "url|size|mime|extmetadata",
            "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist",
        }))["query"]
        de_para = {n["to"]: n["from"] for n in r.get("normalized", [])}
        for p in r["pages"]:
            if "imageinfo" not in p:
                continue
            ii = p["imageinfo"][0]
            if ii["mime"] != "image/svg+xml":
                continue
            em = {k: v.get("value") for k, v in ii.get("extmetadata", {}).items()}
            por_arquivo[de_para.get(p["title"], p["title"])[5:]] = {
                "url": ii["url"], "pagina": ii["descriptionurl"],
                "largura": ii.get("width"), "altura": ii.get("height"),
                "licenca": limpa(em.get("LicenseShortName")),
                "licenca_url": em.get("LicenseUrl") or "",
                "autor": limpa(em.get("Artist")),
            }
        print(f"metadados {min(i + 50, len(nomes))}/{len(nomes)}", flush=True)
        time.sleep(0.5)
    saida = {k: {**e, **por_arquivo[e["arquivo"]]}
             for k, e in sorted(achados.items()) if e["arquivo"] in por_arquivo}
    ARQ.write_text(json.dumps(saida, ensure_ascii=False, indent=1))
    return saida


def etapa_download(fonte: dict, limite: int | None) -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    arq_origem = DEST / "_origem.json"
    origem = json.loads(arq_origem.read_text()) if arq_origem.exists() else {}
    # UFs e Brasil primeiro
    fila = sorted((k for k, e in fonte.items()
                   if not (DEST / f"{k}.svg").exists() or origem.get(k) != e["arquivo"]),
                  key=lambda k: (k.isdigit(), k))[:limite]
    pausa = PAUSA_ORIGINAL
    for n, k in enumerate(fila, 1):
        if not re.fullmatch(r"[a-z]{2}|\d{7}", k):
            raise RuntimeError(f"nome de arquivo recusado: {k}")
        for _ in range(4):
            try:
                dados = svg_utf8(baixa(fonte[k]["url"]))
                if b"<svg" not in dados[:20000]:
                    raise RuntimeError("resposta não é SVG")
                (DEST / f"{k}.svg").write_bytes(dados)
                origem[k] = fonte[k]["arquivo"]
                break
            except Limitado as e:  # respeita o prazo do servidor e desacelera
                pausa = min(pausa * 1.5, 30)
                print(f"  limitado por {e.espera}s; pausa {pausa:.1f}s", file=sys.stderr, flush=True)
                time.sleep(max(e.espera, 90) + 1)
            except Exception as e:
                print(f"ERRO {k}: {e}", file=sys.stderr, flush=True)
                break
        if n % 20 == 0 or n == len(fila):
            arq_origem.write_text(json.dumps(origem, ensure_ascii=False, indent=0))
            print(f"download {n}/{len(fila)}", flush=True)
        time.sleep(pausa)
    for p in DEST.glob("*.svg"):  # o brasão saiu do Wikidata
        if p.stem not in fonte:
            p.unlink()
    print(f"brasões em disco: {sum(1 for _ in DEST.glob('*.svg'))} de {len(fonte)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-metadados", action="store_true")
    ap.add_argument("--limite", type=int)
    a = ap.parse_args()
    etapa_listas()
    f = etapa_fonte()
    print(f"brasões em SVG na fonte: {len(f)}")
    if not a.so_metadados:
        etapa_download(f, a.limite)
