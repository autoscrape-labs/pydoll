# Trabalhando com IFrames

Páginas modernas usam `<iframe>` para embutir outros documentos. Nas versões antigas do Pydoll era necessário transformar o iframe em uma `Tab` com `tab.get_frame()` e cuidar de alvos CDP manualmente. **Isso acabou.**  
Agora um iframe se comporta como qualquer outro `WebElement`: você pode chamar `find()`, `query()`, `execute_script()`, `inner_html`, `text` e todos os utilitários diretamente — o Pydoll encaminha a operação para o contexto correto em qualquer domínio.

!!! info "Modelo mental simples"
    Pense no iframe como mais uma `div`. Localize o elemento, guarde a referência e continue a navegação a partir dele. O Pydoll se encarrega de criar o mundo isolado, configurar o contexto JavaScript e lidar com iframes aninhados automaticamente.

## Guia rápido

### Interagir com o primeiro iframe da página

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def interagir_iframe():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/page-with-iframe')

        iframe = await tab.find(tag_name='iframe', id='content-frame')

        # As chamadas abaixo já executam dentro do iframe
        title = await iframe.find(tag_name='h1')
        await title.click()

        form = await iframe.find(id='login-form')
        username = await form.find(name='username')
        await username.type_text('john_doe')

asyncio.run(interagir_iframe())
```

### Iframes aninhados

Basta encadear as buscas:

```python
outer = await tab.find(id='outer-frame')
inner = await outer.find(tag_name='iframe')  # procura dentro do primeiro iframe

submit_button = await inner.find(id='submit')
await submit_button.click()
```

O fluxo é sempre o mesmo:

1. Localize o iframe desejado.
2. Use esse `WebElement` como escopo das próximas buscas.
3. Repita para níveis mais profundos, se necessário.

### Executar JavaScript dentro do iframe

```python
iframe = await tab.find(tag_name='iframe')
result = await iframe.execute_script('return document.title', return_by_value=True)
print(result['result']['result']['value'])
```

O Pydoll garante que o script rode no contexto isolado do iframe, inclusive em frames cross-origin.

## Por que ficou melhor?

- **Intuitivo:** você programa exatamente o que vê na árvore DOM.
- **Sem dor de cabeça com CDP:** mundos isolados e targets são configurados automaticamente.
- **Suporte nativo a aninhamento:** cada busca é relativa ao elemento atual; hierarquias profundas continuam legíveis.
- **Uma única API:** não é preciso alternar entre métodos de `Tab` e de `WebElement`.

!!! tip "Aviso de descontinuação"
    `Tab.get_frame()` agora emite `DeprecationWarning` e será removido em uma versão futura. Atualize seus scripts para usar o iframe diretamente, como mostrado acima.

## Padrões comuns

### Capturar imagem de conteúdo dentro do iframe

```python
iframe = await tab.find(tag_name='iframe')
chart = await iframe.find(id='sales-chart')
await chart.take_screenshot('chart.png')
```

### Iterar sobre vários iframes

```python
iframes = await tab.find(tag_name='iframe', find_all=True)
for frame in iframes:
    heading = await frame.find(tag_name='h2')
    print(await heading.text)
```

### Aguardar até que um iframe esteja pronto

```python
iframe = await tab.find(tag_name='iframe')
await iframe.wait_until(is_visible=True, timeout=10)
banner = await iframe.find(id='promo-banner')
```

## Seletores que Cruzam IFrames

Em vez de localizar manualmente cada iframe e depois buscar dentro dele, você pode escrever um **único seletor** que cruza as fronteiras do iframe. O Pydoll detecta automaticamente os passos `iframe` no seu XPath ou CSS, divide em segmentos e percorre a cadeia de iframes por você.

### Seletores CSS

Use qualquer combinador padrão (`>`, espaço) após um composto `iframe`:

```python
# Cruzamento de um único iframe
button = await tab.query('iframe > .submit-btn')

# Com seletores de atributo no iframe
button = await tab.query('iframe[src*="checkout"] > #pay-button')

# Iframes aninhados
element = await tab.query('iframe.outer > iframe.inner > div.content')

# Múltiplos passos após o iframe
link = await tab.query('iframe > nav > a.home-link')

# Iframe dentro de outro elemento (não na raiz)
button = await tab.query('div > iframe > button.submit')
content = await tab.query('.wrapper iframe > div.content')
```

### Expressões XPath

Use `/` após um passo `iframe` — o Pydoll divide no nó do iframe:

```python
# Cruzamento de um único iframe
button = await tab.query('//iframe/body/button[@id="submit"]')

# Iframe dentro de outro elemento (não na raiz)
div = await tab.query('//div/iframe/div')
item = await tab.query('//div[@class="wrapper"]/iframe/body/div')

# Com predicados no iframe
heading = await tab.query('//iframe[@src*="cloudflare"]//h1')

# Iframes aninhados
element = await tab.query('//iframe[@id="outer"]//iframe[@id="inner"]//div')
```

### Como funciona

Quando o Pydoll encontra um seletor como `iframe[src*="checkout"] > form > button`:

1. **Analisa** o seletor em segmentos: `iframe[src*="checkout"]` e `form > button`
2. **Encontra** o elemento iframe usando o primeiro segmento
3. **Busca dentro** do iframe usando o segundo segmento
4. Para iframes aninhados, repete o processo em cada fronteira

Isso equivale à abordagem manual, mas em uma única chamada:

```python
# Manual (continua funcionando)
iframe = await tab.find(tag_name='iframe', src='*checkout*')
button = await iframe.query('form > button')

# Automático (mesmo resultado, uma linha)
button = await tab.query('iframe[src*="checkout"] > form > button')
```

### Quando a divisão NÃO acontece

Seletores só são divididos quando `iframe` aparece como **nome de tag**. Estes seletores passam inalterados:

- `.iframe > body` — seletor de classe, não de tag
- `#iframe > body` — seletor de ID
- `div.iframe > body` — tag é `div`, não `iframe`
- `[data-type="iframe"] > body` — seletor de atributo
- `iframe` ou `//iframe` — sem conteúdo após o iframe (nada para buscar dentro)

### Suporte a find_all

O último segmento respeita `find_all=True`, retornando todos os elementos correspondentes dentro do iframe final:

```python
# Obter todos os links dentro de um iframe
links = await tab.query('iframe > a', find_all=True)
```

## Boas práticas

- **Use o iframe como escopo:** prefira chamar `find`, `query` e derivados diretamente nele.
- **Evite `tab.find` para elementos internos:** ele só enxerga o documento principal.
- **Guarde referências úteis:** o contexto é cacheado pelo Pydoll.
- **Continue aplicando os mesmos fluxos:** rolagem, screenshots, waits, scripts, atributos e texto funcionam igual a qualquer outro elemento.

## Leituras recomendadas

- **[Busca de Elementos](../element-finding.md)** – explica buscas encadeadas e escopos.
- **[Capturas e PDFs](screenshots-and-pdfs.md)** – detalhes sobre captura de tela.
- **[Event System](../advanced/event-system.md)** – monitore eventos de forma reativa (inclusive de iframes).

Com o novo fluxo, iframes deixam de ser um caso especial: são apenas mais um nó na árvore DOM. Concentre-se na lógica da automação; o Pydoll cuida da parte difícil para você.
