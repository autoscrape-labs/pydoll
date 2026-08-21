# Repetição

Páginas reais são instáveis: um elemento carrega um instante atrasado, uma navegação cai, uma requisição expira. O decorador `@retry` reexecuta uma função quando ela lança uma exceção, então uma falha transitória vira uma segunda tentativa em vez de uma quebra, e seu código de automação fica livre de encanamento de repetição.

## Repita uma função instável

Decore uma função assíncrona com `@retry` e liste as exceções que valem uma repetição. Se a função lançar uma delas, ela roda de novo, até `max_retries` vezes a mais.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout, ConnectionFailed


@retry(max_retries=3, exceptions=[WaitElementTimeout, ConnectionFailed])
async def scrape_title(url):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(url)
        heading = await tab.find(id='firstHeading', timeout=5)
        return await heading.text


async def main():
    title = await scrape_title('https://en.wikipedia.org/wiki/Web_scraping')
    print(title)


asyncio.run(main())
```

`max_retries` conta as repetições, não o total de tentativas: `max_retries=3` roda a função uma vez e depois até mais três vezes, ou seja, no máximo quatro tentativas.

## Repita apenas as falhas que você espera

`@retry` usa por padrão `exceptions=Exception`, que repete em tudo, incluindo bugs no seu próprio código que uma segunda execução não corrige (um erro de digitação, um seletor errado, um `KeyError`). Nomeie as exceções específicas em vez disso, para que bugs genuínos apareçam de imediato enquanto apenas falhas recuperáveis são repetidas.

```python
from pydoll.exceptions import ElementNotFound, WaitElementTimeout, ConnectionFailed

@retry(max_retries=3, exceptions=[ElementNotFound, WaitElementTimeout, ConnectionFailed])
async def open_dashboard(tab):
    await tab.go_to('https://app.example.test/dashboard')
    return await tab.find(id='dashboard', timeout=10)
```

As exceções que valem uma repetição em automação de navegador são as transitórias. Escolhas comuns:

- `WaitElementTimeout`, `ElementNotFound`: o elemento não estava lá a tempo.
- `ElementNotVisible`, `ElementNotInteractable`, `ClickIntercepted`: o elemento existia mas ainda não podia ser usado.
- `ConnectionFailed`, `NetworkError`, `PageLoadTimeout`: a página ou a conexão falhou.

## Espere entre as tentativas

Repetir instantaneamente raramente ajuda quando o problema é um servidor lento. Passe `delay` (segundos) para esperar entre as tentativas:

```python
@retry(max_retries=3, exceptions=[ConnectionFailed], delay=2)
async def fetch(tab, url):
    await tab.go_to(url)
    return await tab.find(id='content', timeout=10)
```

## Aumente o intervalo exponencialmente

Para limites de taxa ou um servidor sobrecarregado, um delay constante ainda o martela. Defina `exponential_backoff=True` e cada espera cresce: com `delay=1`, as pausas são de 2s, depois 4s, depois 8s, dando ao servidor cada vez mais espaço para se recuperar.

```python
@retry(
    max_retries=4,
    exceptions=[ConnectionFailed, PageLoadTimeout],
    delay=1,
    exponential_backoff=True,
)
async def fetch(tab, url):
    await tab.go_to(url)
    return await tab.find(id='content', timeout=10)
```

<iframe src="/docs/resources/visuals/retry-backoff.html" aria-label="Fixed delay vs exponential backoff retry timeline" style="width: 100%; height: 290px; border: 0;" loading="lazy"></iframe>

Execute cada modo: um delay fixo mantém o mesmo intervalo entre as tentativas, enquanto o backoff exponencial o dobra (2s, 4s, 8s), espaçando as repetições cada vez mais.

## Recupere-se antes da próxima tentativa

`on_retry` roda uma função assíncrona depois de cada tentativa falha, antes da próxima. Use-a para colocar a página de volta em um bom estado, por exemplo dando refresh após elementos obsoletos ou um modal que bloqueia.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, WaitElementTimeout


class ProductScraper:
    def __init__(self, tab):
        self.tab = tab

    async def recover(self):
        await self.tab.refresh()
        await asyncio.sleep(1)

    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, WaitElementTimeout],
        on_retry=recover,
        delay=1,
    )
    async def price(self):
        element = await self.tab.find(class_name='price', timeout=5)
        return await element.text
```

Duas coisas para saber sobre `on_retry`:

- Ela precisa ser uma função assíncrona, porque o decorador a aguarda.
- Quando o callback é um método, defina-o **acima** do método decorado no corpo da classe. O Python avalia `@retry(on_retry=recover)` enquanto a classe está sendo construída, então o nome já precisa existir.

## Lance seu próprio erro quando as repetições acabam

Por padrão, a última exceção é relançada quando toda tentativa falha. Passe `exception_to_raise` para expor um erro mais claro ao seu chamador:

```python
from pydoll.exceptions import ConnectionFailed


class SiteUnavailable(Exception):
    pass


@retry(
    max_retries=3,
    exceptions=[ConnectionFailed],
    exception_to_raise=SiteUnavailable('the site never responded'),
)
async def open_site(tab, url):
    await tab.go_to(url)
    return await tab.find(id='content', timeout=10)
```

## Próximos passos

- [Eventos](events.md): reaja a eventos de página e de rede em vez de repetir às cegas.
- [Busca de elementos](element-finding.md): o `timeout` do `find()` já espera por elementos atrasados, antes de qualquer repetição ser necessária.
- [Proxies](proxies.md): rotacione o IP de saída quando as falhas vêm de limites de taxa ou bloqueios.
