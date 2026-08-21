# Async Python na prática

Toda chamada do Pydoll tem um `await` na frente. Se essa palavra-chave é novidade para você, esta é a página para ler primeiro. Você não precisa dominar o asyncio; precisa só do suficiente para ficar confortável, e para entender por que o Pydoll é construído em cima dele. Cada exemplo aqui roda por conta própria, então cole eles em um arquivo e veja o que acontece.

## Por que toda chamada do Pydoll é aguardada com await

A automação de navegador passa a maior parte do tempo esperando: uma página carregar, um elemento aparecer, uma requisição de rede voltar. O código Python comum fica parado durante essas esperas. O código async não: enquanto uma tarefa espera, outra pode rodar.

Essa única ideia é o que torna estes recursos do Pydoll possíveis:

- Controlar várias abas ou navegadores **ao mesmo tempo** em vez de um depois do outro.
- Observar o **tráfego de rede** enquanto seu script continua trabalhando.
- Executar **callbacks** no momento em que um evento da página dispara.

Nada disso precisa de threads. Tudo vem de `async` e `await`, então vale os dez minutos para pegar o formato.

## O formato: `async def`, `await`, `asyncio.run`

Três peças aparecem em todo script do Pydoll:

```python
import asyncio


async def main():          # 1. uma função async, chamada de coroutine
    print('hello')
    await asyncio.sleep(1)  # 2. await pausa aqui por 1 segundo
    print('one second later')


asyncio.run(main())         # 3. asyncio.run coloca ela para rodar
```

- `async def` define uma **coroutine**: uma função que pode pausar e retomar.
- `await` é onde ela pausa. Você só pode usar `await` dentro de um `async def`.
- `asyncio.run()` é o ponto de entrada que de fato roda a coroutine. É a única chamada que *não* é aguardada com await, porque é ela que dá partida em tudo.

Chamar `main()` sozinho não faz nada útil; só cria um objeto coroutine. `asyncio.run(main())` é o que faz ela andar.

## `await` significa "espere aqui, mas deixe outro trabalho rodar"

`await asyncio.sleep(1)` não congela o seu programa inteiro por um segundo. Ele pausa *esta* coroutine e devolve o controle, então qualquer outra coisa que esteja pronta pode rodar durante esse segundo. Essa devolução de controle é o que torna a concorrência possível, e a próxima seção mostra por que isso importa.

## Fazendo várias coisas ao mesmo tempo

Imagine duas tarefas domésticas que são, em sua maior parte, espera: ferver água e torrar pão, dois minutos cada.

Faça uma depois da outra e você espera pelas duas em sequência:

```python
import asyncio
import time


async def boil_water():
    print('kettle on')
    await asyncio.sleep(2)
    print('water boiled')


async def toast_bread():
    print('bread in')
    await asyncio.sleep(2)
    print('toast ready')


async def main():
    start = time.perf_counter()
    await boil_water()
    await toast_bread()
    print(f'done in {time.perf_counter() - start:.1f}s')


asyncio.run(main())
```

Rode isso e você obtém cerca de **4 segundos**, porque você aguardou uma tarefa por completo antes de começar a próxima.

Agora inicie as duas e depois espere pelas duas juntas com `asyncio.gather`:

```python
async def main():
    start = time.perf_counter()
    await asyncio.gather(boil_water(), toast_bread())
    print(f'done in {time.perf_counter() - start:.1f}s')


asyncio.run(main())
```

Desta vez são cerca de **2 segundos**. As duas esperas se sobrepõem. A água ferve enquanto o pão torra.

<iframe src="/docs/resources/visuals/async-flow.html" aria-label="Async sequencial vs concorrente, animado" style="width: 100%; height: 285px; border: 0;" loading="lazy"></iframe>

Rode cada modo e observe o cronômetro: o sequencial termina em 4.0s, o concorrente em 2.0s, porque as duas esperas se sobrepõem.

`asyncio.gather(*coroutines)` roda tudo o que você passa concorrentemente e retorna os resultados na ordem assim que todos terminam.

## A mesma ideia, com Pydoll

Troque as tarefas domésticas por páginas reais e nada muda. Carregar três páginas uma de cada vez espera três vezes; carregar elas com `gather` sobrepõe as esperas.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def title_of(browser, url):
    tab = await browser.new_tab(url)
    title = await tab.title
    await tab.close()
    return title


async def main():
    urls = [
        'https://en.wikipedia.org/wiki/Async/await',
        'https://en.wikipedia.org/wiki/Coroutine',
        'https://en.wikipedia.org/wiki/Web_scraping',
    ]
    async with Chrome() as browser:
        await browser.start()
        titles = await asyncio.gather(*(title_of(browser, url) for url in urls))
        for title in titles:
            print(title)


asyncio.run(main())
```

As três páginas carregam concorrentemente, então o todo demora mais ou menos o tempo da página individual mais lenta.

## Dois erros que você provavelmente vai encontrar

Esses são os tropeços normais quando async é novidade. São rápidos de reconhecer depois que você já os viu.

**Você esqueceu o `await`.** Sem ele, você obtém o objeto coroutine em vez do resultado dele, e um aviso:

```python
title = tab.title
print(title)   # <coroutine object ...>, e: RuntimeWarning: coroutine was never awaited
```

A correção é adicionar `await`: `title = await tab.title`.

**Você chamou código async sem iniciar o loop.** `await` só funciona dentro de um `async def`, e coroutines só rodam sob `asyncio.run()` (ou outro loop em execução):

```python
main()   # nada acontece; isso só cria uma coroutine
```

A correção é `asyncio.run(main())`.

## Onde o async compensa no Pydoll

Uma vez que o formato esteja confortável, estes recursos são o `gather` e os callbacks em ação:

- **Automação em paralelo:** controle várias abas ou navegadores de uma vez com `gather`. Veja [Abas](../guides/tabs.md).
- **Interceptação de rede:** observe e modifique requisições enquanto seu script continua. Veja [Monitoramento de rede](../guides/network-monitoring.md).
- **Callbacks de eventos:** execute uma função no momento em que um evento de página ou de rede dispara. Veja [Eventos](../guides/events.md).

## Próximos passos

- [Instalação](../getting-started.md): instale o Pydoll e rode seu primeiro script.
- [Conceitos centrais](../guides/core-concepts.md): como os objetos do navegador e da aba se encaixam.
- [Seletores: CSS e XPath](selectors.md): o outro pré-requisito, escolher e escrever seletores.
