#!/usr/bin/env python3
"""Passa o svgo em flags/**/*.svg, mas só fica com o resultado se o desenho
não mudar.

O svgo às vezes quebra um arquivo (a bandeira de Alagoas perdia o brasão), então
cada SVG otimizado é renderizado e comparado com o original de originais/; se
mais de 0,1% dos pixels diferirem, ou se não renderizar, fica o original.

Precisa de svgo (pnpm install), rsvg-convert e magick.
Uso: python3 tools/otimizar.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIG = RAIZ / "originais"
SVGO = RAIZ / "node_modules" / ".bin" / "svgo"
ESTADO = ORIG / "_otimizados.json"
LIMITE = 0.001  # fração de pixels que pode diferir


def render(svg: Path, png: Path) -> bool:
    r = subprocess.run(["rsvg-convert", "-w", "600", "-b", "#808080", str(svg), "-o", str(png)],
                       capture_output=True)
    return r.returncode == 0 and png.exists()


def processa(dst: Path) -> tuple[str, str, int]:
    src = ORIG / dst.name
    antes = src.stat().st_size
    with tempfile.TemporaryDirectory() as t:
        tmp, a, b = Path(t) / "o.svg", Path(t) / "a.png", Path(t) / "b.png"
        r = subprocess.run([str(SVGO), "--config", str(RAIZ / "svgo.config.mjs"), "-q",
                            "-i", str(src), "-o", str(tmp)], capture_output=True)
        motivo = ""
        if r.returncode != 0 or not tmp.exists():
            motivo = "svgo falhou"
        elif not render(src, a):
            motivo = "original não renderiza no rsvg (mantido sem conferir)"
        elif not render(tmp, b):
            motivo = "otimizado não renderiza"
        else:
            c = subprocess.run(["magick", "compare", "-metric", "AE", "-fuzz", "3%",
                                str(a), str(b), "null:"], capture_output=True, text=True)
            try:
                dif = float(c.stderr.split()[0])
                w, h = map(int, subprocess.run(
                    ["magick", "identify", "-format", "%w %h", str(a)],
                    capture_output=True, text=True).stdout.split())
                if dif / (w * h) > LIMITE:
                    motivo = f"desenho mudou ({100 * dif / (w * h):.2f}% dos pixels)"
            except (ValueError, IndexError):
                motivo = "comparação falhou (tamanhos diferentes?)"
        if motivo:
            shutil.copyfile(src, dst)
            return dst.name, motivo, 0
        shutil.copyfile(tmp, dst)
        return dst.name, "", antes - dst.stat().st_size


def main() -> None:
    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    fila = []
    for dst in sorted((RAIZ / "flags").rglob("*.svg")):
        src = ORIG / dst.name
        if src.exists() and estado.get(dst.name, {}).get("mtime") != src.stat().st_mtime:
            fila.append(dst)
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(processa, fila))
    ganho = 0
    for nome, motivo, g in res:
        ganho += g
        estado[nome] = {"mtime": (ORIG / nome).stat().st_mtime, "mantido_original": motivo}
        if motivo:
            print(f"{nome}: {motivo}", file=sys.stderr)
    ESTADO.write_text(json.dumps(estado, indent=0, ensure_ascii=False))
    mantidos = sum(1 for _, m, _ in res if m)
    print(f"{len(res)} SVG processados, {mantidos} mantidos como o original, "
          f"{ganho / 1e6:.1f} MB economizados")


if __name__ == "__main__":
    main()
