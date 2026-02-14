# Controle do Mouse

A API de Mouse fornece controle completo sobre a entrada do mouse no nível da página, permitindo simular movimentos realistas do cursor, cliques, cliques duplos e operações de arrastar. Por padrão, todas as operações do mouse usam simulação humanizada: as trajetórias seguem curvas de Bezier naturais com temporização pela Lei de Fitts, perfis de velocidade minimum-jerk, tremor fisiológico e correção de overshoot, tornando a automação virtualmente indistinguível do comportamento humano.

!!! info "Interface Centralizada de Mouse"
    Todas as operações do mouse são acessíveis via `tab.mouse`, fornecendo uma API limpa e unificada para todas as interações com o mouse.

## Início Rápido

```python
from pydoll.browser.chromium import Chrome
from pydoll.protocol.input.types import MouseButton

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')

    # Mover cursor para posição (humanizado por padrão)
    await tab.mouse.move(500, 300)

    # Clicar na posição (humanizado por padrão)
    await tab.mouse.click(500, 300)

    # Clique direito
    await tab.mouse.click(500, 300, button=MouseButton.RIGHT)

    # Clique duplo
    await tab.mouse.double_click(500, 300)

    # Arrastar de uma posição para outra
    await tab.mouse.drag(100, 200, 500, 400)
```

## Métodos Principais

### move: Mover Cursor

Move o cursor do mouse para uma posição específica na página:

```python
# Movimento humanizado (padrão, trajetória curva com temporização natural)
await tab.mouse.move(500, 300)

# Movimento instantâneo (único evento CDP, sem simulação)
await tab.mouse.move(500, 300, humanize=False)
```

**Parâmetros:**

- `x`: Coordenada X de destino (pixels CSS)
- `y`: Coordenada Y de destino (pixels CSS)
- `humanize` (keyword-only): Simular movimento curvo semelhante ao humano (padrão: `True`)

### click: Clicar na Posição

Move para a posição e realiza um clique do mouse:

```python
from pydoll.protocol.input.types import MouseButton

# Clique esquerdo com movimento humanizado (padrão)
await tab.mouse.click(500, 300)

# Clique direito
await tab.mouse.click(500, 300, button=MouseButton.RIGHT)

# Clique duplo via click_count
await tab.mouse.click(500, 300, click_count=2)

# Clique instantâneo sem humanização
await tab.mouse.click(500, 300, humanize=False)
```

**Parâmetros:**

- `x`: Coordenada X de destino
- `y`: Coordenada Y de destino
- `button` (keyword-only): Botão do mouse, sendo `LEFT`, `RIGHT` ou `MIDDLE` (padrão: `LEFT`)
- `click_count` (keyword-only): Número de cliques (padrão: `1`)
- `humanize` (keyword-only): Simular comportamento semelhante ao humano (padrão: `True`)

### double_click: Clique Duplo na Posição

Método de conveniência equivalente a `click(x, y, click_count=2)`:

```python
await tab.mouse.double_click(500, 300)
await tab.mouse.double_click(500, 300, humanize=False)
```

### down / up: Controle de Botão de Baixo Nível

Pressionar ou soltar botões do mouse independentemente:

```python
# Pressionar botão esquerdo na posição atual
await tab.mouse.down()

# Soltar botão esquerdo
await tab.mouse.up()

# Botão direito
await tab.mouse.down(button=MouseButton.RIGHT)
await tab.mouse.up(button=MouseButton.RIGHT)
```

Esses são primitivos que operam na posição atual do cursor e não possuem parâmetro `humanize`.

### drag: Arrastar e Soltar

Move do ponto inicial ao final mantendo o botão do mouse pressionado:

```python
# Arrastar humanizado (padrão)
await tab.mouse.drag(100, 200, 500, 400)

# Arrastar instantâneo sem humanização
await tab.mouse.drag(100, 200, 500, 400, humanize=False)
```

**Parâmetros:**

- `start_x`, `start_y`: Coordenadas iniciais
- `end_x`, `end_y`: Coordenadas finais
- `humanize` (keyword-only): Simular arrasto semelhante ao humano (padrão: `True`)

## Desabilitando a Humanização

Todos os métodos do mouse usam `humanize=True` por padrão. Para realizar operações instantâneas sem humanização, passe `humanize=False`:

```python
# Movimento instantâneo, único evento CDP mouseMoved
await tab.mouse.move(500, 300, humanize=False)

# Clique instantâneo: move + press + release, sem simulação
await tab.mouse.click(500, 300, humanize=False)

# Arrasto instantâneo, sem curvas, sem pausas
await tab.mouse.drag(100, 200, 500, 400, humanize=False)
```

Isso é útil quando a velocidade é crítica e a evasão de detecção não é uma preocupação, por exemplo em ambientes de teste ou ferramentas internas.

## Modo Humanizado

Quando `humanize=True` (o padrão), o módulo de mouse aplica múltiplas camadas de realismo:

### Trajetórias com Curvas de Bezier

O mouse segue uma trajetória curva natural em vez de uma linha reta. Os pontos de controle são deslocados aleatoriamente perpendiculares à linha início→fim, com posicionamento assimétrico (mais curvatura no início do movimento, como um alcance balístico real).

### Temporização pela Lei de Fitts

A duração do movimento segue a Lei de Fitts: `MT = a + b × log₂(D/W + 1)`. Distâncias maiores levam proporcionalmente mais tempo, correspondendo ao comportamento de controle motor humano.

### Perfil de Velocidade Minimum-Jerk

O cursor segue um perfil de velocidade em forma de sino, iniciando lento, acelerando até a velocidade máxima no meio e depois desacelerando no final. Isso corresponde à trajetória de movimento humano mais suave possível.

### Tremor Fisiológico

Ruído gaussiano pequeno (σ ≈ 1px) é adicionado a cada quadro, simulando tremor da mão. A amplitude do tremor escala inversamente com a velocidade, com mais tremor quando o cursor está lento ou parado e menos durante movimentos balísticos rápidos.

### Overshoot e Correção

Para movimentos rápidos de longa distância (~70% de probabilidade), o cursor ultrapassa o alvo em 3–12% da distância, depois faz um pequeno sub-movimento corretivo de volta ao alvo. Isso corresponde a dados reais de controle motor humano.

### Pausa Pré-Clique

Cliques humanizados incluem uma pausa pré-clique (50–200ms) que simula o tempo natural de estabilização antes de pressionar o botão.

## Cliques Humanizados Automáticos em Elementos

Quando você usa `element.click()`, a API do Mouse é utilizada automaticamente para produzir um movimento realista com curva de Bezier da posição atual do cursor até o centro do elemento antes de clicar. Isso significa que cada chamada `element.click()` gera movimento natural do mouse, tornando cliques em elementos indistinguíveis do comportamento humano.

```python
# Clique humanizado (padrão): movimento com curva de Bezier + clique
button = await tab.find(id='submit')
await button.click()

# Com deslocamento do centro
await button.click(x_offset=10, y_offset=5)

# Desabilitar humanização: press/release CDP bruto, sem movimento do cursor
await button.click(humanize=False)
```

O rastreamento de posição é mantido entre cliques em elementos. Clicar no elemento A, depois no elemento B, produz um caminho curvo natural de A até B.

## Configuração Personalizada de Temporização

Todos os parâmetros de humanização são configuráveis via `MouseTimingConfig`:

```python
from pydoll.interactions.mouse import MouseTimingConfig

config = MouseTimingConfig(
    fitts_a=0.070,              # Intercepto da Lei de Fitts (segundos)
    fitts_b=0.150,              # Inclinação da Lei de Fitts (segundos/bit)
    frame_interval=0.012,       # Intervalo base entre eventos mouseMoved
    curvature_min=0.10,         # Curvatura mínima como fração da distância
    curvature_max=0.30,         # Curvatura máxima
    tremor_amplitude=1.0,       # Sigma do tremor em pixels
    overshoot_probability=0.70, # Chance de overshoot em movimentos rápidos
    min_duration=0.08,          # Duração mínima do movimento
    max_duration=2.5,           # Duração máxima do movimento
)

# Aplicar à instância de mouse do tab
tab.mouse.timing = config
```

Veja o dataclass `MouseTimingConfig` para todos os parâmetros disponíveis.

## Rastreamento de Posição

A API de Mouse rastreia a posição do cursor entre operações:

```python
# Posição inicial é (0, 0)
await tab.mouse.move(100, 200)
# Posição agora é (100, 200)

await tab.mouse.click(300, 400)
# Posição agora é (300, 400)

# Métodos de baixo nível usam a posição rastreada
await tab.mouse.down()   # Pressiona em (300, 400)
await tab.mouse.up()     # Solta em (300, 400)
```

!!! note "Estado da Posição"
    A posição do mouse é rastreada internamente. `WebElement.click()` utiliza automaticamente `tab.mouse` quando disponível, então o rastreamento de posição é mantido entre cliques em elementos.

## Modo Debug

Ative o modo debug para visualizar o movimento do mouse na página. Quando ativo, pontos coloridos são desenhados em um canvas de sobreposição transparente:

- **Pontos azuis**: trajetória do cursor durante o movimento
- **Pontos vermelhos**: posições de clique

```python
# Ativar em tempo de execução via propriedade
tab.mouse.debug = True

# Agora todos os movimentos desenham pontos coloridos
await tab.mouse.click(500, 300)

# Desativar quando terminar
tab.mouse.debug = False
```

Isso é útil para ajustar parâmetros de temporização e verificar que as trajetórias parecem naturais.

## Exemplos Práticos

### Clicar em um Botão com Movimento Realista

```python
async def click_button_naturally(tab):
    # element.click() usa automaticamente tab.mouse para movimento humanizado
    button = await tab.find(id='submit')
    await button.click()
```

### Arrastar um Slider

```python
async def drag_slider(tab):
    slider = await tab.find(css_selector='.slider-handle')
    bounds = await slider.get_bounds_using_js()

    start_x = bounds['x'] + bounds['width'] / 2
    start_y = bounds['y'] + bounds['height'] / 2
    end_x = start_x + 200  # Arrastar 200px para a direita

    await tab.mouse.drag(start_x, start_y, end_x, start_y)
```

### Passar o Mouse Sobre Elementos

```python
async def hover_menu(tab):
    menu = await tab.find(css_selector='.dropdown-trigger')
    bounds = await menu.get_bounds_using_js()

    await tab.mouse.move(
        bounds['x'] + bounds['width'] / 2,
        bounds['y'] + bounds['height'] / 2,
    )
    # O menu agora deve estar visível via CSS :hover
```

## Aprenda Mais

- **[Interações Humanas](human-interactions.md)**: Visão geral de todas as interações humanizadas
- **[Controle de Teclado](keyboard-control.md)**: Simulação realista de teclado
