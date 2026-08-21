# Cookies e sessões

Uma sessão logada vive nos cookies do navegador. Leia-os, defina-os ou salve-os em disco e carregue-os de volta na próxima execução, para que sua automação faça login uma vez em vez de toda vez.

## Leia os cookies

`tab.get_cookies()` retorna todos os cookies no contexto de navegador da aba, não apenas os da página atual:

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com')

        cookies = await tab.get_cookies()
        print(f'{len(cookies)} cookies')
        for cookie in cookies:
            print(f"  {cookie['name']} = {cookie['value'][:16]}...")

asyncio.run(main())
```

Cada cookie é um dict com `name`, `value`, `domain`, `path`, `expires`, `secure`, `httpOnly`, `sameSite` e alguns campos somente leitura como `size` e `session`.

## Defina cookies

Passe uma lista de dicts de cookie para `tab.set_cookies()`. Apenas `name` e `value` são obrigatórios; o restante é opcional e recorre a valores padrão sensatos (`domain` é a página atual, `path` é `/`, `secure` e `httpOnly` são `False`).

```python
await tab.set_cookies([
    {'name': 'theme', 'value': 'dark', 'domain': 'github.com'},
    {'name': 'session', 'value': 'abc123', 'domain': 'github.com', 'secure': True, 'httpOnly': True},
])
```

Cookies se aplicam a todo o contexto de navegador, então toda aba nesse contexto os enxerga. Defina-os antes de navegar se o site os lê no carregamento.

## Limpe os cookies

```python
await tab.delete_all_cookies()
```

Isso limpa o contexto da aba. Para limpar um contexto específico, use o método de nível de navegador com o id dele: `await browser.delete_all_cookies(browser_context_id=ctx)`.

## Salve e restaure uma sessão

Faça login uma vez, salve os cookies e depois recarregue-os em execuções posteriores para pular o login por completo. Este exemplo usa [quotes.toscrape.com](https://quotes.toscrape.com/login), cujo login aceita quaisquer credenciais e define um cookie de sessão.

Primeira execução, faça login e salve:

```python
import asyncio
import json
from pathlib import Path

from pydoll.browser.chromium import Chrome

COOKIE_FILE = Path('session.json')


async def login_and_save():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com/login')

        await (await tab.find(id='username')).type_text('tester', humanize=True)
        await (await tab.find(id='password')).type_text('secret', humanize=True)
        await (await tab.find(tag_name='input', type='submit')).click()

        cookies = await tab.get_cookies()
        COOKIE_FILE.write_text(json.dumps(cookies))
        print(f'Saved {len(cookies)} cookies')

asyncio.run(login_and_save())
```

Nas execuções seguintes, carregue os cookies e você já está logado:

```python
import asyncio
import json
from pathlib import Path

from pydoll.browser.chromium import Chrome

COOKIE_FILE = Path('session.json')


async def restore_and_use():
    saved = json.loads(COOKIE_FILE.read_text())
    cookies = [
        {'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/')}
        for c in saved
    ]

    async with Chrome() as browser:
        tab = await browser.start()
        await tab.set_cookies(cookies)

        await tab.go_to('https://quotes.toscrape.com')
        logout = await tab.find(text='Logout', timeout=5, raise_exc=False)
        print('Session restored.' if logout else 'Session expired, log in again.')

asyncio.run(restore_and_use())
```

O passo de reformatação importa: `get_cookies()` retorna objetos `Cookie` completos com campos somente leitura (`size`, `session` e outros) que `set_cookies()` não aceita, então copie apenas os campos que podem ser definidos.

!!! warning "Cookies salvos são credenciais vivas"
    Um arquivo de sessão salvo concede acesso à conta. Mantenha-o fora do controle de versão, restrinja suas permissões e trate-o como uma senha. Carregue segredos do ambiente em vez de deixá-los fixos no código.

Uma vez que a sessão está ativa, as [requisições HTTP no contexto do navegador](http-requests.md) também a reutilizam, então `tab.request.get(...)` para a API do site já vem autenticado.

## Isole cookies por contexto

Cookies pertencem a um contexto de navegador. Dois contextos têm potes de cookies separados, que é como você roda duas contas lado a lado sem que uma atropele a outra. Defina cookies em um contexto específico com o método de nível de navegador:

```python
ctx = await browser.create_browser_context()
tab2 = await browser.new_tab(browser_context_id=ctx)

await browser.set_cookies(
    [{'name': 'session', 'value': 'second-account', 'domain': 'quotes.toscrape.com'}],
    browser_context_id=ctx,
)
```

Veja [Contextos de navegador](browser-contexts.md) para rodar sessões isoladas em paralelo.

!!! note "Incognito e `get_cookies`"
    `browser.get_cookies()` usa o domínio CDP `Storage`, que não consegue ler cookies sob a flag nativa `--incognito`. `tab.get_cookies()` usa o domínio `Network` e funciona ali, então prefira o método da aba em modo incognito. Para isolamento, use um contexto de navegador em vez de `--incognito`.

## Campos de CookieParam

Ao definir um cookie, estes são os campos que você pode passar:

| Campo | Tipo | Padrão |
|---|---|---|
| `name` | str | obrigatório |
| `value` | str | obrigatório |
| `domain` | str | domínio da página atual |
| `path` | str | `/` |
| `secure` | bool | `False` |
| `httpOnly` | bool | `False` |
| `sameSite` | `'Strict'` / `'Lax'` / `'None'` | padrão do navegador |
| `expires` | float (timestamp Unix) | cookie de sessão |

`CookieParam` (de `pydoll.protocol.network.types`) é um `TypedDict`, então na prática você passa um dict simples; o tipo só adiciona autocomplete no IDE.

## Próximos passos

- [Contextos de navegador](browser-contexts.md): potes de cookies isolados para sessões paralelas.
- [Requisições HTTP no contexto do navegador](http-requests.md): chamadas de API autenticadas que reutilizam a sessão.
- [Sua primeira automação](../first-automation.md): o fluxo de login que este guia salva.
