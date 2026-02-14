# Capturas de Tela (Screenshots) e PDFs

O Pydoll oferece poderosas capacidades de captura de tela e geração de PDF através de comandos diretos do Chrome DevTools Protocol. Capture páginas inteiras, elementos específicos ou gere PDFs com controle refinado.

## Capturas de Tela

### Captura de Tela Básica da Página

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def take_page_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Salvar captura de tela em arquivo
        await tab.take_screenshot('page.png', quality=100)

asyncio.run(take_page_screenshot())
```

### Formatos Suportados

O Pydoll suporta três formatos de imagem com base na extensão do arquivo:

```python
# Formato PNG (sem perdas, tamanho de arquivo maior)
await tab.take_screenshot('screenshot.png', quality=100)

# Formato JPEG (com perdas, tamanho de arquivo menor)
await tab.take_screenshot('screenshot.jpeg', quality=85)

# Formato WebP (moderno, eficiente)
await tab.take_screenshot('screenshot.webp', quality=90)
```

!!! info "Detecção de Formato"
    O formato da imagem é determinado automaticamente pela extensão do arquivo. Usar uma extensão não suportada lança `InvalidFileExtension`.
    
    Tanto `.jpg` quanto `.jpeg` são suportados para o formato JPEG (`.jpg` é normalizado automaticamente para `.jpeg` internamente para corresponder aos requisitos do CDP).

### Parâmetros de Captura de Tela

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `path` | `Optional[str]` | `None` | Caminho do arquivo para salvar a captura de tela. Obrigatório se `as_base64=False`. |
| `quality` | `int` | `100` | Qualidade da imagem (0-100). Valores mais altos significam melhor qualidade e arquivos maiores. |
| `beyond_viewport` | `bool` | `False` | Captura a página inteira rolável, não apenas a área visível. |
| `as_base64` | `bool` | `False` | Retorna a string codificada em base64 em vez de salvar em arquivo. |

### Captura de Tela de Página Inteira

Capture conteúdo além da área visível (viewport):

```python
async def full_page_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/long-page')
        
        # Captura a página inteira, incluindo conteúdo abaixo da dobra
        await tab.take_screenshot(
            'full-page.png',
            beyond_viewport=True,
            quality=90
        )
```

!!! warning "Nota de Desempenho"
    Usar `beyond_viewport=True` em páginas muito longas pode consumir memória significativa e levar mais tempo para processar.

### Captura de Tela em Base64

Obtenha a captura de tela como string base64 para incorporar ou enviar via API:

```python
async def base64_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Obter captura de tela como string base64
        screenshot_base64 = await tab.take_screenshot(
            as_base64=True
        )
        
        # Usar em tag img HTML
        html = f'<img src="data:image/png;base64,{screenshot_base64}" />'
        
        # Ou enviar via API
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post(
                'https://api.example.com/upload',
                json={'image': screenshot_base64}
            )
```

### Captura de Tela de Elemento

Capture elementos específicos em vez da página inteira:

```python
async def element_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Capturar um elemento específico (PNG)
        header = await tab.find(tag_name='header')
        await header.take_screenshot('header.png', quality=100)
        
        # Capturar um formulário (JPEG)
        form = await tab.find(id='login-form')
        await form.take_screenshot('login-form.jpeg', quality=85)
        
        # Capturar um gráfico (WebP)
        chart = await tab.find(class_name='data-visualization')
        await chart.take_screenshot('chart.webp', quality=90)
```

!!! info "Detecção de Formato"
    O formato da imagem é detectado automaticamente a partir da extensão do arquivo (`.png`, `.jpeg`/`.jpg`, ou `.webp`). Usar uma extensão não suportada lança `InvalidFileExtension`.

!!! tip "Rolagem Automática"
    Ao capturar screenshots de elementos, o Pydoll rola automaticamente o elemento para a visão antes de tirar a foto.

### Capturas de Tela de Elemento vs Página

| Característica | `tab.take_screenshot()` | `element.take_screenshot()` |
|---|---|---|
| **Escopo** | Viewport inteira ou página | Apenas elemento específico |
| **Suporte a Formato** | PNG, JPEG, WebP | PNG, JPEG, WebP |
| **Além da Viewport** | Suportado | Não aplicável |
| **Saída Base64** | Suportado | Suportado |
| **Auto-Scroll** | Não aplicável | Sim |
| **Caso de Uso** | Capturas de página inteira | Isolamento de componente, testes |


## Geração de PDF

### Exportação Básica de PDF

Converta páginas para PDF com qualidade de impressão:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def generate_pdf():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/document')
        
        # Gerar PDF com Path
        await tab.print_to_pdf(Path('document.pdf'))
        
        # Ou com string
        await tab.print_to_pdf('document.pdf')

asyncio.run(generate_pdf())
```

### Parâmetros de PDF

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `path` | `Optional[str \| Path]` | `None` | Caminho do arquivo para salvar o PDF. Obrigatório se `as_base64=False`. |
| `landscape` | `bool` | `False` | Usar orientação paisagem (vs retrato). |
| `display_header_footer` | `bool` | `False` | Incluir cabeçalho/rodapé gerado pelo navegador com título, URL, números de página. |
| `print_background` | `bool` | `True` | Incluir gráficos e cores de fundo. |
| `scale` | `float` | `1.0` | Fator de escala da página (0.1-2.0). Útil para efeitos de zoom/redução. |
| `as_base64` | `bool` | `False` | Retorna string codificada em base64 em vez de salvar em arquivo. |

!!! tip "Path vs String"
    Embora objetos `Path` do `pathlib` sejam recomendados como melhor prática para melhor manipulação de caminhos e compatibilidade entre plataformas, você também pode usar strings simples, se preferir.

### Opções Avançadas de PDF

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def advanced_pdf():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/report')
        
        # PDF paisagem com cabeçalhos/rodapés
        await tab.print_to_pdf(
            Path('report-landscape.pdf'),
            landscape=True,
            display_header_footer=True,
            print_background=True,
            scale=0.9
        )
        
        # PDF retrato sem fundos (amigável à tinta)
        await tab.print_to_pdf(
            Path('report-ink-friendly.pdf'),
            landscape=False,
            print_background=False,
            scale=1.0
        )

asyncio.run(advanced_pdf())
```

### Fator de Escala do PDF

Controle o nível de zoom da saída em PDF:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def scaled_pdfs():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/content')
        
        # Encolher conteúdo para caber mais em cada página
        await tab.print_to_pdf(Path('compact.pdf'), scale=0.7)
        
        # Escala normal
        await tab.print_to_pdf(Path('normal.pdf'), scale=1.0)
        
        # Ampliar conteúdo (menos páginas)
        await tab.print_to_pdf(Path('large.pdf'), scale=1.5)

asyncio.run(scaled_pdfs())
```

!!! warning "Limites de Escala"
    O parâmetro `scale` aceita valores entre `0.1` e `2.0`. Valores fora dessa faixa podem produzir resultados inesperados.

### PDF em Base64

Gere PDF como string base64 para transmissão via API:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def base64_pdf():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/invoice')
        
        # Obter PDF como base64 (não precisa de caminho)
        pdf_base64 = await tab.print_to_pdf(as_base64=True)
        
        # Enviar via API
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post(
                'https://api.example.com/invoices',
                json={'pdf': pdf_base64}
            )

asyncio.run(base64_pdf())
```


!!! info "Referência do CDP"
    Para documentação completa do CDP sobre esses comandos, veja:
    
    - [Page.captureScreenshot](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-captureScreenshot)
    - [Page.printToPDF](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-printToPDF)

### Tratamento de Erros

```python
from pydoll.exceptions import (
    InvalidFileExtension,
    MissingScreenshotPath,
    TopLevelTargetRequired
)

async def safe_screenshot():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        try:
            # Caminho faltando e as_base64=False
            await tab.take_screenshot()
        except MissingScreenshotPath:
            print("Erro: Deve fornecer o caminho ou definir as_base64=True")
        
        try:
            # Extensão inválida
            await tab.take_screenshot('image.bmp')
        except InvalidFileExtension as e:
            print(f"Erro: {e}")
        
        # Limitação de screenshot de IFrame
        iframe_element = await tab.find(tag_name='iframe')

        # Isso ainda não funciona: screenshots de nível superior ignoram iframes
        # await tab.take_screenshot('frame.png')

        # Capture um elemento dentro do próprio iframe
        content = await iframe_element.find(id='content')
        await content.take_screenshot('iframe-content.png')
```

## Exportação de Bundle da Página

Salve uma página inteira com todos os seus assets (CSS, JS, imagens, fontes) como um arquivo `.zip` para visualização offline.

### Uso Básico

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def save_page():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

        # Salvar página com assets como arquivos separados
        await tab.save_bundle('page.zip')

asyncio.run(save_page())
```

O zip resultante contém um `index.html` com todas as URLs reescritas para referenciar arquivos locais no diretório `assets/`.

### Modo Inline

Incorpore tudo diretamente em um único `index.html` usando data URIs, `<style>` e `<script>`:

```python
# Um único arquivo HTML autocontido dentro do zip
await tab.save_bundle('page-inline.zip', inline_assets=True)
```

### Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `path` | `str \| Path` | *(obrigatório)* | Caminho de destino. Deve terminar com `.zip`. |
| `inline_assets` | `bool` | `False` | Incorporar todos os assets inline em vez de salvá-los como arquivos separados. |

!!! info "O Que é Incluído no Bundle"
    O bundle inclui recursos dos tipos: Document, Stylesheet, Script, Image, Font e Media. Recursos que falharam ao carregar, foram cancelados ou usam URIs `data:` são automaticamente ignorados.

## Aprenda Mais

Para contexto adicional sobre como screenshots e PDFs se integram com a arquitetura do Pydoll:

- **[Análise Profunda: CDP](../../deep-dive/cdp.md)**: Entendendo os comandos do Chrome DevTools Protocol
- **[Referência da API: Tab](../../api/browser/tab.md#take_screenshot)**: Assinaturas de método e parâmetros completos
- **[Referência da API: WebElement](../../api/elements/web-element.md#take_screenshot)**: Capacidades de screenshot específicas de elementos

Screenshots e PDFs são ferramentas essenciais para automação, testes e documentação. A integração direta do Pydoll com o CDP fornece saída de nível profissional com controle refinado.