#!/usr/bin/env python3
"""Monta o pacote npm dos municípios em npm/flags-brasil-municipios/.

São dois pacotes:
  flags-brasil             a raiz deste repo: Brasil, UFs, CSS base e manifesto
  flags-brasil-municipios  bandeiras municipais e CSS por UF (sem os vetorizados)

Os caminhos dentro dos dois são os mesmos do repo (css/ ao lado de flags/), então
as folhas de estilo funcionam sem ajuste. Para publicar:
  npm publish                                   (raiz)
  python3 tools/empacotar.py && npm publish npm/flags-brasil-municipios
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DEST = RAIZ / "npm" / "flags-brasil-municipios"

README = """# flags-brasil-municipios

Bandeiras dos municípios do Brasil, nomeadas pelo código do IBGE: SVG quando
existe, PNG quando não. Complemento do pacote
[`flags-brasil`](https://www.npmjs.com/package/flags-brasil), que traz a bandeira
nacional, as das 27 UFs e a folha de estilo base.

Site e busca: <https://strategicprojects.github.io/flags-brasil/>

```sh
npm install flags-brasil flags-brasil-municipios
```

```js
import 'flags-brasil/css/flags-brasil.css';            // base + Brasil + UFs
import 'flags-brasil-municipios/css/uf/pe.css';        // municípios de uma UF
// ou 'flags-brasil-municipios/css/municipios.css' para todos
```

```html
<span class="fbr fbr-2611606"></span>  <!-- Recife -->
```

| Caminho | Conteúdo |
|---|---|
| `flags/mun/<codigo>.svg` ou `.png` | bandeira do município |
| `css/municipios.css`, `css/uf/<sigla>.css` | classes `.fbr-<codigo>` |
| `dados/bandeiras.json` | nome, UF, arquivo, formato, autor e licença |

## Licenças

O código é MIT. **Cada bandeira mantém a licença do arquivo de origem**
(Wikimedia Commons, na maioria; algumas do site da prefeitura): muitas em domínio
público, parte em Creative Commons BY ou BY-SA, que exigem atribuição. Autor,
licença e página de origem de cada arquivo estão em `CREDITOS.md` e em
`dados/bandeiras.json` (campo `fonte`).

Os SVG vetorizados automaticamente (`flags/mun/vetorizado/`) não entram neste
pacote, pelo tamanho; estão no repositório e no site, e o campo `vetorizado` do
manifesto aponta para eles.

Pelo CDN use o unpkg (o jsDelivr não estava servindo este pacote quando testamos):
`https://unpkg.com/flags-brasil-municipios/css/uf/pe.css`.

Documentação completa: <https://github.com/StrategicProjects/flags-brasil>
"""


def main() -> None:
    raiz_pkg = json.loads((RAIZ / "package.json").read_text())
    if DEST.exists():
        shutil.rmtree(DEST)
    (DEST / "flags").mkdir(parents=True)
    (DEST / "css").mkdir()
    (DEST / "dados").mkdir()
    # os vetorizados ficam só no repositório e no site: somariam ~45 MB ao pacote
    shutil.copytree(RAIZ / "flags" / "mun", DEST / "flags" / "mun",
                    ignore=shutil.ignore_patterns("vetorizado"))
    shutil.copytree(RAIZ / "css" / "uf", DEST / "css" / "uf")
    shutil.copyfile(RAIZ / "css" / "municipios.css", DEST / "css" / "municipios.css")
    shutil.copyfile(RAIZ / "dados" / "bandeiras.json", DEST / "dados" / "bandeiras.json")
    for f in ("CREDITOS.md", "LICENSE"):
        shutil.copyfile(RAIZ / f, DEST / f)
    (DEST / "README.md").write_text(README)
    (DEST / "package.json").write_text(json.dumps({
        "name": "flags-brasil-municipios",
        "version": raiz_pkg["version"],
        "description": "Bandeiras dos municípios do Brasil por código do IBGE (SVG ou PNG), "
                       "com classes CSS. Complemento do flags-brasil.",
        "keywords": ["bandeiras", "brasil", "municipios", "flags", "svg", "ibge", "css"],
        "homepage": raiz_pkg["homepage"],
        "repository": raiz_pkg["repository"],
        "bugs": {"url": "https://github.com/StrategicProjects/flags-brasil/issues"},
        "license": "SEE LICENSE IN LICENSE",
        "author": raiz_pkg["author"],
        "contributors": raiz_pkg["contributors"],
        "style": "css/municipios.css",
        "peerDependencies": {"flags-brasil": f'^{raiz_pkg["version"]}'},
    }, ensure_ascii=False, indent=2) + "\n")
    n = sum(1 for _ in (DEST / "flags").rglob("*.*"))
    print(f"{DEST.relative_to(RAIZ)}: {n} bandeiras, versão {raiz_pkg['version']}")


if __name__ == "__main__":
    main()
