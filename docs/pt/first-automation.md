# Sua primeira automação

Automação de verdade é mais do que carregar uma página: você preenche formulários, clica em botões, espera a página reagir e coleta dados. Nesta página você vai construir um fluxo completo contra o [quotes.toscrape.com](https://quotes.toscrape.com), um site feito para praticar scraping: fazer login, confirmar que deu certo e extrair cada citação como um objeto tipado.

**Você vai aprender**

- [Como preencher um formulário e fazer login como uma pessoa](#log-in-like-a-person)
- [Como confirmar que a página reagiu](#confirm-the-login-worked)
- [Como extrair dados tipados com um modelo](#extract-typed-data)
- [Como fica o script completo](#the-full-script)

## Fazer login como uma pessoa {#log-in-like-a-person}

`find()` localiza elementos pelos atributos, e `type_text(humanize=True)` digita com o ritmo variável de um usuário real, incluindo erros de digitação corrigidos de vez em quando. Você não precisa focar o campo primeiro; o Pydoll clica nele antes de digitar.

```python
await tab.go_to('https://quotes.toscrape.com/login')

username = await tab.find(id='username')
await username.type_text('john', humanize=True)

password = await tab.find(id='password')
await password.type_text('SecretPass123', humanize=True)

submit = await tab.find(tag_name='input', type='submit')
await submit.click()
```

O formulário de login desse site aceita qualquer usuário e senha, então os valores só precisam parecer reais.

## Confirmar que o login funcionou {#confirm-the-login-worked}

Depois de enviar, a página recarrega e mostra um link de Logout. Encontrar esse link é a sua confirmação. `find()` espera por ele, então não há sleep entre clicar e verificar:

```python
logout_link = await tab.find(text='Logout', timeout=5, raise_exc=False)
if logout_link:
    print('Logged in.')
else:
    print('Login failed.')
```

`raise_exc=False` faz `find()` retornar `None` em vez de levantar uma exceção quando o elemento nunca aparece, o que mantém o controle de fluxo nas suas mãos.

## Extrair dados tipados {#extract-typed-data}

Com a sessão ativa, passe de interagir para coletar. Declare como é uma citação uma única vez, e `extract_all()` retorna uma lista de objetos validados:

```python
from pydoll.extractor import ExtractionModel, Field


class Quote(ExtractionModel):
    text: str = Field(selector='.text')
    author: str = Field(selector='.author')
    tags: list[str] = Field(selector='.tag')


quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)

for quote in quotes:
    print(f'{quote.author}: {quote.text}')
    print(f'  tags: {", ".join(quote.tags)}')
```

Cada `quote` é um objeto Pydantic de verdade: `quote.tags` é uma `list[str]`, sua IDE autocompleta os campos e `quote.model_dump_json()` o serializa. Sem consultar elemento por elemento, sem conversão manual de tipos.

## O script completo {#the-full-script}

Crie `first_automation.py`:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.extractor import ExtractionModel, Field


class Quote(ExtractionModel):
    text: str = Field(selector='.text')
    author: str = Field(selector='.author')
    tags: list[str] = Field(selector='.tag')


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.go_to('https://quotes.toscrape.com/login')

        username = await tab.find(id='username')
        await username.type_text('john', humanize=True)

        password = await tab.find(id='password')
        await password.type_text('SecretPass123', humanize=True)

        submit = await tab.find(tag_name='input', type='submit')
        await submit.click()

        logout_link = await tab.find(text='Logout', timeout=5, raise_exc=False)
        if not logout_link:
            print('Login failed.')
            return

        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
        for quote in quotes:
            print(f'{quote.author}: {quote.text}')

asyncio.run(main())
```

Rode:

```bash
python first_automation.py
```

Você vai ver o navegador digitar as credenciais, fazer login e, então, seu terminal se enche de autores e citações.

## Próximos passos

- [Passando despercebido](stealth/index.md): o próximo passo da jornada, evitar que sua automação pareça uma automação.
- [Encontrando elementos](guides/element-finding.md): cada atributo, seletor e estratégia que `find()` e `query()` suportam.
- [Extração estruturada](guides/structured-extraction.md): atributos, transformações e modelos aninhados.
