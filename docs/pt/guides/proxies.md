# Proxies

Roteie o tráfego do navegador por um proxy para mudar seu IP de saída, distribuir requisições entre endereços ou alcançar um site de outra região. Você define um proxy com um argumento de inicialização, e o Pydoll cuida da autenticação do proxy para você.

<iframe src="/docs/resources/visuals/proxy-routing.html" aria-label="Uma requisição roteada direta versus através de um proxy, mudando o IP que o alvo enxerga" style="width: 100%; height: 300px; border: 0;" loading="lazy"></iframe>

## Definir um proxy

Passe `--proxy-server` para `ChromiumOptions` e toda requisição que o navegador faz passa por ele. URLs HTTP, HTTPS e SOCKS5 funcionam:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.add_argument('--proxy-server=http://proxy.example.com:8080')

    async with Chrome(options=options) as browser:
        tab = await browser.start()

        response = await tab.request.get('https://httpbin.org/ip')
        print(response.json())   # {'origin': '<o IP do proxy>'}

asyncio.run(main())
```

`tab.request.get` roda no contexto do navegador, então passa pelo mesmo proxy que a página. Veja [Requisições HTTP](http-requests.md).

## Usar um proxy autenticado

A maioria dos proxies pagos exige usuário e senha. Coloque as credenciais na URL do proxy e o Pydoll responde ao desafio de autenticação para você, então a navegação funciona:

```python
options = ChromiumOptions()
options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')
```

Você não escreve nenhum código de autenticação. Nos bastidores, o Pydoll ativa o domínio Fetch do Chrome no nível do navegador; quando o proxy retorna um desafio 407, o Chrome pausa a requisição e o Pydoll responde com as credenciais da sua URL. O handler equivalente construído sobre a API pública fica assim:

```python
from pydoll.protocol.fetch.types import AuthChallengeResponseType


async def on_auth_required(event):
    await tab.continue_with_auth(
        request_id=event['params']['requestId'],
        auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
        proxy_username='user',
        proxy_password='pass',
    )
```

!!! warning "Autenticação SOCKS5 não é suportada pelo Chrome"
    O Chrome ignora credenciais em uma URL `socks5://user:pass@host:port` ([Chromium issue 40323993](https://issues.chromium.org/issues/40323993)): ele nunca as envia e nunca emite o desafio 407 que o Pydoll responderia. Rode um forwarder SOCKS5 local sem autenticação que trata as credenciais para você, e aponte o Chrome para ele:

    ```python
    import asyncio

    from pydoll.utils import SOCKS5Forwarder
    from pydoll.browser.chromium import Chrome
    from pydoll.browser.options import ChromiumOptions


    async def main():
        forwarder = SOCKS5Forwarder(
            remote_host='proxy.example.com',
            remote_port=1080,
            username='myuser',
            password='mypass',
            local_port=1081,
        )
        async with forwarder:
            options = ChromiumOptions()
            options.add_argument('--proxy-server=socks5://127.0.0.1:1081')

            async with Chrome(options=options) as browser:
                tab = await browser.start()
                await tab.go_to('https://httpbin.org/ip')

    asyncio.run(main())
    ```

    O Chrome conecta em `127.0.0.1` sem autenticação; o forwarder faz o handshake de usuário/senha com o proxy remoto.

## Usar um proxy diferente por contexto

Um [contexto de navegador](browser-contexts.md) pode carregar seu próprio proxy, então uma execução de navegador pode enviar abas diferentes por proxies diferentes. Passe `proxy_server` ao criar o contexto:

```python
async with Chrome() as browser:
    await browser.start()

    us_ctx = await browser.create_browser_context(proxy_server='http://user:pass@us.proxy.com:8080')
    de_ctx = await browser.create_browser_context(proxy_server='http://user:pass@de.proxy.com:8080')

    us_tab = await browser.new_tab(browser_context_id=us_ctx)
    de_tab = await browser.new_tab(browser_context_id=de_ctx)

    print((await us_tab.request.get('https://httpbin.org/ip')).json())
    print((await de_tab.request.get('https://httpbin.org/ip')).json())
```

## Pular o proxy para alguns hosts

Use `--proxy-bypass-list` para enviar certos hosts direto, o que é útil para servidores de desenvolvimento local e recursos internos:

```python
options.add_argument('--proxy-server=http://proxy.example.com:8080')
options.add_argument('--proxy-bypass-list=localhost,127.0.0.1,*.local')
```

## Verificar seu IP de saída

Antes de uma execução longa, confirme que o tráfego de fato sai pelo proxy:

```python
async with Chrome(options=options) as browser:
    tab = await browser.start()
    ip = (await tab.request.get('https://httpbin.org/ip')).json()['origin']
    print(f'Egress IP: {ip}')
```

!!! note "O proxy é apenas um sinal de detecção"
    Mudar seu IP não torna a automação indetectável, e o IP errado piora as coisas. Sistemas anti-bot pesam a reputação do IP (endereços residenciais parecem bem mais legítimos que faixas de datacenter) e cruzam o país do IP com o timezone e os idiomas do navegador. Combinar a geografia do proxy com o resto da sua configuração é parte de um fingerprint coerente, coberto em [Injeção de fingerprint](../stealth/fingerprint-injection.md).

## Próximos passos

- [Contextos de navegador](browser-contexts.md): isole sessões e dê a cada uma seu próprio proxy.
- [Injeção de fingerprint](../stealth/fingerprint-injection.md): combine a geografia do IP com o resto da identidade do navegador.
- [Requisições HTTP](http-requests.md): chame APIs pelo mesmo proxy e sessão.
- [Rede e proxies (aprofundamento)](../deep-dive/network/index.md): como os proxies funcionam e como são detectados.
