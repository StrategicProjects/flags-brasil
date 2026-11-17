#!/usr/bin/env python3
"""Monta o pacote a partir de originais/ e dados/fonte/ (ver tools/baixar.py).

Gera:
  flags/br.svg, flags/uf/<sigla>.svg, flags/mun/<codigo-ibge>.{svg,png}
  brasoes/br.svg, brasoes/uf/<sigla>.svg, brasoes/mun/<codigo-ibge>.{svg,png}
                         brasões (ver tools/brasoes.py); só os que existem em SVG
                         no Commons, com os pesados em PNG
  dados/bandeiras.json   manifesto com nome, UF, arquivo, proporção e crédito
  css/flags-brasil.css   Brasil + 27 UFs
  css/municipios.css     todos os municípios
  css/uf/<sigla>.css     municípios de uma UF
  css/brasoes.css, css/brasoes-municipios.css
  CREDITOS.md            autor e licença de cada bandeira
  dados/site.json, dados/detalhe/<uf>.json, mini/<codigo>.webp,
  mini/brasao/<codigo>.webp
                         só para o site: índice enxuto, detalhes sob demanda
                         e miniaturas de 200 px

Precisa do ImageMagick (`magick`) para os rasters. Depois rode
`pnpm run otimizar` (svgo com conferência de render) para enxugar os SVG.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baixar import fontes, origens  # noqa: E402
from svgseguro import problema  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "dados" / "fonte"
ORIG = RAIZ / "originais"
FLAGS = RAIZ / "flags"
BRASOES = RAIZ / "brasoes"
ORIG_BRASOES = ORIG / "_brasoes"
LARGURA = 500
TETO_BRASAO = 300_000  # bytes, depois do svgo; acima disso o município recebe PNG

BASE_CSS_BRASOES = """\
/* flags-brasil — brasões do Brasil e dos estados (os dos municípios estão em
   brasoes-municipios.css). Uso: <span class="bbr bbr-pe"></span>
   Gerado por tools/gerar.py; não edite à mão. */
.bbr {
  display: inline-block;
  width: 1em;
  height: 1em;
  line-height: 1em;
  vertical-align: -0.125em;
  background: center / contain no-repeat;
}
.bbr::before { content: "\\00a0"; }
"""

BASE_CSS = """\
/* flags-brasil — bandeiras do Brasil, dos estados e dos municípios.
   Uso: <span class="fbr fbr-pe"></span> ou <span class="fbr fbr-2611606"></span>
   Gerado por tools/gerar.py; não edite à mão. */
.fbr {
  display: inline-block;
  width: 1.4286em; /* 10:7, a proporção da bandeira nacional */
  height: 1em;
  line-height: 1em;
  vertical-align: -0.125em;
  background: center / contain no-repeat;
}
.fbr::before { content: "\\00a0"; }
.fbr.fbr-1x1 { width: 1em; background-size: cover; }
.fbr.fbr-4x3 { width: 1.3333em; background-size: cover; }
"""


def url_http(u: str) -> str:
    return u if u.startswith(("https://", "http://")) else ""


def limpa_autor(a: str) -> str:
    """O campo Artist do Commons às vezes traz o texto do aviso de licença."""
    if not a:
        return "não informado"
    if a.startswith("Unknown author"):
        return "autor desconhecido"
    if re.match(r"(Public domain|This (work|file|image)|Esta (obra|imagem)|Este arquivo)", a):
        return "ver página de origem"
    return a if len(a) <= 160 else a[:157] + "…"


def destino(chave: str, ext: str, base: Path = FLAGS) -> Path:
    if chave == "br":
        return base / f"br.{ext}"
    if chave.isdigit():
        return base / "mun" / f"{chave}.{ext}"
    return base / "uf" / f"{chave}.{ext}"


def converte(par: tuple[Path, Path]) -> str | None:
    src, dst = par
    if src.suffix == ".svg" and dst.suffix == ".png":
        # SVG recusado na conferência de segurança: entra rasterizado, que é inerte.
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            return None
        r = subprocess.run(["rsvg-convert", "-w", str(LARGURA), str(src)], capture_output=True)
        if r.returncode != 0:
            return f"{src.name}: SVG recusado e não rasterizável; não publicado"
        r = subprocess.run(["magick", "png:-", "-strip", "-colors", "256", "-define",
                            "png:compression-level=9", f"PNG8:{dst}"],
                           input=r.stdout, capture_output=True)
        return None if r.returncode == 0 else f"{src.name}: falha ao rasterizar"
    if src.suffix == ".svg":
        # Fechado por padrão: confere sempre o original e o que já está publicado.
        motivo = problema(src.read_bytes()) or (dst.exists() and problema(dst.read_bytes()))
        if motivo:
            dst.unlink(missing_ok=True)
            return f"{src.name}: SVG recusado ({motivo}); não publicado"
        if not (dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime):
            shutil.copyfile(src, dst)
        return None
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return None
    r = subprocess.run(
        ["magick", f"{src}[0]", "-auto-orient", "-strip", "-resize", f"{LARGURA}x>",
         "-colors", "256", "-define", "png:compression-level=9", f"PNG8:{dst}"],
        capture_output=True, text=True)
    return None if r.returncode == 0 else f"{src.name}: {r.stderr.strip()[:200]}"


def main() -> None:
    ibge = json.loads((FONTE / "ibge.json").read_text())
    wd = fontes()
    origem = origens()
    arq_ext = FONTE / "externos.json"
    externos = json.loads(arq_ext.read_text()) if arq_ext.exists() else {}
    meta = json.loads((FONTE / "commons.json").read_text())
    for d in (FLAGS / "uf", FLAGS / "mun", RAIZ / "css" / "uf"):
        d.mkdir(parents=True, exist_ok=True)

    originais = {p.stem: p for p in ORIG.iterdir()
                 if p.suffix != ".pdf" and not p.name.startswith("_")}
    recusados = {k: m for k, p in originais.items()
                 if p.suffix == ".svg" and (m := problema(p.read_bytes()))}
    for k, m in sorted(recusados.items()):
        print(f"SVG recusado, publicado como PNG: {k} ({m})", file=sys.stderr)
    pares = [(p, destino(k, "svg" if p.suffix == ".svg" and k not in recusados else "png"))
             for k, p in sorted(originais.items())]
    with ThreadPoolExecutor(8) as ex:
        erros = [e for e in ex.map(converte, pares) if e]
    for e in erros:
        print("ERRO", e, file=sys.stderr)
    # remove saídas cujo original sumiu ou mudou de formato
    esperados = {d for _, d in pares}
    VET = FLAGS / "mun" / "vetorizado"  # gerado por tools/vetorizar.py
    for p in list(FLAGS.rglob("*.svg")) + list(FLAGS.rglob("*.png")):
        if p.parent == VET:
            # só vale ao lado de um PNG; some se o município ganhou SVG de verdade
            if not (FLAGS / "mun" / f"{p.stem}.png").exists() or problema(p.read_bytes()):
                p.unlink()
        elif p not in esperados:
            p.unlink()

    # --- brasões: só SVG do Commons; o reprovado na conferência entra em PNG ---
    arq_bras = FONTE / "brasoes.json"
    fonte_bras = json.loads(arq_bras.read_text()) if arq_bras.exists() else {}
    for d in (BRASOES / "uf", BRASOES / "mun"):
        d.mkdir(parents=True, exist_ok=True)
    validas = ({"br"} | {u["sigla"].lower() for u in ibge["ufs"]}
               | {str(m["codigo"]) for m in ibge["municipios"]})
    # curadoria manual: arquivo que o Wikidata aponta como brasão e não é
    arq_exc = FONTE / "brasoes_excluidos.json"
    excluidos = json.loads(arq_exc.read_text()) if arq_exc.exists() else {}
    orig_bras = {p.stem: p for p in ORIG_BRASOES.glob("*.svg")
                 if p.stem in fonte_bras and p.stem in validas
                 and p.stem not in excluidos} if ORIG_BRASOES.exists() else {}
    # Brasão municipal pesado (acima do teto depois do svgo) ou que é só um raster
    # embrulhado em SVG entra em PNG. O tamanho final vem do estado do otimizar.py,
    # então a ordem é gerar.py, otimizar.py e gerar.py de novo.
    arq_otim = ORIG / "_otimizados.json"
    otim = json.loads(arq_otim.read_text()) if arq_otim.exists() else {}
    pares_bras, pesados = [], 0
    for k, p in sorted(orig_bras.items()):
        m = problema(p.read_bytes())
        if m:
            print(f"brasão: SVG recusado, publicado como PNG: {k} ({m})", file=sys.stderr)
        o = otim.get(f"brasoes/{k}.svg", {})
        pesado = k.isdigit() and (o.get("bytes", 0) > TETO_BRASAO or o.get("raster_embutido"))
        pesados += bool(pesado and not m)
        pares_bras.append((p, destino(k, "png" if m or pesado else "svg", BRASOES)))
    print(f"brasões municipais pesados, publicados em PNG: {pesados}", file=sys.stderr)
    with ThreadPoolExecutor(8) as ex:
        erros_bras = [e for e in ex.map(converte, pares_bras) if e]
    for e in erros_bras:
        print("ERRO brasão", e, file=sys.stderr)
    erros += erros_bras
    esperados_bras = {d for _, d in pares_bras}
    for p in list(BRASOES.rglob("*.svg")) + list(BRASOES.rglob("*.png")):
        if p not in esperados_bras:
            p.unlink()

    def brasao(e: dict, chave: str) -> None:
        arq = next((d for x in ("svg", "png")
                    if (d := destino(chave, x, BRASOES)).exists()), None)
        if not arq:
            return
        m = fonte_bras[chave]
        e["brasao"] = {
            "arquivo": arq.relative_to(RAIZ).as_posix(),
            "formato": arq.suffix[1:],
            "fonte": {
                "origem": "Wikimedia Commons",
                "arquivo": m["arquivo"],
                "pagina": url_http(m["pagina"]),
                "autor": limpa_autor(m["autor"]),
                "licenca": m["licenca"] or "ver página do arquivo",
                "licenca_url": url_http(m["licenca_url"]),
            },
        }

    def vet(e: dict, arq: Path) -> None:
        v = VET / f"{arq.stem}.svg"
        if arq.suffix == ".png" and arq.parent == FLAGS / "mun" and v.exists():
            e["vetorizado"] = v.relative_to(RAIZ).as_posix()  # traçado automático do PNG

    def entrada(chave: str, nome: str, tipo: str, uf: str | None) -> dict:
        e = bandeira(chave, nome, tipo, uf)
        brasao(e, chave)
        return e

    def bandeira(chave: str, nome: str, tipo: str, uf: str | None) -> dict:
        e = {"codigo": chave, "nome": nome, "tipo": tipo}
        if uf:
            e["uf"] = uf
        w = wd.get(chave)
        if w and w.get("wikidata"):
            e["wikidata"] = w["wikidata"]
        arq = next((d for k in ("svg", "png") if (d := destino(chave, k)).exists()), None)
        x = externos.get(chave)
        if arq and x and not w:  # fonte fora do Commons
            vet(e, arq)
            e["arquivo"] = arq.relative_to(RAIZ).as_posix()
            e["formato"] = arq.suffix[1:]
            e["fonte"] = {
                "origem": x["origem"], "arquivo": x["url"].rsplit("/", 1)[-1],
                "pagina": url_http(x["pagina"]), "autor": x["autor"],
                "licenca": x["licenca"], "licenca_url": "",
            }
            return e
        if not (w and arq):
            e["arquivo"] = None
            return e
        vet(e, arq)
        fonte = origem.get(chave, w["arquivos"][0])  # o arquivo que está em disco
        m = meta[fonte]
        e["arquivo"] = arq.relative_to(RAIZ).as_posix()
        e["formato"] = arq.suffix[1:]
        if m.get("largura") and m.get("altura"):
            e["proporcao"] = round(m["largura"] / m["altura"], 4)
        e["fonte"] = {
            "origem": "Wikimedia Commons",
            "arquivo": fonte,
            "pagina": url_http(m["pagina"]),
            "autor": limpa_autor(m["autor"]),
            "licenca": m["licenca"] or "ver página do arquivo",
            "licenca_url": url_http(m["licenca_url"]),
        }
        return e

    itens = [entrada("br", "Brasil", "pais", None)]
    itens += [entrada(u["sigla"].lower(), u["nome"], "uf", u["sigla"]) for u in ibge["ufs"]]
    itens += [entrada(str(m["codigo"]), m["nome"], "municipio", m["uf"])
              for m in ibge["municipios"]]
    (RAIZ / "dados" / "bandeiras.json").write_text(
        json.dumps(itens, ensure_ascii=False, separators=(",", ":")))

    # --- arquivos só do site: índice enxuto, detalhes por UF e miniaturas ---
    (RAIZ / "dados" / "site.json").write_text(json.dumps(
        [[e["codigo"], e["nome"], e.get("uf", ""), e.get("formato", ""),
          1 if e.get("vetorizado") else 0, 1 if e.get("brasao") else 0] for e in itens],
        ensure_ascii=False, separators=(",", ":")))
    det = RAIZ / "dados" / "detalhe"
    det.mkdir(exist_ok=True)
    grupos: dict[str, dict] = {}
    for e in itens:
        g = e["uf"].lower() if e["tipo"] == "municipio" else "br"
        grupos.setdefault(g, {})[e["codigo"]] = e
    for g, d in grupos.items():
        (det / f"{g}.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")))

    mini = RAIZ / "mini"
    mini.mkdir(exist_ok=True)

    def miniatura(e: dict) -> str | None:
        src, dst = RAIZ / e["arquivo"], mini / f'{e["codigo"]}.webp'
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            return None
        if src.suffix == ".svg":
            r = subprocess.run(["rsvg-convert", "-w", "200", str(src)], capture_output=True)
            if r.returncode != 0:
                return f"miniatura {src.name}: rsvg falhou"
            r = subprocess.run(["magick", "png:-", "-quality", "75", str(dst)],
                               input=r.stdout, capture_output=True)
        else:
            r = subprocess.run(["magick", str(src), "-resize", "200x>", "-quality", "75",
                                str(dst)], capture_output=True)
        return None if r.returncode == 0 else f"miniatura {src.name}: magick falhou"

    com_arquivo = [e for e in itens if e["arquivo"]]
    with ThreadPoolExecutor(8) as ex:
        for erro in ex.map(miniatura, com_arquivo):
            if erro:
                print("ERRO", erro, file=sys.stderr)
    vivos = {f'{e["codigo"]}.webp' for e in com_arquivo}
    for p in mini.glob("*.webp"):
        if p.name not in vivos:
            p.unlink()

    # miniaturas dos brasões (160 px de altura), para os cartões do site
    mini_b = mini / "brasao"
    mini_b.mkdir(exist_ok=True)

    def miniatura_brasao(e: dict) -> str | None:
        src, dst = RAIZ / e["brasao"]["arquivo"], mini_b / f'{e["codigo"]}.webp'
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            return None
        if src.suffix == ".svg":
            r = subprocess.run(["rsvg-convert", "-h", "160", str(src)], capture_output=True)
            if r.returncode != 0:
                return f"miniatura do brasão {src.name}: rsvg falhou"
            r = subprocess.run(["magick", "png:-", "-quality", "80", str(dst)],
                               input=r.stdout, capture_output=True)
        else:
            r = subprocess.run(["magick", str(src), "-resize", "x160>", "-quality", "80",
                                str(dst)], capture_output=True)
        return None if r.returncode == 0 else f"miniatura do brasão {src.name}: magick falhou"

    com_brasao = [e for e in itens if e.get("brasao")]
    with ThreadPoolExecutor(8) as ex:
        for erro in ex.map(miniatura_brasao, com_brasao):
            if erro:
                print("ERRO", erro, file=sys.stderr)
    vivos_b = {f'{e["codigo"]}.webp' for e in com_brasao}
    for p in mini_b.glob("*.webp"):
        if p.name not in vivos_b:
            p.unlink()

    def regra(e: dict, prefixo: str) -> str:
        return f'.fbr-{e["codigo"]}{{background-image:url({prefixo}{e["arquivo"]})}}\n'

    com = [e for e in itens if e["arquivo"]]
    (RAIZ / "css" / "flags-brasil.css").write_text(
        BASE_CSS + "".join(regra(e, "../") for e in com if e["tipo"] != "municipio"))
    muns = [e for e in com if e["tipo"] == "municipio"]
    cab = "/* flags-brasil — municípios{}. Use junto com flags-brasil.css. */\n"
    (RAIZ / "css" / "municipios.css").write_text(
        cab.format("") + "".join(regra(e, "../") for e in muns))
    for u in ibge["ufs"]:
        (RAIZ / "css" / "uf" / f'{u["sigla"].lower()}.css').write_text(
            cab.format(f' de {u["nome"]}')
            + "".join(regra(e, "../../") for e in muns if e["uf"] == u["sigla"]))

    # --- brasões: folhas de estilo ---
    bras = [e for e in itens if e.get("brasao")]

    def regra_b(e: dict) -> str:
        return f'.bbr-{e["codigo"]}{{background-image:url(../{e["brasao"]["arquivo"]})}}\n'

    (RAIZ / "css" / "brasoes.css").write_text(
        BASE_CSS_BRASOES + "".join(regra_b(e) for e in bras if e["tipo"] != "municipio"))
    (RAIZ / "css" / "brasoes-municipios.css").write_text(
        "/* flags-brasil — brasões dos municípios. Use junto com brasoes.css. */\n"
        + "".join(regra_b(e) for e in bras if e["tipo"] == "municipio"))

    linhas = [
        "# Créditos das bandeiras e dos brasões", "",
        "Quase todas as imagens vêm do [Wikimedia Commons](https://commons.wikimedia.org/), "
        "localizadas pela propriedade *imagem da bandeira* (P41) do Wikidata ou pelas "
        "categorias de bandeiras municipais. Cada arquivo mantém a licença indicada na sua "
        "página de origem. Algumas, sem arquivo no Commons, vêm do site da prefeitura: a "
        "coluna Origem indica, e a licença aparece como não declarada (a bandeira é símbolo "
        "oficial do município, mas o arquivo não traz licença); os SVG foram enxugados com svgo "
        "e os rasters reduzidos para até 500 px de largura e convertidos em PNG de 256 cores.", "",
        "Gerado por `tools/gerar.py`. A mesma informação está em `dados/bandeiras.json`.", "",
        "| Código | Local | Arquivo | Autor | Licença | Origem |", "|---|---|---|---|---|---|",
    ]
    for e in com:
        f = e["fonte"]
        autor = f["autor"].replace("|", "\\|")
        if len(autor) > 120:
            autor = autor[:117] + "…"
        lic = f'[{f["licenca"]}]({f["licenca_url"]})' if f["licenca_url"] else f["licenca"]
        local = e["nome"] + (f' ({e["uf"]})' if e["tipo"] == "municipio" else "")
        linhas.append(f'| {e["codigo"]} | {local} | `{e["arquivo"]}` | {autor} | {lic} '
                      f'| [{f["origem"]}]({f["pagina"]}) |')
    linhas += [
        "", "## Brasões", "",
        "Os brasões vêm do Wikimedia Commons, localizados pela propriedade *imagem do "
        "brasão* (P94) do Wikidata; só entram os que existem em SVG. Cada arquivo mantém a "
        "licença indicada na sua página de origem.", "",
        "| Código | Local | Arquivo | Autor | Licença | Origem |", "|---|---|---|---|---|---|",
    ]
    for e in bras:
        f = e["brasao"]["fonte"]
        autor = f["autor"].replace("|", "\\|")
        if len(autor) > 120:
            autor = autor[:117] + "…"
        lic = f'[{f["licenca"]}]({f["licenca_url"]})' if f["licenca_url"] else f["licenca"]
        local = e["nome"] + (f' ({e["uf"]})' if e["tipo"] == "municipio" else "")
        linhas.append(f'| {e["codigo"]} | {local} | `{e["brasao"]["arquivo"]}` | {autor} | {lic} '
                      f'| [{f["origem"]}]({f["pagina"]}) |')
    (RAIZ / "CREDITOS.md").write_text("\n".join(linhas) + "\n")

    n = lambda t, f=None: sum(1 for e in com if e["tipo"] == t and (not f or e["formato"] == f))
    vets = [e for e in com if e.get("vetorizado")]
    (RAIZ / "css" / "vetorizado.css").write_text(
        "/* flags-brasil — troca o PNG pelo SVG vetorizado automaticamente, onde existe.\n"
        "   Carregue DEPOIS da folha de municípios. Traçado automático: pode ter imperfeições. */\n"
        + "".join(f'.fbr-{e["codigo"]}{{background-image:url(../{e["vetorizado"]})}}\n'
                  for e in vets))
    resumo = {
        "ufs": n("uf"), "municipios_total": len(ibge["municipios"]),
        "municipios_com_bandeira": n("municipio"),
        "municipios_svg": n("municipio", "svg"), "municipios_png": n("municipio", "png"),
        "municipios_vetorizados": len(vets),
        "brasoes_ufs": sum(1 for e in bras if e["tipo"] == "uf"),
        "brasoes_municipios": sum(1 for e in bras if e["tipo"] == "municipio"),
        "brasoes_municipios_svg": sum(1 for e in bras if e["tipo"] == "municipio"
                                      and e["brasao"]["formato"] == "svg"),
    }
    (RAIZ / "dados" / "resumo.json").write_text(json.dumps(resumo, indent=1) + "\n")
    por_uf = []
    for u in ibge["ufs"]:
        tot = sum(1 for m in ibge["municipios"] if m["uf"] == u["sigla"])
        c = [e for e in muns if e["uf"] == u["sigla"]]
        s = sum(1 for e in c if e["formato"] == "svg")
        por_uf.append(f'| {u["sigla"]} | {tot} | {len(c)} | {s} | {len(c) - s} | '
                      f'{100 * len(c) / tot:.0f}% |')
    t = resumo
    bloco = "\n".join([
        "<!-- resumo:inicio -->",
        f'Hoje: Brasil, {t["ufs"]} UFs e **{t["municipios_com_bandeira"]} de '
        f'{t["municipios_total"]} municípios** ({t["municipios_svg"]} em SVG, '
        f'{t["municipios_png"]} em PNG, dos quais {t["municipios_vetorizados"]} também '
        f'com SVG vetorizado automaticamente). Brasões: Brasil, {t["brasoes_ufs"]} UFs e '
        f'{t["brasoes_municipios"]} municípios ({t["brasoes_municipios_svg"]} em SVG).', "",
        "<details><summary>Cobertura por UF</summary>", "",
        "| UF | Municípios | Com bandeira | SVG | PNG | Cobertura |", "|---|--:|--:|--:|--:|--:|",
        *por_uf, "", "</details>", "<!-- resumo:fim -->"])
    readme = RAIZ / "README.md"
    txt = readme.read_text()
    a, b = txt.index("<!-- resumo:inicio -->"), txt.index("<!-- resumo:fim -->")
    readme.write_text(txt[:a] + bloco + txt[b + len("<!-- resumo:fim -->"):])
    print(resumo, f"erros={len(erros)}")


if __name__ == "__main__":
    main()
