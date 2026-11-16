#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["vtracer"]
# ///
"""Vetoriza automaticamente (vtracer) as bandeiras que só existem em raster.

O resultado vai para flags/mun/vetorizado/<codigo>.svg, AO LADO do PNG, que
continua sendo o arquivo padrão. É traçado automático, não redesenho: as bordas
podem ondular e texto pequeno perde nitidez. Por isso só é publicado o que
passa em três filtros:

  - fonte com pelo menos LARGURA_MIN px de largura;
  - render do SVG parecido com o original (no máximo DIF_MAX dos pixels
    diferindo além de 8% de cor, e nenhum bloco de uma grade 16x12 com
    mais de LOCAL_MAX);
  - arquivo final de até TAMANHO_MAX bytes, depois do svgo.

O que reprova fica só em PNG; o motivo vai para originais/_vetorizacao.json.

Uso: uv run tools/vetorizar.py --uf PE [--uf PB ...] | --todas [--refazer]
     uv run tools/vetorizar.py --uf PE --folha <pasta>   (folhas de conferência)
Precisa de magick, rsvg-convert e svgo (pnpm install). Depois rode gerar.py.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import vtracer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgseguro import problema  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ORIG = RAIZ / "originais"
SAIDA = RAIZ / "flags" / "mun" / "vetorizado"
SVGO = RAIZ / "node_modules" / ".bin" / "svgo"
ESTADO = ORIG / "_vetorizacao.json"
FONTE_TTC = "/System/Library/Fonts/Helvetica.ttc"

LARGURA_MIN = 400
DIF_MAX = 0.02
LOCAL_MAX = 0.30
TAMANHO_MAX = 300_000
PARAMS = dict(colormode="color", hierarchical="stacked", mode="spline",
              color_precision=6, filter_speckle=8, layer_difference=16,
              corner_threshold=60, length_threshold=4.0, splice_threshold=45,
              path_precision=1)


def roda(*args: str, ok: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=ok)


def vetoriza(item: tuple[str, Path]) -> tuple[str, dict]:
    k, raster = item
    src = f"{raster}[0]"
    dst = SAIDA / f"{k}.svg"
    try:
        w = int(roda("magick", "identify", "-format", "%w", src).stdout)
        if w < LARGURA_MIN:
            dst.unlink(missing_ok=True)
            return k, {"ok": False, "motivo": f"fonte com {w} px"}
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            pre, bruto, svg = t / "pre.png", t / "bruto.svg", t / "o.svg"
            a, b = t / "a.png", t / "b.png"
            # amplia e suaviza: o traçado segue melhor as bordas e ignora ruído de JPEG
            escala = max(1, round(1500 / w))
            roda("magick", src, "-background", "white", "-alpha", "remove", "-filter",
                 "Lanczos", "-resize", f"{escala * 100}%", "-median", "2", str(pre))
            vtracer.convert_image_to_svg_py(str(pre), str(bruto), **PARAMS)
            r = roda(str(SVGO), "--config", str(RAIZ / "svgo.config.mjs"), "-q",
                     "-i", str(bruto), "-o", str(svg), ok=False)
            if r.returncode != 0 or not svg.exists():
                svg = bruto
            dados = svg.read_bytes()
            if problema(dados):
                dst.unlink(missing_ok=True)
                return k, {"ok": False, "motivo": "reprovado na conferência de segurança"}
            roda("magick", str(pre), "-resize", "400x", str(a))
            dim = roda("magick", "identify", "-format", "%wx%h!", str(a)).stdout
            roda("rsvg-convert", "-w", "400", str(svg), "-o", str(b))
            roda("magick", str(b), "-background", "white", "-alpha", "remove",
                 "-resize", dim, str(b))
            c = roda("magick", "compare", "-metric", "AE", "-fuzz", "8%",
                     str(a), str(b), "null:", ok=False)
            wa, ha = map(int, dim.rstrip("!").split("x"))
            dif = float(c.stderr.split()[0]) / (wa * ha)
            # pior bloco de uma grade 16x12: pega perda de cor numa área pequena
            # (uma folhagem que virou azul), que a média da bandeira inteira esconde
            # (as duas imagens são desfocadas antes: serrilhado e traço fino não contam)
            loc = float(roda("magick", "(", str(a), "-blur", "0x4", ")",
                             "(", str(b), "-blur", "0x4", ")",
                             "-compose", "difference", "-composite",
                             "-separate", "-evaluate-sequence", "Max",  # pior canal
                             "-threshold", "10%", "-scale", "16x12!",
                             "-format", "%[fx:maxima]", "info:").stdout)
            info = {"dif": round(dif, 4), "local": round(loc, 3), "bytes": len(dados),
                    "fonte_px": w}
            if dif > DIF_MAX or loc > LOCAL_MAX:
                dst.unlink(missing_ok=True)
                return k, {**info, "ok": False, "motivo": "desenho diferente do original"}
            if len(dados) > TAMANHO_MAX:
                dst.unlink(missing_ok=True)
                return k, {**info, "ok": False, "motivo": "arquivo grande demais"}
            dst.write_bytes(dados)
            return k, {**info, "ok": True}
    except Exception as e:
        dst.unlink(missing_ok=True)
        return k, {"ok": False, "motivo": f"erro: {type(e).__name__}: {str(e)[:120]}"}


def folhas(pasta: Path, itens: list[tuple[str, Path]], estado: dict, nomes: dict) -> None:
    """Original | vetorizado, com nome, diferença e tamanho, para conferência visual."""
    pasta.mkdir(parents=True, exist_ok=True)
    celulas = []
    for k, raster in itens:
        e = estado.get(k, {})
        svg = SAIDA / f"{k}.svg"
        if not (e.get("ok") and svg.exists()):
            continue
        png, cel = pasta / f"{k}_v.png", pasta / f"{k}.png"
        roda("rsvg-convert", "-w", "640", str(svg), "-o", str(png))
        roda("magick", "montage", f"{raster}[0]", str(png), "-font", FONTE_TTC, "-tile", "2x1",
             "-geometry", "300x210+4+4", "-background", "#cfd4cc", str(cel))
        rot = f"{nomes[k]}  dif {100 * e['dif']:.1f}%  {e['bytes'] // 1024} KB"
        roda("magick", str(cel), "-font", FONTE_TTC, "-pointsize", "15", "-background",
             "white", "-gravity", "south", "-splice", "0x22", "-annotate", "+0+3", rot, str(cel))
        png.unlink()
        celulas.append(str(cel))
    for i in range(0, len(celulas), 15):
        roda("magick", "montage", *celulas[i:i + 15], "-font", FONTE_TTC, "-tile", "3x",
             "-geometry", "+6+6", str(pasta / f"folha{i // 15:02d}.png"))
    print(f"{len(celulas)} bandeiras em {pasta}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", action="append", default=[])
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--refazer", action="store_true")
    ap.add_argument("--folha", type=Path)
    a = ap.parse_args()
    if not (a.uf or a.todas):
        ap.error("informe --uf ou --todas")
    ibge = json.loads((RAIZ / "dados" / "fonte" / "ibge.json").read_text())
    ufs = {u.upper() for u in a.uf}
    nomes = {str(m["codigo"]): m["nome"] for m in ibge["municipios"]
             if a.todas or m["uf"] in ufs}
    SAIDA.mkdir(parents=True, exist_ok=True)
    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    itens = []
    for k in sorted(nomes):
        arqs = [p for p in ORIG.glob(f"{k}.*")]
        if not arqs or any(p.suffix == ".svg" for p in arqs):
            (SAIDA / f"{k}.svg").unlink(missing_ok=True)  # sem fonte, ou já há vetor de verdade
            continue
        itens.append((k, arqs[0]))
    fila = [(k, p) for k, p in itens
            if a.refazer or estado.get(k, {}).get("mtime") != p.stat().st_mtime]
    with ThreadPoolExecutor(6) as ex:
        for k, info in ex.map(vetoriza, fila):
            estado[k] = {**info, "mtime": dict(itens)[k].stat().st_mtime}
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=0))
    feitos = [estado[k] for k, _ in itens if k in estado]
    ok = [e for e in feitos if e["ok"]]
    motivos: dict[str, int] = {}
    for e in feitos:
        if not e["ok"]:
            m = e["motivo"].split(" com ")[0] if e["motivo"].startswith("fonte") else e["motivo"]
            motivos[m] = motivos.get(m, 0) + 1
    print(f"{len(itens)} rasters, {len(fila)} processados agora, {len(ok)} vetorizados "
          f"({sum(e['bytes'] for e in ok) / 1e6:.1f} MB); reprovados: {motivos}")
    if a.folha:
        folhas(a.folha, itens, estado, nomes)


if __name__ == "__main__":
    main()
