# Passando despercebido

Quando um scraper é bloqueado, geralmente o código está correto; o problema são os sinais. Os sites leem três camadas: o que o seu navegador diz que é (User-Agent, marcadores de headless, fingerprint), como ele se comporta (cliques instantâneos, digitação perfeitamente regular) e como ele responde aos desafios (Cloudflare Turnstile). Esta página estabelece o mínimo para cada camada e aponta para os guias mais aprofundados.

Algumas das partes difíceis você já ganha de graça: como o Pydoll controla um Chrome real via CDP, os fingerprints de rede e de navegador são autênticos, e `navigator.webdriver` é `false` sem nenhum patch. O que segue é o que ainda cabe a você controlar.

**Você vai aprender**

- [Como manter a identidade do navegador consistente](#keep-the-identity-consistent)
- [Como interagir como uma pessoa](#interact-like-a-person)
- [Como lidar com o Cloudflare Turnstile](#handle-cloudflare-turnstile)

## Mantenha a identidade consistente {#keep-the-identity-consistent}

A identidade é a camada mais difícil, porque os sinais têm que concordar entre si e com o seu IP e sistema operacional. O User-Agent, os Client Hints, o idioma, o fuso horário, o renderer WebGL e as fontes são todos verificados de forma cruzada; sobrescrever um deles isoladamente costuma te deixar mais detectável, não menos. O Pydoll já mantém parte disso consistente para você (ele ajusta o User-Agent e os Client Hints juntos quando você define `--user-agent=`) e aplica uma identidade completa e coerente através de `apply_fingerprint()`.

Comece por [Técnicas de evasão](evasion-techniques.md) para as alavancas que você controla (User-Agent, idioma, WebRTC, perfil realista) e por [Injeção de fingerprint](fingerprint-injection.md) para aplicar uma identidade completa a partir de um único perfil.

## Interaja como uma pessoa {#interact-like-a-person}

Cliques instantâneos no centro exato de um elemento e teclas digitadas a cada 50ms são fingerprints comportamentais. Passe `humanize=True` e o Pydoll move o cursor por um caminho curvo, com um tempo humano, antes de clicar, e digita com ritmo variável e erros de digitação ocasionais que são corrigidos:

```python
search_box = await tab.find(id='search')
await search_box.type_text('browser automation', humanize=True)

submit = await tab.find(tag_name='button', type='submit')
await submit.click(humanize=True)
```

A humanização é opcional por interação, então você a mantém onde o comportamento é observado e a dispensa onde a velocidade importa. [Interações humanizadas](human-like-interactions.md) explica o modelo de tempo e como ajustá-lo.

## Lide com o Cloudflare Turnstile {#handle-cloudflare-turnstile}

Quando uma página protegida exibe o checkbox do Turnstile, o Pydoll consegue detectá-lo e clicar nele para você:

```python
async with tab.expect_and_bypass_cloudflare_captcha():
    await tab.go_to('https://site-protected-by-cloudflare.com')

print('Challenge handled, page loaded.')
```

Clicar no widget é apenas parte disso: se o Cloudflare aceita ou não o clique também depende da reputação do seu IP e de quão consistente o resto do seu navegador parece. Se os desafios continuarem falhando, siga por [Bypass de captcha](captcha-bypass.md) e considere [um proxy residencial](../guides/proxies.md).

## O que vem a seguir

- [Técnicas de evasão](evasion-techniques.md): o modelo de detecção completo e as alavancas que você controla.
- [Interações humanizadas](human-like-interactions.md): o modelo de tempo por trás de `humanize=True`.
- [Bypass de captcha](captcha-bypass.md): o tratamento do Cloudflare Turnstile em profundidade.
- [Injeção de fingerprint](fingerprint-injection.md): aplique uma identidade coerente em todas as camadas.
