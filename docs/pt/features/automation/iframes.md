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
