# flags-brasil

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

<!-- resumo:inicio -->
Hoje: Brasil, 27 UFs e **4082 de 5571 municípios** (12 em SVG, 4070 em PNG).

<details><summary>Cobertura por UF</summary>

| UF | Municípios | Com bandeira | SVG | PNG | Cobertura |
|---|--:|--:|--:|--:|--:|
| AC | 22 | 14 | 1 | 13 | 64% |
| AL | 102 | 65 | 0 | 65 | 64% |
| AM | 62 | 47 | 0 | 47 | 76% |
| AP | 16 | 13 | 0 | 13 | 81% |
| BA | 417 | 179 | 0 | 179 | 43% |
| CE | 184 | 141 | 0 | 141 | 77% |
| DF | 1 | 1 | 0 | 1 | 100% |
| ES | 78 | 64 | 0 | 64 | 82% |
| GO | 246 | 169 | 0 | 169 | 69% |
| MA | 217 | 89 | 0 | 89 | 41% |
| MG | 853 | 584 | 0 | 584 | 68% |
| MS | 79 | 75 | 0 | 75 | 95% |
| MT | 142 | 72 | 0 | 72 | 51% |
| PA | 144 | 93 | 0 | 93 | 65% |
| PB | 223 | 193 | 0 | 193 | 87% |
| PE | 185 | 177 | 2 | 175 | 96% |
| PI | 224 | 68 | 0 | 68 | 30% |
| PR | 399 | 383 | 2 | 381 | 96% |
| RJ | 92 | 92 | 0 | 92 | 100% |
| RN | 167 | 117 | 0 | 117 | 70% |
| RO | 52 | 41 | 5 | 36 | 79% |
| RR | 15 | 15 | 0 | 15 | 100% |
| RS | 497 | 413 | 0 | 413 | 83% |
| SC | 295 | 273 | 2 | 271 | 93% |
| SE | 75 | 57 | 0 | 57 | 76% |
| SP | 645 | 617 | 0 | 617 | 96% |
| TO | 139 | 30 | 0 | 30 | 22% |

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

Para instalar como dependência sem publicar no npm:
`pnpm add github:StrategicProjects/flags-brasil`.

## Créditos e licenças

As imagens vêm do [Wikimedia Commons](https://commons.wikimedia.org/) e foram
localizadas pela propriedade *imagem da bandeira* (P41) do
[Wikidata](https://www.wikidata.org/). **Cada bandeira mantém a licença do
arquivo de origem.** A maioria está em domínio público; parte está sob Creative
Commons (BY ou BY-SA) ou licenças equivalentes, que exigem atribuição e, no caso
das BY-SA, compartilhamento pela mesma licença.

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
python3 tools/gerar.py    # flags/, css/, dados/bandeiras.json, CREDITOS.md
pnpm install && pnpm run otimizar   # svgo nos SVG, conferindo o render
pnpm run site             # http://localhost:8377
```

`baixar.py` é retomável e respeita o limite de requisições do Commons: quando o
servidor recusa um original (comum atrás de VPN), entra uma miniatura
provisória, e uma nova execução troca pelo original. Para refazer as listas do
zero, apague `dados/fonte/wikidata.json` e `dados/fonte/commons.json`.
