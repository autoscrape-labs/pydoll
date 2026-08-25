# Teclado

Controle a entrada de teclado através de `tab.keyboard`: digite em campos, pressione teclas especiais como Enter e Tab, e execute atalhos como Ctrl+A. Use quando um formulário precisa de navegação por teclado ou uma aplicação web responde a combinações de teclas que um clique não consegue acionar.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://www.wikipedia.org')

        search = await tab.find(id='searchInput')
        await search.type_text('web scraping', humanize=True)

        await tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(2)
        print(await tab.current_url)

asyncio.run(main())
```

## Digitar em um campo

Para digitar caractere por caractere no elemento em foco, use `type_text` no elemento. Passe `humanize=True` para um tempo variável com um ou outro erro de digitação corrigido; deixe desligado para um ritmo fixo e mais rápido.

```python
field = await tab.find(id='searchInput')
await field.type_text('search query', humanize=True)
```

Digite seu próprio texto abaixo e execute das duas formas. Com `humanize=True` o ritmo varia e um ou outro erro de digitação é corrigido, então cada execução é diferente; sem ele, cada intervalo é fixo em 50ms.

<iframe scrolling="no" src="/docs/resources/visuals/keyboard-humanize.html" aria-label="Interactive humanized typing: type text and watch it typed with human rhythm and corrected typos" style="width: 100%; height: 350px; border: 0;" loading="lazy"></iframe>

Se você só precisa que o texto apareça e não se importa com eventos por tecla, `insert_text` cola a string inteira de uma vez:

```python
await field.insert_text('search query')   # instantâneo, sem eventos de tecla
```

!!! note "`tab.keyboard` digita onde o foco já estiver"
    `type_text` e `insert_text` em um elemento colocam o foco nesse elemento para você, então o texto vai parar no lugar certo. Os métodos de nível mais baixo do `tab.keyboard` (abaixo) não fazem isso: eles enviam as teclas para o que quer que a página tenha em foco no momento. Coloque o foco no campo primeiro (clicar nele o foca) antes de digitar através do `tab.keyboard`.

## Pressionar uma tecla

O `press()` executa um pressionamento completo de tecla (baixa, breve espera, sobe). Use para teclas que acionam comportamento em vez de texto: Enter para enviar, Tab para mover entre campos, Escape para dispensar.

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.press(Key.ESCAPE)

# teclas de seta e navegação
await tab.keyboard.press(Key.ARROWDOWN)
await tab.keyboard.press(Key.END)
```

`press(key, interval=0.1)` mantém a tecla pressionada por `interval` segundos antes de soltar; aumente para simular um pressionamento mais longo.

## Executar um atalho de teclado

O `hotkey()` pressiona uma combinação e a solta na ordem certa, então você não calcula bitmasks de modificadores por conta própria. Passe o modificador primeiro.

```python
from pydoll.constants import Key

await tab.keyboard.hotkey(Key.CONTROL, Key.A)   # seleciona tudo
await tab.keyboard.hotkey(Key.CONTROL, Key.C)   # copia
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWLEFT)  # seleciona a palavra à esquerda
```

O macOS usa Command (Meta) onde Windows e Linux usam Control, então escolha o modificador conforme a plataforma:

```python
import sys
from pydoll.constants import Key

mod = Key.META if sys.platform == 'darwin' else Key.CONTROL
await tab.keyboard.hotkey(mod, Key.C)
```

## Aplicar um modificador a uma única tecla

`press()` e `down()` recebem um argumento `modifiers` do enum `KeyModifier`:

```python
from pydoll.protocol.input.types import KeyModifier

await tab.keyboard.press(Key.S, modifiers=KeyModifier.CTRL)   # Ctrl+S
```

Os membros são `KeyModifier.ALT`, `.CTRL`, `.META` e `.SHIFT`. O `hotkey()` já aplica os modificadores para você, então recorra a `modifiers` apenas quando você pressiona ou segura uma única tecla manualmente.

## Segurar e soltar teclas

Para sequências em que um modificador permanece pressionado ao longo de vários toques, controle `down()` e `up()` você mesmo. Solte em um bloco `finally` para que um erro no meio da sequência não deixe uma tecla travada.

```python
from pydoll.constants import Key

try:
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWRIGHT)   # estende a seleção
    await tab.keyboard.press(Key.ARROWRIGHT)
finally:
    await tab.keyboard.up(Key.SHIFT)
```

## Atalhos da UI do navegador não funcionam

Teclas enviadas pelo DevTools Protocol são marcadas como não confiáveis, então nunca acionam a própria UI do Chrome. Atalhos que abrem abas, o DevTools ou a barra de endereços ficam inertes. Atalhos em nível de página dentro do documento funcionam normalmente.

!!! warning "Use comandos do navegador, não atalhos da UI"
    Ctrl+T, Ctrl+W, F12 e Ctrl+L não farão nada. Controle o navegador pela API dele: `await browser.new_tab()`, `await tab.close()`, `await tab.go_to(url)`, `await tab.refresh()`. Atalhos que agem no conteúdo da página (Ctrl+A, Ctrl+C, Tab, Enter, teclas de seta) funcionam como esperado.

## Referência de teclas

O `Key` (`from pydoll.constants import Key`) cobre o teclado inteiro:

| Categoria | Membros |
|----------|---------|
| Letras | `Key.A` até `Key.Z` |
| Números | `Key.DIGIT0` a `Key.DIGIT9`, `Key.NUMPAD0` a `Key.NUMPAD9` |
| Função | `Key.F1` até `Key.F12` |
| Navegação | `ARROWUP`, `ARROWDOWN`, `ARROWLEFT`, `ARROWRIGHT`, `HOME`, `END`, `PAGEUP`, `PAGEDOWN` |
| Modificadores | `CONTROL`, `SHIFT`, `ALT`, `META` |
| Edição | `ENTER`, `TAB`, `SPACE`, `BACKSPACE`, `DELETE`, `ESCAPE`, `INSERT` |

## Próximos passos

- [Mouse](mouse.md): cliques, movimento e arrasto com tempo humanizado.
- [Encontrar elementos](element-finding.md): localize os campos em que você digita.
- [Interações humanizadas](../stealth/human-like-interactions.md): o que `humanize=True` faz internamente.
