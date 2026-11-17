# flags-brasil

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.24286741-0b7a43)](https://doi.org/10.5281/zenodo.24286741)
[![Versão](https://img.shields.io/github/v/release/StrategicProjects/flags-brasil?label=vers%C3%A3o)](https://github.com/StrategicProjects/flags-brasil/releases/latest)
[![npm](https://img.shields.io/npm/v/flags-brasil?label=npm)](https://www.npmjs.com/package/flags-brasil)
[![npm municípios](https://img.shields.io/npm/v/flags-brasil-municipios?label=npm%20munic%C3%ADpios)](https://www.npmjs.com/package/flags-brasil-municipios)
[![Código MIT](https://img.shields.io/badge/c%C3%B3digo-MIT-blue)](LICENSE)

Bandeiras do Brasil, das 27 unidades da federação e dos municípios, prontas para
usar em sites, painéis e relatórios. Inspirado no
[flag-icons](https://github.com/lipis/flag-icons), com o recorte que ele não
cobre: estados e municípios brasileiros.

**Site e busca:** <https://strategicprojects.github.io/flags-brasil/>

- Arquivos nomeados pela sigla da UF (`pe`) e pelo código do IBGE de 7 dígitos
  (`2611606`).
- SVG quando existe um vetor no Wikimedia Commons; PNG de até 500 px de largura
  quando só há imagem raster.
- Classes CSS no estilo do flag-icons, um manifesto JSON e créditos por arquivo.
- Brasões em SVG do Brasil, das UFs e de parte dos municípios, em `brasoes/`.

<!-- resumo:inicio -->
Hoje: Brasil, 27 UFs e **4085 de 5571 municípios** (603 em SVG, 3482 em PNG, dos quais 753 também com SVG vetorizado automaticamente). Brasões: Brasil, 27 UFs e 404 municípios (314 em SVG).

<details><summary>Cobertura por UF</summary>

| UF | Municípios | Com bandeira | SVG | PNG | Cobertura |
|---|--:|--:|--:|--:|--:|
| AC | 22 | 14 | 7 | 7 | 64% |
| AL | 102 | 65 | 9 | 56 | 64% |
| AM | 62 | 47 | 16 | 31 | 76% |
| AP | 16 | 13 | 9 | 4 | 81% |
| BA | 417 | 179 | 44 | 135 | 43% |
| CE | 184 | 141 | 23 | 118 | 77% |
| DF | 1 | 1 | 1 | 0 | 100% |
| ES | 78 | 64 | 11 | 53 | 82% |
| GO | 246 | 169 | 10 | 159 | 69% |
| MA | 217 | 89 | 20 | 69 | 41% |
| MG | 853 | 584 | 26 | 558 | 68% |
| MS | 79 | 75 | 5 | 70 | 95% |
| MT | 142 | 72 | 7 | 65 | 51% |
| PA | 144 | 93 | 20 | 73 | 65% |
| PB | 223 | 193 | 63 | 130 | 87% |
| PE | 185 | 180 | 46 | 134 | 97% |
| PI | 224 | 68 | 9 | 59 | 30% |
| PR | 399 | 383 | 44 | 339 | 96% |
| RJ | 92 | 92 | 22 | 70 | 100% |
| RN | 167 | 117 | 1 | 116 | 70% |
| RO | 52 | 41 | 16 | 25 | 79% |
| RR | 15 | 15 | 8 | 7 | 100% |
| RS | 497 | 413 | 26 | 387 | 83% |
| SC | 295 | 273 | 69 | 204 | 93% |
| SE | 75 | 57 | 19 | 38 | 76% |
| SP | 645 | 617 | 67 | 550 | 96% |
| TO | 139 | 30 | 5 | 25 | 22% |

</details>
<!-- resumo:fim -->

## Usar por classe CSS

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/StrategicProjects/flags-brasil@main/css/flags-brasil.css">

<span class="fbr fbr-br"></span>   <!-- Brasil -->
<span class="fbr fbr-pe"></span>   <!-- Pernambuco -->
```

`flags-brasil.css` traz o Brasil e as UFs. Os municípios ficam em folhas
separadas, para não carregar milhares de regras sem precisar:

```html
<!-- municípios de uma UF -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/StrategicProjects/flags-brasil@main/css/uf/pe.css">
<!-- ou todos -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/StrategicProjects/flags-brasil@main/css/municipios.css">

<span class="fbr fbr-2611606"></span>   <!-- Recife -->
```

A bandeira tem a altura do texto (`1em`) e mantém a proporção original dentro de
um quadro 10:7. Para recortar num quadro fixo, some `fbr-1x1` ou `fbr-4x3`.

## Usar por arquivo

| Caminho | Conteúdo |
|---|---|
| `flags/br.svg` | bandeira nacional |
| `flags/uf/<sigla>.svg` | unidade da federação, sigla minúscula |
| `flags/mun/<codigo>.svg` ou `.png` | município, código do IBGE |
| `dados/bandeiras.json` | manifesto: nome, UF, arquivo, formato, proporção, autor, licença |
| `css/` | folhas de estilo |

Endereços diretos: `https://strategicprojects.github.io/flags-brasil/flags/uf/pe.svg`
ou pelo jsDelivr, `https://cdn.jsdelivr.net/gh/StrategicProjects/flags-brasil@main/flags/uf/pe.svg`.

### SVG vetorizado automaticamente

Para parte dos municípios que só têm PNG existe também
`flags/mun/vetorizado/<codigo>.svg`, traçado automaticamente a partir do raster
com o [vtracer](https://github.com/visioncortex/vtracer). O PNG continua sendo o
arquivo padrão (`arquivo` no manifesto); o traçado aparece no campo
`vetorizado`. Não é redesenho: escala sem pixelar, mas as bordas podem ondular,
texto pequeno perde nitidez e o arquivo é mais pesado (até 300 KB). Só entra o
que passa numa comparação automática com o original. Para usar por classe CSS,
carregue `css/vetorizado.css` depois da folha de municípios.

Como o formato do município varia, consulte o manifesto antes de montar a URL:

```js
const bandeiras = await (await fetch(
  'https://strategicprojects.github.io/flags-brasil/dados/bandeiras.json')).json();
const recife = bandeiras.find((b) => b.codigo === '2611606');
recife.arquivo; // "flags/mun/2611606.svg", ou null se não houver bandeira
```

```r
b <- jsonlite::fromJSON("https://strategicprojects.github.io/flags-brasil/dados/bandeiras.json")
base <- "https://strategicprojects.github.io/flags-brasil/"
paste0(base, b$arquivo[b$codigo == "2611606"])
```

Em Quarto/Markdown: `![](https://strategicprojects.github.io/flags-brasil/flags/uf/pe.svg){height=1em}`.

## Brasões

Além das bandeiras, o acervo traz os brasões que existem em SVG no Wikimedia
Commons (propriedade *imagem do brasão*, P94, do Wikidata): o do Brasil, os das
27 UFs e os de parte dos municípios. Brasão que só existe em JPG ou PNG no
Commons ainda não entra. Brasão municipal cujo SVG passa de 300 KB depois do
svgo, ou que é só uma imagem raster embrulhada em SVG, é publicado em PNG de até
500 px, assim como o que não passa na conferência de segurança. Arquivo que o
Wikidata aponta como brasão e não é (logotipo de prefeitura, por exemplo) sai
pela lista `dados/fonte/brasoes_excluidos.json`.

| Caminho | Conteúdo |
|---|---|
| `brasoes/br.svg` | brasão nacional |
| `brasoes/uf/<sigla>.svg` | unidade da federação |
| `brasoes/mun/<codigo>.svg` ou `.png` | município, código do IBGE |
| `css/brasoes.css` | classes `.bbr-br` e `.bbr-<sigla>` |
| `css/brasoes-municipios.css` | classes `.bbr-<codigo>`; carregue junto com `brasoes.css` |

```html
<link rel="stylesheet" href="https://strategicprojects.github.io/flags-brasil/css/brasoes.css">
<span class="bbr bbr-pe"></span>
```

No manifesto, quem tem brasão ganha o campo `brasao`, com `arquivo`, `formato` e
`fonte` (autor, licença e página de origem), inclusive municípios que ainda não
têm bandeira no acervo:

```js
recife.brasao?.arquivo; // "brasoes/mun/2611606.png", ou undefined se não houver
```

Os brasões ficam no repositório e no site, fora dos pacotes npm.

## Pelo npm

```sh
npm install flags-brasil                 # Brasil, UFs, CSS base e manifesto (~1,5 MB)
npm install flags-brasil-municipios      # municípios e CSS por UF
```

```js
import 'flags-brasil/css/flags-brasil.css';
import 'flags-brasil-municipios/css/uf/pe.css';
```

Os caminhos dentro dos pacotes são os mesmos deste repositório. Pelo CDN:
`https://cdn.jsdelivr.net/npm/flags-brasil/css/flags-brasil.css` e, para os
municípios, `https://unpkg.com/flags-brasil-municipios/css/uf/pe.css` (o
jsDelivr não estava servindo o pacote de municípios quando testamos). Os SVG vetorizados
ficam só no repositório e no site, fora do pacote npm.

## Créditos e licenças

As imagens vêm do [Wikimedia Commons](https://commons.wikimedia.org/) e foram
localizadas pela propriedade *imagem da bandeira* (P41) do
[Wikidata](https://www.wikidata.org/). **Cada bandeira mantém a licença do
arquivo de origem.** A maioria está em domínio público; parte está sob Creative
Commons (BY ou BY-SA) ou licenças equivalentes, que exigem atribuição e, no caso
das BY-SA, compartilhamento pela mesma licença.

Quando não há arquivo no Commons, a bandeira pode vir do **site da prefeitura**
(`dados/fonte/externos.json`). Nesses casos `fonte.origem` diz "site da
prefeitura", `fonte.pagina` aponta para a página consultada e a licença aparece
como não declarada: a bandeira é símbolo oficial do município, mas o arquivo não
traz licença explícita.

Os brasões seguem a mesma regra: vêm do Commons, pela propriedade *imagem do
brasão* (P94), e cada um mantém a licença do arquivo de origem.

- [`CREDITOS.md`](CREDITOS.md) lista autor, licença e página de origem de cada arquivo.
- `dados/bandeiras.json` traz o mesmo em `fonte` (`autor`, `licenca`,
  `licenca_url`, `pagina`), para gerar a atribuição no seu projeto.
- O site mostra o crédito ao abrir cada bandeira.

Ao usar uma bandeira com licença de atribuição, cite o autor e a licença
indicados. As alterações feitas aqui: os SVG passaram pelo
[svgo](https://github.com/svg/svgo) (cada resultado é comparado com o original e descartado se o desenho mudar) e as imagens raster
foram reduzidas para até 500 px de largura e convertidas em PNG de 256 cores.

O código (scripts, CSS e site) é [MIT](LICENSE). Bandeiras são símbolos oficiais;
o uso de cada uma pode ser regulado por lei do respectivo ente.

## Como citar

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24286741.svg)](https://doi.org/10.5281/zenodo.24286741)

Os dados de citação estão em [`CITATION.cff`](CITATION.cff); no GitHub, use o
botão "Cite this repository". O DOI acima aponta sempre para a versão mais
recente arquivada no Zenodo; cada release tem também um DOI próprio.

## Cobertura e correções

Nem todo município tem bandeira no Commons, e parte das que existem só está em
JPG ou PNG. O site permite filtrar os que faltam. Para incluir ou corrigir uma
bandeira, o caminho é a fonte: envie o arquivo ao Wikimedia Commons e preencha
*imagem da bandeira* no item do município no Wikidata; ela entra na próxima
atualização. Erros de associação (bandeira de outro município, brasão no lugar
da bandeira) podem ser relatados nas
[issues](https://github.com/StrategicProjects/flags-brasil/issues).

## Atualizar o acervo

Precisa de Python 3.10+, ImageMagick e pnpm.

```sh
python3 tools/baixar.py   # IBGE + Wikidata + Commons -> dados/fonte/ e originais/
python3 tools/brasoes.py  # brasões em SVG (P94) -> dados/fonte/brasoes.json e originais/_brasoes/
python3 tools/gerar.py    # flags/, brasoes/, css/, dados/bandeiras.json, CREDITOS.md
pnpm install && pnpm run otimizar   # svgo nos SVG, conferindo o render
python3 tools/gerar.py    # de novo: troca por PNG os brasões que ficaram acima do teto
uv run tools/vetorizar.py --uf PE   # opcional: SVG vetorizado dos rasters (depois, gerar.py de novo)
pnpm run site             # http://localhost:8377
```

`baixar.py` é retomável e respeita o limite de requisições do Commons: quando o
servidor recusa um original (comum atrás de VPN), entra uma miniatura
provisória, e uma nova execução troca pelo original. Para refazer as listas do
zero, apague `dados/fonte/wikidata.json` e `dados/fonte/commons.json`.
