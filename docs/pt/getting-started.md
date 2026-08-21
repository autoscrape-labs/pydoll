# Primeiros passos

O Pydoll automatiza o Chrome ou o Edge que você já tem instalado, então a configuração são dois passos: instalar o pacote e rodar um script. Esta página leva você de uma pasta vazia até um script funcional que abre uma página real e lê dados dela.

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

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        first_quote = await tab.find(class_name='text')
        print(await first_quote.text)

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

- `async with Chrome() as browser` iniciou o Chrome instalado na sua máquina e garante que ele feche quando o bloco terminar, mesmo se o script falhar.
- `browser.start()` retornou uma [aba](api/browser/tab.md), o objeto que você vai usar para navegação, busca de elementos e todo o resto na página.
- `tab.find(class_name='text')` esperou o elemento aparecer e o retornou. Você não precisa adicionar sleeps nem escrever loops de espera; `find()` tenta de novo até o elemento aparecer ou o timeout expirar.

!!! note "Novo em Python assíncrono?"
    Toda chamada do Pydoll é `await`ada dentro de uma função `async def`, e `asyncio.run(main())` a inicia. Esse é todo o asyncio que você precisa por enquanto; o resto da documentação segue esse mesmo formato.

## Rodar em headless {#run-headless}

Em um servidor ou em CI não há display, então rode o navegador em headless. Passe opções ao criar o navegador:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.add_argument('--headless=new')

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        first_quote = await tab.find(class_name='text')
        print(await first_quote.text)

asyncio.run(main())
```

O script se comporta exatamente da mesma forma; a janela é invisível. `ChromiumOptions` aceita qualquer argumento de linha de comando do Chromium. Veja [Opções do navegador](guides/browser-options.md) para os que vale a pena conhecer.

!!! warning "Headless é detectável"
    O Chrome headless vaza mais do que uma string de User-Agent. Ele renderiza WebGL por um rasterizador de software em vez da sua GPU real, não expõe plugins de PDF, informa métricas de tela sem a folga da barra de tarefas e não tem dispositivos de mídia. Sistemas anti-bot verificam todos esses pontos, então definir um User-Agent sozinho não faz um navegador headless passar por headful, nem de longe. Se você automatiza sites que combatem bots, ou rode em headful, ou neutralize os sinais de headless com [Injeção de fingerprint](stealth/fingerprint-injection.md).

## Próximos passos

- [Sua primeira automação](first-automation.md): faça login em um site, interaja como uma pessoa e extraia dados tipados.
- [Passando despercebido](stealth/index.md): a configuração mínima para evitar os sinais óbvios de bot.
- [Encontrando elementos](guides/element-finding.md): todas as formas de localizar elementos com `find()` e `query()`.
