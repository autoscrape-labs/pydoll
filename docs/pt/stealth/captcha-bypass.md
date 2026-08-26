# Cloudflare Turnstile

O Pydoll consegue clicar num checkbox do Cloudflare Turnstile para você, o mesmo clique que uma pessoa faz no widget. Ele não resolve desafios de imagem ou de quebra-cabeça, e se o clique é aceito ou não depende da reputação do seu IP e do seu fingerprint, não do Pydoll. Encare isto como automatizar o clique, não como derrotar o captcha.

<iframe scrolling="no" src="/docs/resources/visuals/captcha-turnstile.html" aria-label="Pydoll clicando num checkbox do Turnstile, com o resultado dependendo da reputação do IP" style="width: 100%; height: 345px; border: 0;" loading="lazy"></iframe>

## Lide com o Turnstile enquanto navega

O context manager espera o widget do Turnstile aparecer durante o bloqueio, clica no seu checkbox e deixa o seu código continuar assim que agiu. Coloque dentro do bloco a navegação que dispara o desafio.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://a-site-behind-turnstile.com')

        content = await tab.find(id='protected-content', timeout=10, raise_exc=False)
        print(await content.text if content else 'Still challenged.')

asyncio.run(main())
```

Substitua a URL pelo site que você está automatizando. Não existe uma página pública e estável do Turnstile para apontar.

## Lide com o Turnstile em segundo plano

Quando você não quer envolver uma navegação específica, ative o tratamento em segundo plano: o Pydoll clica no widget sempre que ele aparece, até você desativar.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_auto_solve_cloudflare_captcha()
        await tab.go_to('https://a-site-behind-turnstile.com')
        await asyncio.sleep(5)   # dá tempo para o widget aparecer e ser clicado

        await tab.disable_auto_solve_cloudflare_captcha()

asyncio.run(main())
```

## Como ele encontra o checkbox

O Pydoll detecta o Turnstile fazendo polling no shadow DOM da página em busca do widget do Cloudflare: ele procura o shadow root que hospeda `challenges.cloudflare.com`, entra no seu iframe cross-origin, encontra o shadow root interno e clica no checkbox assim que ele aparece. Você não configura um seletor, e não há delay de clique para ajustar.

## Dê tempo para o widget aparecer

Alguns sites renderizam o Turnstile depois do carregamento inicial. `time_to_wait_captcha` (padrão 5 segundos) é quanto tempo o Pydoll espera pelo widget antes de desistir. Aumente para um site lento.

```python
async with tab.expect_and_bypass_cloudflare_captcha(time_to_wait_captcha=15):
    await tab.go_to('https://a-site-behind-turnstile.com')
```

`time_to_wait_captcha` é o único parâmetro de tempo. Se o widget nunca aparecer dentro dessa janela, a interação é ignorada.

!!! note "Migrando de versões antigas"
    `custom_selector` e `time_before_click` ainda existem nesses métodos, mas estão deprecados e são ignorados. A detecção agora é automática, então remova-os do código antigo.

## O que determina se o clique é aceito

Clicar no checkbox é apenas parte disso. O Turnstile decide se aceita a partir de sinais que o Pydoll não controla:

- **Reputação do IP.** Um IP residencial ou móvel limpo costuma ser aceito; um IP de datacenter é frequentemente desafiado ou bloqueado. Nenhuma configuração de navegador supera um IP marcado. Veja [Proxies](../guides/proxies.md).
- **Consistência do fingerprint.** A identidade que o seu navegador apresenta tem que concordar consigo mesma e com o seu IP. Duas coisas fazem o Turnstile tropeçar com mais frequência:
    - **Uma incompatibilidade de versão do Chrome.** Com a [Injeção de fingerprint](fingerprint-injection.md), a versão anunciada pelo perfil tem que corresponder ao binário real (alinhe-a a `await browser.get_version()`), ou a página fica presa em "Just a moment...".
    - **Uma identidade que para na página.** O widget lê o fingerprint dentro do seu próprio iframe cross-origin, então o perfil precisa alcançar lá também. `apply_fingerprint()` faz isso por padrão (`cross_origin_iframes`), e combinar o locale, o fuso horário e a geolocalização do perfil com o IP de saída completa o quadro.
- **Headful vs headless.** O headless emite um sinal de display mais fraco que pode reduzir a pontuação de confiança, mas não é uma barreira. Com um fingerprint totalmente coerente (incluindo o iframe cross-origin) e um locale combinado com o IP, o headless passa pelo Turnstile num IP decente. Num IP marginal, prefira headful, ou headful sob um framebuffer virtual (Xvfb) num servidor, para que o sinal de display pare de pesar contra você. O aprofundamento sobre o [managed challenge do Cloudflare](../deep-dive/fingerprinting/cloudflare-challenge.md) traz o detalhamento completo.

Se o checkbox é clicado mas um desafio de quebra-cabeça ou de imagem aparece em seguida, a pontuação de confiança estava baixa demais. O Pydoll não consegue resolver esse desafio; melhore o IP e o fingerprint em vez disso.

<iframe scrolling="no" src="/docs/resources/visuals/turnstile-trust-score.html" aria-label="Reputação do IP, consistência do fingerprint e o modo do navegador alimentam uma pontuação de confiança que resulta em aceito, desafiado ou bloqueado; o clique que o Pydoll automatiza é apenas uma das entradas" style="width: 100%; height: 430px; border: 0;" loading="lazy"></iframe>

## O que ele não faz

- Ele não resolve desafios de seleção de imagem ou de quebra-cabeça.
- Ele não lida com reCAPTCHA nem hCaptcha. Esses não são suportados por este recurso.
- Ele não muda o seu IP nem o seu fingerprint. Combine-o com um bom proxy e um fingerprint consistente para que o clique surta efeito.

!!! warning "Respeite os termos do site"
    Automatizar um captcha pode violar os Termos de Serviço de um site. Use isto apenas onde você está autorizado a fazê-lo: testando suas próprias aplicações, monitorando serviços que você controla ou em pesquisa com permissão.

## O que vem a seguir

- [Passando despercebido](index.md): como o tratamento de captcha se encaixa com o resto das camadas de stealth.
- [Proxies](../guides/proxies.md): a reputação de IP que decide a maioria dos resultados do Turnstile.
- [Interações humanizadas](human-like-interactions.md): comportamento humanizado antes e ao redor do clique.
