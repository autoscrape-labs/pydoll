# Interações humanizadas

Os sistemas de detecção observam *como* você age, não só no que você clica. Cliques instantâneos no centro exato de um elemento, teclas digitadas a uma taxa perfeitamente fixa e saltos do cursor em linhas retas são todos indícios comportamentais. Passe `humanize=True` e o Pydoll executa a mesma ação com o tempo e o movimento de uma pessoa: ritmo de digitação variável, caminhos curvos do cursor e rolagem baseada em física.

A humanização é opcional por interação, então você gasta os milissegundos extras apenas onde o comportamento é observado, e ela é uma camada de stealth, não todas elas. Ela molda o comportamento; não muda a sua [identidade ou fingerprint de rede](index.md).

## Digite como um humano

Passe `humanize=True` para `type_text()` e o Pydoll varia o intervalo entre as teclas e adiciona erros de digitação ocasionais que são corrigidos (cerca de 2%). Sem isso, a digitação corre a uma taxa fixa de 50ms por caractere.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com/login')

        username = await tab.find(id='username')
        await username.type_text('tester', humanize=True)

        password = await tab.find(id='password')
        await password.type_text('secret-passphrase', humanize=True)

asyncio.run(main())
```

Quando o conteúdo de um campo não precisa parecer digitado (um token oculto, um valor que ninguém observa), `insert_text()` define a string inteira de uma vez, sem eventos por tecla.

<iframe src="/docs/resources/visuals/typing-rhythm.html" aria-label="A mesma palavra digitada numa cadência fixa de 50ms versus um ritmo humanizado com intervalos variáveis e um erro de digitação corrigido, no mesmo eixo de tempo" style="width: 100%; height: 340px; border: 0;" loading="lazy"></iframe>

## Clique como um humano

`humanize=True` no `click()` move o cursor até o elemento por um caminho curvo, com tempo humano, antes de pressionar. Você também pode deslocar o clique para fora do centro exato com `x_offset`/`y_offset`, e variar quanto tempo o botão fica pressionado com `hold_time`.

```python
button = await tab.find(id='submit')

# aproximação curva, tempo de pressão humano
await button.click(humanize=True)

# cai um pouco fora do centro, segura um instante a mais
await button.click(x_offset=6, y_offset=-3, hold_time=0.12)
```

`click()` despacha eventos de mouse reais (move, down, up, click), que é o que uma página vê de um usuário real. `click_using_js()` chama o `click()` JavaScript do elemento: funciona em elementos ocultos ou cobertos e é mais rápido, mas não dispara nenhum dos eventos de mouse, então prefira `click()` onde o comportamento é observado e reserve `click_using_js()` para controles ocultos ou etapas críticas em velocidade.

## Mova o mouse como um humano

Para coordenadas puras em vez de um elemento, controle `tab.mouse` com `humanize=True`. O cursor segue um caminho de Bezier com uma duração da Lei de Fitts (mais longa para alvos mais distantes e menores), um perfil de velocidade em forma de sino, um pequeno tremor e um overshoot ocasional que se corrige de volta.

```python
await tab.mouse.move(480, 260, humanize=True)
await tab.mouse.click(480, 260, humanize=True)
await tab.mouse.drag(120, 200, 480, 360, humanize=True)
```

Veja [Mouse](../guides/mouse.md) para a API completa de coordenadas e [Teclado](../guides/keyboard.md) para pressionamentos de teclas e atalhos.

## Role a página como um humano

Usuários reais não se teletransportam para baixo numa página. `tab.scroll` oferece três modos; `humanize=True` roda um modelo de física com momento, atrito, micro-pausas e overshoot, e espera pelo evento `scrollend` do navegador antes de retornar, de modo que a próxima ação só roda depois que a rolagem termina.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://news.ycombinator.com')

        await tab.scroll.by(ScrollPosition.DOWN, 600, humanize=True)
        await tab.scroll.to_bottom(humanize=True)
        await tab.scroll.to_top(humanize=True)

asyncio.run(main())
```

Sem `humanize`, `smooth=True` (o padrão) faz uma animação CSS previsível, e `smooth=False` salta instantaneamente. Para trazer um elemento para a área visível antes de um screenshot, use `await element.scroll_into_view()`.

## Ajuste o tempo

A física humanizada do mouse vem de um `MouseTimingConfig` em `tab.mouse.timing`: as constantes da Lei de Fitts, a curvatura do caminho, o tremor, o overshoot e os limites de duração. Sobrescreva apenas os campos que te interessam. O [guia do Mouse](../guides/mouse.md#tune-the-timing) mostra a config com cada campo explicado.

## O que a humanização não cobre

O comportamento humanizado trata uma camada de detecção. Um site ainda pode te sinalizar pela identidade do seu navegador (User-Agent, WebGL, canvas) ou pelo seu caminho de rede (reputação do IP, TLS), não importa quão natural o seu cursor pareça. Encare esta página como a peça comportamental e combine-a com o resto:

!!! note "Uma camada entre várias"
    O comportamento humanizado não torna a automação indetectável por si só. Combine-o com uma identidade consistente e um IP limpo. Veja a [visão geral de stealth](index.md) para entender como as camadas se encaixam.

## O que vem a seguir

- [Bypass de captcha](captcha-bypass.md): lide com o Cloudflare Turnstile quando ele aparecer.
- [Visão geral de stealth](index.md): o quadro completo, do comportamento à identidade e à rede.
- [Teclado](../guides/keyboard.md) e [Mouse](../guides/mouse.md): as APIs completas de input.
- [Fingerprinting comportamental](../deep-dive/fingerprinting/behavioral-fingerprinting.md): como o mouse, o teclado e o tempo são analisados.
