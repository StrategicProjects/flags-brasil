#!/usr/bin/env python3
"""Baixa as bandeiras de estados e municípios do Brasil do Wikimedia Commons.

Fontes:
  - IBGE (API de localidades): lista oficial de UFs e municípios.
  - Wikidata: propriedade P41 (imagem da bandeira) dos itens com código IBGE
    (P1585, municípios) ou ISO 3166-2 (P300, estados).
  - Wikimedia Commons: arquivo, autor e licença de cada bandeira.

Etapas (todas retomáveis; rode de novo para continuar de onde parou):
  1. dados/fonte/ibge.json e dados/fonte/wikidata.json
  2. dados/fonte/commons.json   (metadados e licença de cada arquivo)
  3. originais/                 (SVG original ou miniatura PNG de 500 px)

Uso: python3 tools/baixar.py [--so-metadados] [--limite N]
Só biblioteca padrão.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "dados" / "fonte"
ORIG = RAIZ / "originais"
UA = "FlagCatalogBot/0.1 (open-source flag catalog; python-urllib)"
PAUSA_ORIGINAL = 3.0  # s entre originais: em rajada o servidor responde 429 e depois bloqueia 10 min
LARGURA_RASTER = 500  # degrau padrão de miniatura do Commons


def get(url: str, dados: dict | None = None, tentativas: int = 6) -> bytes:
    if dados:
        url = url + "?" + urllib.parse.urlencode(dados)
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                corpo = r.read()
                if corpo[:2] == b"\x1f\x8b":  # o IBGE responde gzip mesmo sem pedir
                    import gzip
                    corpo = gzip.decompress(corpo)
                return corpo
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            espera = int(e.headers.get("Retry-After") or 0) or 5 * (i + 1)
            print(f"  HTTP {e.code}; esperando {espera}s", file=sys.stderr)
            time.sleep(min(espera, 120))
        except Exception as e:  # rede
            print(f"  {type(e).__name__}: {e}; nova tentativa", file=sys.stderr)
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"falhou: {url}")


def sparql(q: str) -> list[dict]:
    b = get("https://query.wikidata.org/sparql", {"query": q, "format": "json"})
    return [
        {k: v["value"] for k, v in linha.items()}
        for linha in json.loads(b)["results"]["bindings"]
    ]


def nome_arquivo(url: str) -> str:
    return urllib.parse.unquote(url.rsplit("/Special:FilePath/", 1)[1]).replace("_", " ")


def etapa_listas() -> None:
    FONTE.mkdir(parents=True, exist_ok=True)
    ibge = FONTE / "ibge.json"
    if not ibge.exists():
        mun = json.loads(get(
            "https://servicodados.ibge.gov.br/api/v1/localidades/municipios",
            {"view": "nivelado"}))
        ufs = json.loads(get("https://servicodados.ibge.gov.br/api/v1/localidades/estados"))
        ibge.write_text(json.dumps({
            "ufs": sorted(({"codigo": u["id"], "sigla": u["sigla"], "nome": u["nome"],
                            "regiao": u["regiao"]["nome"]} for u in ufs),
                          key=lambda u: u["sigla"]),
            "municipios": sorted(({"codigo": m["municipio-id"], "nome": m["municipio-nome"],
                                   "uf": m["UF-sigla"]} for m in mun),
                                 key=lambda m: m["codigo"]),
        }, ensure_ascii=False, indent=1))
    wd = FONTE / "wikidata.json"
    if not wd.exists():
        mun = sparql("SELECT ?item ?cod ?flag WHERE { ?item wdt:P1585 ?cod ; wdt:P41 ?flag }")
        ufs = sparql('SELECT ?item ?cod ?flag WHERE { ?item wdt:P300 ?cod ; wdt:P41 ?flag . '
                     'FILTER(STRSTARTS(?cod, "BR-")) }')
        br = sparql("SELECT ?flag WHERE { wd:Q155 wdt:P41 ?flag }")
        saida: dict[str, dict] = {}

        def entra(chave: str, item: str, flag: str) -> None:
            e = saida.setdefault(chave, {"wikidata": item.rsplit("/", 1)[-1], "arquivos": []})
            f = nome_arquivo(flag)
            if f not in e["arquivos"]:
                e["arquivos"].append(f)

        for x in br:
            entra("br", "Q155", x["flag"])
        for x in ufs:
            entra(x["cod"][3:].lower(), x["item"], x["flag"])
        for x in mun:
            entra(x["cod"], x["item"], x["flag"])
        for e in saida.values():  # SVG primeiro; depois ordem alfabética (determinístico)
            e["arquivos"].sort(key=lambda f: (not f.lower().endswith(".svg"), f))
        wd.write_text(json.dumps(dict(sorted(saida.items())), ensure_ascii=False, indent=1))


def fontes() -> dict:
    """Wikidata + dados/fonte/complementos.json (curadoria manual: bandeiras que
    estão no Commons mas não no Wikidata, ou SVG melhor que o raster apontado).
    O complemento tem precedência."""
    wd = json.loads((FONTE / "wikidata.json").read_text())
    comp = FONTE / "complementos.json"
    if comp.exists():
        for k, c in json.loads(comp.read_text()).items():
            e = wd.setdefault(k, {"arquivos": []})
            e["arquivos"] = [c["arquivo"]] + [f for f in e["arquivos"] if f != c["arquivo"]]
            e["origem"] = c.get("origem", "categoria do Wikimedia Commons")
    # As chaves viram nome de arquivo: só passam "br", as siglas das UFs e os
    # códigos de município da lista do IBGE (o Wikidata é editável por qualquer um).
    ibge = json.loads((FONTE / "ibge.json").read_text())
    validas = ({"br"} | {u["sigla"].lower() for u in ibge["ufs"]}
               | {str(m["codigo"]) for m in ibge["municipios"]})
    return {k: e for k, e in wd.items()
            if k in validas and re.fullmatch(r"[a-z]{2}|\d{7}", k) and e["arquivos"]}


def origens() -> dict:
    """De qual arquivo do Commons veio cada original em disco. O que foi baixado
    antes de existir originais/_origem.json veio do primeiro arquivo do Wikidata."""
    wd = json.loads((FONTE / "wikidata.json").read_text())
    o = {k: e["arquivos"][0] for k, e in wd.items()}
    arq = ORIG / "_origem.json"
    if arq.exists():
        o.update(json.loads(arq.read_text()))
    return o


def limpa(s: str | None) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def etapa_commons() -> dict:
    wd = fontes()
    arq = FONTE / "commons.json"
    meta = json.loads(arq.read_text()) if arq.exists() else {}
    falta = sorted({e["arquivos"][0] for e in wd.values()} - set(meta))
    for i in range(0, len(falta), 50):
        lote = falta[i:i + 50]
        r = json.loads(get("https://commons.wikimedia.org/w/api.php", {
            "action": "query", "format": "json", "formatversion": "2",
            "prop": "imageinfo", "titles": "|".join("File:" + f for f in lote),
            "iiprop": "url|size|mime|extmetadata", "iiurlwidth": str(LARGURA_RASTER),
            "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit|"
                                   "AttributionRequired|UsageTerms",
        }))["query"]
        de_para = {n["to"]: n["from"] for n in r.get("normalized", [])}
        for p in r["pages"]:
            pedido = de_para.get(p["title"], p["title"])[5:]
            if "imageinfo" not in p:
                meta[pedido] = {"ausente": True}
                continue
            ii = p["imageinfo"][0]
            em = {k: v.get("value") for k, v in ii.get("extmetadata", {}).items()}
            meta[pedido] = {
                "url": ii["url"],
                "miniatura": ii.get("thumburl"),
                "pagina": ii["descriptionurl"],
                "mime": ii["mime"],
                "largura": ii.get("width"),
                "altura": ii.get("height"),
                "bytes": ii.get("size"),
                "licenca": limpa(em.get("LicenseShortName")),
                "licenca_url": em.get("LicenseUrl") or "",
                "autor": limpa(em.get("Artist")),
                "credito": limpa(em.get("Credit")),
                "atribuicao_obrigatoria": em.get("AttributionRequired") == "true",
            }
        arq.write_text(json.dumps(dict(sorted(meta.items())), ensure_ascii=False, indent=1))
        print(f"metadados {min(i + 50, len(falta))}/{len(falta)}", flush=True)
        time.sleep(0.5)
    return meta


class Limitado(Exception):
    """O servidor pediu para esperar (HTTP 429)."""

    def __init__(self, espera: int):
        self.espera = espera


def baixa(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise Limitado(int(e.headers.get("Retry-After") or 60))
        raise


DEGRAUS = (500, 330, 250, 120, 60)  # larguras de miniatura que o Commons aceita


def miniatura(m: dict) -> tuple[str, str] | None:
    """URL da maior miniatura padrão mais estreita que o original."""
    base = m["url"].split("?")[0]
    nome = base.rsplit("/", 1)[-1]
    svg = m["mime"] == "image/svg+xml"
    for w in DEGRAUS:
        if svg or (m.get("largura") or 0) > w:
            caminho = base.split("/wikipedia/commons/", 1)[1]
            url = (f"https://thumb.wikimedia.org/wikipedia/commons/thumb/{caminho}/"
                   f"{w}px-{nome}" + (".png" if svg else ""))
            return url, "png" if svg else nome.rsplit(".", 1)[-1].lower()
    return None


def baixa_mini(url: str) -> bytes:
    for _ in range(5):
        try:
            return baixa(url)
        except Limitado as e:
            print(f"  miniaturas limitadas; esperando {e.espera}s", file=sys.stderr, flush=True)
            time.sleep(min(e.espera, 660) + 1)
    raise RuntimeError("miniatura limitada repetidamente")


def etapa_download(limite: int | None) -> None:
    """O ideal é o original para SVG e para raster de até 500 px, e a miniatura
    de 500 px para raster maior. O upload.wikimedia.org limita originais por IP
    (429 com Retry-After de 10 min, comum atrás de VPN); nesse caso entra uma
    miniatura como provisória (anotada em originais/_provisorios.json) e o
    original fica para uma próxima execução. O limite é respeitado: depois de
    um 429 os originais só voltam a ser pedidos passado o prazo."""
    wd = fontes()
    meta = json.loads((FONTE / "commons.json").read_text())
    ORIG.mkdir(exist_ok=True)
    arq_prov = ORIG / "_provisorios.json"
    prov = set(json.loads(arq_prov.read_text())) if arq_prov.exists() else set()
    stems = {p.stem for p in ORIG.iterdir() if not p.name.startswith("_")}
    origem = origens()
    arq_origem = ORIG / "_origem.json"
    fila = []
    for k, e in wd.items():
        m = meta.get(e["arquivos"][0]) or {}
        if m.get("ausente") or not m.get("url") or m["mime"] == "application/pdf":
            continue
        svg = m["mime"] == "image/svg+xml"
        trocar = k in stems and origem.get(k) != e["arquivos"][0]  # a fonte mudou
        if k in stems and k not in prov and not trocar:
            continue
        if trocar:
            stems.discard(k)
            prov.discard(k)
        quer_original = svg or (m.get("largura") or 0) <= LARGURA_RASTER
        fila.append((k.isdigit(), k in prov, quer_original, k, m))
    fila.sort(key=lambda t: t[:4])  # UFs; depois o que falta; por último os provisórios
    if limite:
        fila = fila[:limite]
    liberado_em = 0.0
    pausa = PAUSA_ORIGINAL

    def grava(chave: str, ext: str, dados: bytes) -> None:
        if not re.fullmatch(r"[a-z]{2}|\d{7}", chave) or not re.fullmatch(r"[a-z0-9]{2,5}", ext):
            raise RuntimeError(f"nome de arquivo recusado: {chave}.{ext}")
        for p in ORIG.glob(f"{chave}.*"):
            p.unlink()
        (ORIG / f"{chave}.{ext}").write_bytes(dados)
        origem[chave] = wd[chave]["arquivos"][0]

    for n, (_, _, quer_original, chave, m) in enumerate(fila, 1):
        mini = miniatura(m)
        ext_orig = m["url"].split("?")[0].rsplit(".", 1)[-1].lower()
        try:
            if not quer_original:
                grava(chave, mini[1], baixa_mini(mini[0]))
            else:
                ok = False
                if chave in stems and time.time() < liberado_em:
                    # já há um provisório: só resta esperar o servidor liberar
                    time.sleep(liberado_em - time.time() + 1)
                if time.time() >= liberado_em:
                    try:
                        dados = baixa(m["url"])
                        if ext_orig == "svg" and b"<svg" not in dados[:20000]:
                            raise RuntimeError("resposta não é SVG")
                        grava(chave, ext_orig, dados)
                        prov.discard(chave)
                        ok = True
                        time.sleep(pausa)
                    except Limitado as e:
                        liberado_em = time.time() + max(e.espera, 90)
                        pausa = min(pausa * 1.5, 30)  # foi rápido demais: desacelera
                        print(f"  originais limitados por {e.espera}s; pausa {pausa:.1f}s",
                              file=sys.stderr, flush=True)
                if not ok and chave not in stems and mini:  # só se não houver nada
                    grava(chave, mini[1], baixa_mini(mini[0]))
                    prov.add(chave)
        except Exception as e:
            print(f"ERRO {chave}: {e}", file=sys.stderr, flush=True)
        if n % 100 == 0 or n == len(fila):
            arq_prov.write_text(json.dumps(sorted(prov)))
            arq_origem.write_text(json.dumps(origem, ensure_ascii=False, indent=0))
            print(f"download {n}/{len(fila)} (provisórios: {len(prov)})", flush=True)
        time.sleep(0.3)
    arq_prov.write_text(json.dumps(sorted(prov)))
    arq_origem.write_text(json.dumps(origem, ensure_ascii=False, indent=0))
    print(f"provisórios (miniatura no lugar do original): {len(prov)}; "
          "rode de novo para tentar os originais")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-metadados", action="store_true")
    ap.add_argument("--limite", type=int)
    a = ap.parse_args()
    etapa_listas()
    etapa_commons()
    if not a.so_metadados:
        etapa_download(a.limite)
