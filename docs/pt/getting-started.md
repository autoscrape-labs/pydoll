# Primeiros passos

O Pydoll automatiza o Chrome ou o Edge que você já tem instalado, então a configuração são dois passos: instalar o pacote e rodar um script. Esta página leva você de uma pasta vazia até um script funcional que abre uma página real e lê dados dela.

O Pydoll suporta duas variações da sua API: síncrona e assíncrona. Elas expõem as mesmas classes e métodos; a API síncrona bloqueia a cada chamada, e a assíncrona é a escolha se o seu projeto já roda em `asyncio` ou se você quer controlar muitas abas de uma vez. Todo exemplo de código desta documentação tem uma aba **Sync** e uma **Async**, então escolha a que combina com o seu código.

**Você vai aprender**

- [Como instalar o Pydoll](#install-pydoll)
- [Como escrever e rodar seu primeiro script](#write-your-first-script)
- [Como rodar sem uma janela visível do navegador](#run-headless)

## Instalar o Pydoll {#install-pydoll}

O Pydoll requer Python 3.10 ou mais recente, e o Google Chrome ou o Microsoft Edge instalado na sua máquina. Você não precisa baixar um webdriver; o Pydoll fala diretamente com o navegador.

Crie e ative um [ambiente virtual](https://docs.python.org/3/tutorial/venv.html) e, em seguida, instale:

<div class="termy">
```bash
$ pip install pydoll-python

---> 100%
```
</div>

Para experimentar a versão de desenvolvimento mais recente, instale a partir do GitHub:

```bash
pip install git+https://github.com/autoscrape-labs/pydoll.git
```

## Escrever seu primeiro script {#write-your-first-script}

Crie um arquivo chamado `first_script.py`:

=== "Sync"

    ```python
    from pydoll import Chrome

    def main():
        with Chrome() as browser:
            tab = browser.start()
            tab.go_to('https://quotes.toscrape.com')

            first_quote = tab.find(class_name='text')
            print(first_quote.text())

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://quotes.toscrape.com')

            first_quote = await tab.find(class_name='text')
            print(await first_quote.text())

    asyncio.run(main())
    ```

Rode:

```bash
python first_script.py
```

Uma janela do Chrome abre, carrega a página e seu terminal imprime a primeira citação:

```
"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
```

Três coisas aconteceram aí:

- `with Chrome() as browser` (ou `async with` na API assíncrona) iniciou o Chrome instalado na sua máquina e garante que ele feche quando o bloco terminar, mesmo se o script falhar.
- `browser.start()` retornou uma [aba](api/browser/tab.md), o objeto que você vai usar para navegação, busca de elementos e todo o resto na página.
- `tab.find(class_name='text')` esperou o elemento aparecer e o retornou. Você não precisa adicionar sleeps nem escrever loops de espera; `find()` tenta de novo até o elemento aparecer ou o timeout expirar.

!!! note "Síncrono ou assíncrono?"
    A forma síncrona importa de `pydoll.sync` e chama métodos como qualquer outra função Python. A forma assíncrona importa de `pydoll`, usa `await` em cada chamada dentro de uma função `async def` e começa com `asyncio.run(main())`. Esse é todo o asyncio que você precisa por enquanto; se for novidade, [Python assíncrono na prática](basics/async-python.md) cobre o resto.

## Rodar em headless {#run-headless}

Em um servidor ou em CI não há display, então rode o navegador em headless. Passe opções ao criar o navegador:

=== "Sync"

    ```python
    from pydoll import Chrome, ChromiumOptions

    def main():
        options = ChromiumOptions()
        options.add_argument('--headless=new')

        with Chrome(options=options) as browser:
            tab = browser.start()
            tab.go_to('https://quotes.toscrape.com')

            first_quote = tab.find(class_name='text')
            print(first_quote.text())

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome, ChromiumOptions


    async def main():
        options = ChromiumOptions()
        options.add_argument('--headless=new')

        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to('https://quotes.toscrape.com')

            first_quote = await tab.find(class_name='text')
            print(await first_quote.text())

    asyncio.run(main())
    ```

O script se comporta exatamente da mesma forma; a janela é invisível. `ChromiumOptions` aceita qualquer argumento de linha de comando do Chromium. Veja [Opções do navegador](guides/browser-options.md) para os que vale a pena conhecer.

!!! warning "Headless é detectável"
    O Chrome headless vaza mais do que uma string de User-Agent. Ele renderiza WebGL por um rasterizador de software em vez da sua GPU real, não expõe plugins de PDF, informa métricas de tela sem a folga da barra de tarefas e não tem dispositivos de mídia. Sistemas anti-bot verificam todos esses pontos, então definir um User-Agent sozinho não faz um navegador headless passar por headful, nem de longe. Se você automatiza sites que combatem bots, ou rode em headful, ou neutralize os sinais de headless com [Injeção de fingerprint](stealth/fingerprint-injection.md).

## Próximos passos

- [Sua primeira automação](first-automation.md): faça login em um site, interaja como uma pessoa e extraia dados tipados.
- [Traga seu script Playwright](playwright.md): já tem código Playwright? Um import o coloca no Pydoll.
- [Passando despercebido](stealth/index.md): a configuração mínima para evitar os sinais óbvios de bot.
- [Encontrando elementos](guides/element-finding.md): todas as formas de localizar elementos com `find()` e `query()`.
