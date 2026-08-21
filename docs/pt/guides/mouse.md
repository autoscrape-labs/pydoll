# Mouse

O Pydoll controla o mouse de duas formas: através de um elemento que você encontrou, que é o que você quer na maior parte do tempo, ou em coordenadas brutas da página quando você precisa de posições precisas. Ambas suportam `humanize=True`, que move o cursor por um caminho curvo, com tempo humano, em vez de teleportar para o alvo.

<iframe src="/docs/resources/visuals/mouse-humanize.html" aria-label="Humanized curved cursor path versus an instant robotic jump" style="width: 100%; height: 345px; border: 0;" loading="lazy"></iframe>

## Clicar em um elemento

O caso comum é clicar em um elemento que você já localizou com `find()` ou `query()`. Chame `click()` nele; você não calcula coordenadas, e o elemento é rolado para a área visível primeiro.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/add_remove_elements/')

        add_button = await tab.find(text='Add Element')
        await add_button.click()

        # o clique adicionou um botão Delete
        delete = await tab.find(class_name='added-manually')
        print('Added:', await delete.text)

asyncio.run(main())
```

O `click()` recebe algumas opções:

```python
# clica em um ponto deslocado do centro do elemento (pixels)
await element.click(x_offset=10, y_offset=5)

# mantém o botão pressionado por mais tempo antes de soltar (segundos)
await element.click(hold_time=0.3)

# humanizado: caminho curvo do cursor até o elemento, depois clique
await element.click(humanize=True)
```

!!! note "Clique em elemento vs coordenadas brutas"
    Prefira `element.click()`. Ele encontra a posição do elemento para você e sobrevive a mudanças de layout. Recorra à API de coordenadas abaixo apenas quando não há elemento a mirar, como clicar dentro de um `<canvas>` ou arrastar um controle por pixel.

## A API de mouse por coordenadas

`tab.mouse` clica, move e arrasta em coordenadas explícitas em pixels CSS, medidas a partir do canto superior esquerdo da página. Você geralmente obtém essas coordenadas a partir dos limites de um elemento (veja [Arrastar um slider](#drag-a-slider)).

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.protocol.input.types import MouseButton


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/')

        await tab.mouse.move(500, 300)                        # move o cursor
        await tab.mouse.click(500, 300)                       # clique esquerdo
        await tab.mouse.click(500, 300, button=MouseButton.RIGHT)  # clique direito
        await tab.mouse.double_click(500, 300)               # clique duplo
        await tab.mouse.drag(100, 200, 500, 400)             # pressiona, move, solta

asyncio.run(main())
```

O `MouseButton` (de `pydoll.protocol.input.types`) tem `LEFT`, `MIDDLE` e `RIGHT`. O `click()` também recebe `click_count` (passe `2` para um clique duplo) e todo método recebe o `humanize` (apenas por palavra-chave).

Para pressionar e soltar separadamente, `down()` e `up()` operam na posição atual do cursor:

```python
await tab.mouse.move(300, 400)
await tab.mouse.down(button=MouseButton.LEFT)
await tab.mouse.move(600, 400)     # arraste manualmente
await tab.mouse.up(button=MouseButton.LEFT)
```

O `tab.mouse` rastreia a posição do cursor entre chamadas, então `down()`/`up()` agem onde quer que o último `move()` ou `click()` tenha deixado.

## Mover como um humano

Por padrão, um movimento ou clique salta direto para o alvo, o que é um indício comportamental. Passe `humanize=True` e o Pydoll move o cursor por um caminho curvo com tempo humano (uma duração baseada na Lei de Fitts, um perfil de velocidade em forma de sino, um pequeno tremor, e ocasional ultrapassagem com correção):

```python
await tab.mouse.move(500, 300, humanize=True)
await tab.mouse.click(500, 300, humanize=True)
await tab.mouse.drag(100, 200, 500, 400, humanize=True)
```

> 🎞️ **Placeholder de GIF** — o cursor traçando um caminho humanizado curvo e desacelerando com uma pequena ultrapassagem, ao lado de um salto em linha reta para contraste.

Cliques humanizados em elementos funcionam da mesma forma. Como a posição é rastreada, clicar no elemento A e depois no elemento B traça uma curva natural de um para o outro:

```python
# instantâneo: o cursor salta direto para cada alvo
await (await tab.find(id='first')).click()
await (await tab.find(id='second')).click()

# humanizado: o cursor curva naturalmente de um alvo para o próximo
await (await tab.find(id='first')).click(humanize=True)
await (await tab.find(id='second')).click(humanize=True)
```

Veja [Interações humanizadas](../stealth/human-like-interactions.md) para o modelo completo de tempo e quando a humanização importa.

### Ajustar o tempo {#tune-the-timing}

A física humanizada é configurável através de `MouseTimingConfig`. Atribua uma nova config a `tab.mouse.timing`:

```python
from pydoll.interactions.mouse import MouseTimingConfig

tab.mouse.timing = MouseTimingConfig(
    fitts_a=0.070,               # tempo base de movimento (segundos)
    fitts_b=0.150,               # tempo adicionado por bit de dificuldade
    curvature_min=0.10,          # menor curvatura do caminho (fração da distância)
    curvature_max=0.30,          # maior curvatura do caminho
    tremor_amplitude=1.0,        # sigma do tremor da mão em pixels
    overshoot_probability=0.70,  # chance de ultrapassagem em movimentos rápidos e longos
    max_duration=2.5,            # limite para um único movimento (segundos)
)
```

Todo campo tem um valor padrão, então sobrescreva apenas o que precisar. Veja a dataclass `MouseTimingConfig` em `pydoll/interactions/mouse.py` para a lista completa.

## Observar o cursor durante o ajuste

Defina `tab.mouse.debug = True` e o Pydoll desenha o caminho do cursor sobre uma sobreposição transparente: pontos azuis traçam o movimento, pontos vermelhos marcam os cliques. Use para verificar se os caminhos humanizados parecem naturais, depois desligue.

```python
tab.mouse.debug = True
await tab.mouse.click(500, 300, humanize=True)
tab.mouse.debug = False
```

## Exemplos práticos

### Arrastar um slider {#drag-a-slider}

Leia a posição do controle a partir dos seus limites, depois arraste de lá:

```python
slider = await tab.query('.slider-handle')
bounds = await slider.get_bounds_using_js()   # {'x', 'y', 'width', 'height'}, pixels do viewport

start_x = bounds['x'] + bounds['width'] / 2
start_y = bounds['y'] + bounds['height'] / 2

await tab.mouse.drag(start_x, start_y, start_x + 200, start_y, humanize=True)
```

> 🎞️ **Placeholder de GIF** — o controle do slider sendo arrastado 200px para a direita ao longo de um caminho humanizado.

### Passar o cursor sobre um menu

Mova o cursor até um elemento para acionar seu estado CSS `:hover`, sem clicar:

```python
trigger = await tab.query('.dropdown-trigger')
bounds = await trigger.get_bounds_using_js()

await tab.mouse.move(
    bounds['x'] + bounds['width'] / 2,
    bounds['y'] + bounds['height'] / 2,
    humanize=True,
)
```

> 🎞️ **Placeholder de GIF** — o cursor se movendo até o gatilho do menu e seu dropdown se expandindo ao passar o cursor.

## Próximos passos

- [Teclado](keyboard.md): digite texto e pressione teclas, com o mesmo tempo humanizado.
- [Interações humanizadas](../stealth/human-like-interactions.md): o modelo de tempo por trás de `humanize=True` e quando usá-lo.
- [Encontrar elementos](element-finding.md): localize os elementos que você clica e arrasta.
