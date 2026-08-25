# Contextos de navegador

Um contexto de navegador é uma sessão isolada dentro de um mesmo processo de navegador: seus próprios cookies, armazenamento e cache, como um perfil anônimo separado. Use contextos para rodar vários logins ou identidades ao mesmo tempo em um único navegador, sem que um vaze para o outro.

## Criar um contexto e abrir uma aba nele

`create_browser_context()` retorna um id de contexto. Passe-o para `new_tab()` e essa aba vive no contexto isolado.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        await browser.start()

        context_id = await browser.create_browser_context()
        tab = await browser.new_tab('https://github.com', browser_context_id=context_id)

        print(await tab.title)

        await browser.delete_browser_context(context_id)

asyncio.run(main())
```

A aba que você obtém de `browser.start()` vive no **contexto padrão** permanente. Qualquer aba que você abrir sem um `browser_context_id` também entra nele.

## Contextos são isolados

O armazenamento definido em um contexto é invisível para outro. Aqui duas abas escrevem a mesma chave e leem valores diferentes de volta:

```python
await tab_a.go_to('https://the-internet.herokuapp.com')
await tab_b.go_to('https://the-internet.herokuapp.com')

await tab_a.execute_script("localStorage.setItem('user', 'Alice')")
await tab_b.execute_script("localStorage.setItem('user', 'Bob')")

a = await tab_a.execute_script("return localStorage.getItem('user')", return_by_value=True)
b = await tab_b.execute_script("return localStorage.getItem('user')", return_by_value=True)
print(a['result']['result']['value'])  # Alice
print(b['result']['result']['value'])  # Bob
```

Cookies, `localStorage`, `sessionStorage`, IndexedDB, cache e permissões são todos separados por contexto, então um login em um contexto não te autentica em nenhum outro lugar.

```mermaid
graph LR
    Browser[Processo do navegador] --> Default[Contexto padrão]
    Browser --> C1[Contexto 1]
    Browser --> C2[Contexto 2]
    Default --> T1[Aba A]
    C1 --> T2[Aba B]
    C2 --> T3[Aba C]
```

<iframe scrolling="no" src="/docs/resources/visuals/contexts-isolation.html" aria-label="Dois contextos de navegador, cada um com seu próprio pote de cookies, mostrando que um cookie definido em um não aparece no outro" style="width: 100%; height: 325px; border: 0;" loading="lazy"></iframe>

Faça login em cada contexto: o cookie cai apenas no pote daquele contexto. Nada atravessa, e é isso que torna os contextos bons para rodar sessões separadas em um só navegador.

## Rodar várias sessões lado a lado

Dê a cada conta seu próprio contexto e elas permanecem logadas de forma independente. Como as esperas se sobrepõem, `asyncio.gather` as executa de uma vez.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def open_session(browser, label):
    context_id = await browser.create_browser_context()
    tab = await browser.new_tab('https://the-internet.herokuapp.com', browser_context_id=context_id)
    await tab.execute_script(f"localStorage.setItem('account', '{label}')")
    return context_id, tab, label


async def main():
    async with Chrome() as browser:
        await browser.start()

        sessions = await asyncio.gather(
            open_session(browser, 'account-1'),
            open_session(browser, 'account-2'),
            open_session(browser, 'account-3'),
        )

        for context_id, tab, label in sessions:
            result = await tab.execute_script(
                "return localStorage.getItem('account')", return_by_value=True
            )
            active = result['result']['result']['value']
            print(f'{label}: {active}')
            await browser.delete_browser_context(context_id)

asyncio.run(main())
```

## Dar a um contexto seus próprios cookies

Os métodos de cookies em nível de navegador recebem um `browser_context_id`, então você pode semear ou ler os cookies de um contexto sem navegar em uma aba. Cookies definidos em um contexto nunca aparecem em outro.

```python
from pydoll.protocol.network.types import CookieParam

context_id = await browser.create_browser_context()

await browser.set_cookies(
    [CookieParam(name='session', value='abc123', domain='httpbin.org')],
    browser_context_id=context_id,
)

in_context = await browser.get_cookies(browser_context_id=context_id)
in_default = await browser.get_cookies()   # não inclui o cookie acima
```

Veja [Cookies e sessões](cookies-and-sessions.md) para ler, escrever e limpar cookies em profundidade.

## Rotear um contexto por seu próprio proxy

Passe `proxy_server` ao criar o contexto e toda requisição das abas dele passa por esse proxy. É assim que você roda diferentes geografias ao mesmo tempo.

```python
us = await browser.create_browser_context(proxy_server='http://us-proxy.example:8080')
eu = await browser.create_browser_context(proxy_server='http://eu-proxy.example:8080')

us_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=us)
eu_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=eu)
```

Credenciais na URL do proxy (`http://user:pass@host:port`) são tratadas para você: elas são removidas dos comandos CDP e fornecidas apenas quando o proxy exige autenticação. Veja [Proxies](proxies.md) para o panorama completo, e [Injeção de fingerprint](../stealth/fingerprint-injection.md) para manter uma identidade por contexto.

## Limpeza

`delete_browser_context()` remove um contexto e fecha todas as abas nele, o que é uma forma rápida de derrubar uma sessão inteira de uma vez.

```python
await browser.delete_browser_context(context_id)
```

!!! warning "Deletar um contexto fecha suas abas"
    Toda aba no contexto é fechada quando você o deleta, então leia antes qualquer coisa que ainda precise. O contexto padrão é permanente e não pode ser deletado; ele fecha quando o navegador para.

## Próximos passos

- [Abas](tabs.md): gerencie várias abas dentro de um contexto.
- [Cookies e sessões](cookies-and-sessions.md): semeie e inspecione os cookies de um contexto.
- [Proxies](proxies.md): roteie contextos por proxies diferentes, com autenticação.
