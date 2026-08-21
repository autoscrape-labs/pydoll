# Capturas de tela e PDFs

Capture a aparência da página: uma captura de tela da página inteira ou de um elemento, ou a página inteira como PDF. O Pydoll usa a própria renderização do Chrome, então a saída corresponde ao que o navegador mostra, e você não roda uma ferramenta de renderização separada.

## Capturar a tela da página

Chame `take_screenshot()` com um caminho de arquivo. A extensão define o formato.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://en.wikipedia.org/wiki/Python_(programming_language)')

        await tab.take_screenshot('python.png')

asyncio.run(main())
```

<p align="center">
  <img src="/docs/resources/images/screenshot-python-wikipedia.png" alt="Artigo da Wikipedia sobre Python capturado pela Pydoll" width="760" />
</p>
<p align="center"><sub>O python.png gerado, o artigo da Wikipedia como a Pydoll capturou.</sub></p>

### Escolher o formato

O formato segue a extensão do arquivo: PNG (sem perdas), JPEG (menor, com perdas), ou WebP. `quality` vai de 0 a 100 e se aplica aos formatos com perdas.

```python
await tab.take_screenshot('page.png')               # sem perdas
await tab.take_screenshot('page.jpeg', quality=85)  # arquivo menor
await tab.take_screenshot('page.webp', quality=90)
```

!!! note "O formato vem da extensão"
    Uma extensão não suportada levanta `InvalidFileExtension`. Tanto `.jpg` quanto `.jpeg` funcionam; `.jpg` é normalizado para `.jpeg` internamente.

### Capturar a página rolável inteira

Por padrão você obtém o viewport visível. Passe `beyond_viewport=True` para capturar tudo abaixo da dobra, até o final.

```python
await tab.take_screenshot('full-article.png', beyond_viewport=True)
```

!!! warning "Páginas longas custam memória"
    Em páginas muito longas, `beyond_viewport=True` demora mais e usa mais memória, porque a página inteira é renderizada de uma vez.

### Obter a imagem em memória

Passe `as_base64=True` para receber uma string base64 em vez de escrever um arquivo. Use para embutir a imagem ou enviá-la a algum lugar, sem arquivo temporário para limpar.

```python
data = await tab.take_screenshot(as_base64=True)

html = f'<img src="data:image/png;base64,{data}" />'
```

## Capturar a tela de um único elemento

Chame `take_screenshot()` em um elemento para capturar apenas esse elemento. O Pydoll o rola para a área visível primeiro.

```python
await tab.go_to('https://en.wikipedia.org/wiki/Python_(programming_language)')

infobox = await tab.find(class_name='infobox')
await infobox.take_screenshot('infobox.png')
```

É assim também que você captura conteúdo dentro de um iframe: `tab.take_screenshot()` só enxerga a página de nível superior, então encontre um elemento dentro do frame e capture esse elemento no lugar.

```python
iframe = await tab.find(tag_name='iframe')
content = await iframe.find(id='content')
await content.take_screenshot('iframe-content.png')
```

| | `tab.take_screenshot()` | `element.take_screenshot()` |
|---|---|---|
| Escopo | Viewport ou página inteira | Um elemento |
| `beyond_viewport` | Sim | Não se aplica |
| `as_base64` | Sim | Sim |
| Rola para a área visível | Não | Sim |
| Alcança conteúdo de iframe | Não | Sim |

## Exportar a página como PDF

`print_to_pdf()` renderiza a página pelo pipeline de impressão do Chrome. Passe um caminho, ou `as_base64=True` para os bytes em memória.

```python
import asyncio
from pathlib import Path

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://en.wikipedia.org/wiki/Python_(programming_language)')

        await tab.print_to_pdf(Path('python.pdf'))

asyncio.run(main())
```

### Controlar a saída

| Parâmetro | Padrão | O que faz |
|---|---|---|
| `path` | `None` | Onde salvar. Obrigatório, a menos que `as_base64=True`. |
| `landscape` | `False` | Orientação paisagem em vez de retrato. |
| `display_header_footer` | `False` | Adiciona o título, a URL e os números de página do Chrome. |
| `print_background` | `True` | Inclui gráficos e cores de fundo. |
| `scale` | `1.0` | Fator de zoom, 0.1 a 2.0. Abaixo de 1.0 cabe mais por página. |
| `as_base64` | `False` | Retorna uma string base64 em vez de escrever um arquivo. |

```python
# relatório em paisagem com cabeçalho e rodapé, levemente reduzido
await tab.print_to_pdf(
    Path('report.pdf'),
    landscape=True,
    display_header_footer=True,
    scale=0.9,
)

# econômico em tinta: sem gráficos de fundo
await tab.print_to_pdf(Path('draft.pdf'), print_background=False)

# bytes em memória, sem arquivo
pdf_data = await tab.print_to_pdf(as_base64=True)
```

## Salvar uma página para visualização offline

`save_bundle()` grava a página e seus assets (CSS, JS, imagens, fontes, mídia) em um `.zip` que você pode abrir depois. O arquivo contém um `index.html` com as URLs reescritas para os arquivos locais.

```python
await tab.save_bundle('page.zip')
```

Passe `inline_assets=True` para embutir tudo em um único `index.html` autocontido usando data URIs e tags `<style>`/`<script>` inline:

```python
await tab.save_bundle('page-inline.zip', inline_assets=True)
```

!!! note "O que é empacotado"
    Documentos, folhas de estilo, scripts, imagens, fontes e mídia. Recursos que falharam ao carregar, foram cancelados, ou usam URIs `data:` são ignorados.

## Lidar com os erros comuns

```python
from pydoll.exceptions import InvalidFileExtension, MissingScreenshotPath

# sem caminho e as_base64 é False
try:
    await tab.take_screenshot()
except MissingScreenshotPath:
    print('Pass a path, or set as_base64=True.')

# extensão não suportada
try:
    await tab.take_screenshot('image.bmp')
except InvalidFileExtension as error:
    print(error)
```

## Próximos passos

- [Percorrer o DOM](dom-traversal.md): encontre o elemento que você quer capturar, inclusive dentro de iframes.
- [Iframes](iframes.md): trabalhe com o conteúdo de frames em profundidade.
- [Referência da API Tab](../api/browser/tab.md): assinaturas completas de `take_screenshot`, `print_to_pdf` e `save_bundle`.
