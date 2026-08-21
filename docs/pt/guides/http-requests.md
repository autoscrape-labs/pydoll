# Requisições HTTP no contexto do navegador

`tab.request` envia chamadas HTTP de dentro do navegador, então elas carregam automaticamente os cookies, a sessão e a autenticação da página. Faça login uma vez pela interface e depois chame a API do site diretamente: sem cookies para copiar, sem um segundo cliente HTTP para manter em sincronia com o navegador.

## Faça sua primeira requisição

`tab.request` oferece uma interface parecida com a do `requests`. Chame `get()` com uma URL e leia a resposta:

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        response = await tab.request.get('https://jsonplaceholder.typicode.com/posts/1')

        print(response.status_code)   # 200
        print(response.json()['title'])

asyncio.run(main())
```

A chamada passa pelo próprio `fetch` do navegador, então tudo o que o navegador já carrega (cookies, uma sessão ativa) vai junto com ela.

## Chame uma API depois de fazer login

Requisições no contexto do navegador são mais úteis depois de um login. Entre na página como um usuário faria e depois acesse a API do site com a sessão que você acabou de estabelecer. Você não extrai um token nem copia um conjunto de cookies; a requisição já vem autenticada.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        # 1. Faça login pela interface (esta é a sua própria aplicação autenticada)
        await tab.go_to('https://yourapp.com/login')
        await (await tab.find(id='username')).type_text('tester', humanize=True)
        await (await tab.find(id='password')).type_text('secret', humanize=True)
        await (await tab.find(tag_name='button', type='submit')).click()

        # 2. Chame a API com a sessão logada
        response = await tab.request.get('https://yourapp.com/api/profile')
        print(response.json())

asyncio.run(main())
```

!!! note "Sem manipulação de cookies"
    Nada acima copia cookies ou passa um token. Como a requisição roda no contexto do navegador, ela usa a mesma sessão que a página acabou de autenticar.

## Envie dados com POST

Passe `json=` para enviar um corpo JSON (o `Content-Type` é definido para você):

```python
response = await tab.request.post(
    'https://jsonplaceholder.typicode.com/posts',
    json={'title': 'Automating the web', 'body': 'with pydoll', 'userId': 1},
)
print(response.status_code)          # 201
print(response.json()['id'])
```

Passe `data=` para enviar campos codificados como formulário. `data` e `json` são mutuamente exclusivos:

```python
response = await tab.request.post(
    'https://httpbin.org/post',
    data={'username': 'tester', 'remember': 'true'},
)
print(response.json()['form'])       # {'username': 'tester', 'remember': 'true'}
```

`data` também aceita um `str` ou `bytes` quando você precisa enviar um corpo bruto.

## Adicione cabeçalhos à requisição

Cabeçalhos são uma lista de `HeaderEntry` (um dict tipado com `name` e `value`). Eles são adicionados por cima dos cabeçalhos automáticos do navegador, sem substituí-los:

```python
from pydoll.protocol.fetch.types import HeaderEntry

headers: list[HeaderEntry] = [
    {'name': 'X-API-Version', 'value': '2'},
    {'name': 'Accept-Language', 'value': 'pt-BR,pt;q=0.9'},
]

response = await tab.request.get('https://httpbin.org/headers', headers=headers)
print(response.json()['headers'])
```

!!! tip "Fique com cabeçalhos personalizados"
    Cabeçalhos personalizados como `X-API-Key` ou `Authorization` são enviados junto com os próprios cabeçalhos do navegador. Tentar sobrescrever um cabeçalho padrão (`User-Agent`, `Referer`) tem comportamento inconsistente, então deixe esses para o navegador e defina apenas os seus.

## Leia a resposta

O objeto `Response` espelha a biblioteca `requests`. `text`, `content`, `status_code`, `ok`, `headers`, `cookies` e `url` são propriedades; `json()` e `raise_for_status()` são métodos:

```python
response = await tab.request.get('https://jsonplaceholder.typicode.com/posts/1')

response.status_code     # 200
response.ok              # True para 2xx e 3xx

response.text            # corpo como str
response.content         # corpo como bytes
response.json()          # JSON parseado (dict ou list)

response.url             # URL final após quaisquer redirecionamentos

for header in response.headers:
    print(header['name'], header['value'])

for cookie in response.cookies:
    print(cookie['name'], cookie['value'])

response.raise_for_status()   # lança em um status 4xx ou 5xx
```

`response.url` guarda apenas a URL final. Para acompanhar toda a cadeia de redirecionamentos, observe as requisições com [Monitoramento de rede](network-monitoring.md).

## Outros métodos HTTP

`get` e `post` cobrem a maior parte do trabalho; o restante dos verbos está disponível quando você precisar, com o mesmo formato:

```python
await tab.request.put('https://jsonplaceholder.typicode.com/posts/1', json={'title': 'edited'})
await tab.request.patch('https://jsonplaceholder.typicode.com/posts/1', json={'title': 'tweaked'})
await tab.request.delete('https://jsonplaceholder.typicode.com/posts/1')
await tab.request.head('https://httpbin.org/get')
await tab.request.options('https://httpbin.org/get')
```

Para controle total sobre o verbo e todas as opções em uma única chamada, use `tab.request.request(method, url, params=..., data=..., json=..., headers=...)`.

## Próximos passos

- [Cookies e sessões](cookies-and-sessions.md): gerencie a sessão que suas requisições herdam.
- [Monitoramento de rede](network-monitoring.md): observe cada requisição que a página faz, incluindo redirecionamentos.
- [Interceptação de requisições](request-interception.md): altere ou bloqueie requisições antes que sejam enviadas.
