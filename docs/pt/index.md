<p align="center">
    <img src="/docs/resources/images/logo.png" alt="Pydoll Logo" /> <br><br>
</p>

# Pydoll

O Pydoll automatiza navegadores Chromium pelo Chrome DevTools Protocol, sem webdriver e sem esperas manuais. Use para extrair dados, testar aplicações web e automatizar fluxos reais de navegador em Python assíncrono.

## Instalação

<div class="termy">
```bash
$ pip install pydoll-python

---> 100%
```
</div>

O Pydoll controla o Chrome ou o Edge que já estão instalados na sua máquina. Você não precisa baixar um webdriver nem manter as versões do driver em sincronia com o navegador.

Novo no Pydoll? Siga o [Primeiros passos](getting-started.md) para um passo a passo completo.

## Início rápido

Abra uma página, encontre elementos pela forma como você os descreveria para uma pessoa e interaja com timing humanizado:

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com/autoscrape-labs/pydoll')

        star_button = await tab.find(
            tag_name='button',
            timeout=5,
            raise_exc=False
        )
        if not star_button:
            print('Button not found.')
            return

        await star_button.click()
        await asyncio.sleep(3)

asyncio.run(main())
```

Quando o objetivo é dado, e não interação, defina um modelo e deixe o Pydoll extraí-lo, tipado e validado:

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
        await tab.go_to('https://quotes.toscrape.com')

        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
        for quote in quotes:
            print(f'{quote.author}: {quote.text}')

asyncio.run(main())
```

Os modelos suportam seletores CSS e XPath, mira em atributos HTML, transformações personalizadas e modelos aninhados. Saiba mais em [Extração estruturada](guides/structured-extraction.md).

## Por que Pydoll

- **Sem webdriver**: o Pydoll se conecta direto ao navegador pelo Chrome DevTools Protocol. Nada para baixar, nenhuma incompatibilidade de versão para depurar.
- **Interações humanizadas**: os cliques seguem trajetórias curvas do mouse e a digitação tem ritmo variável, com erros de digitação corrigidos de vez em quando, então sua automação se comporta como uma pessoa no teclado.
- **Assíncrono por natureza**: construído sobre `asyncio`, então um único processo pode controlar muitas abas e navegadores ao mesmo tempo.
- **Tratamento do Cloudflare Turnstile**: o Pydoll detecta o widget Turnstile e clica nele nativamente. Nenhum serviço externo de captcha para pagar ou integrar.
- **Controle de rede**: monitore, intercepte e modifique requisições conforme a página as faz.
- **Extração tipada**: declare um modelo Pydantic e receba objetos validados e amigáveis à IDE, em vez de elementos crus.

## Próximos passos

- [Primeiros passos](getting-started.md): instale o Pydoll e rode seu primeiro script.
- [Sua primeira automação](first-automation.md): faça login em um site e extraia dados tipados.
- [Migrando do Selenium e do Playwright](migrating.md): mapeie os comandos que você conhece para o Pydoll.
- [Passando despercebido](stealth/index.md): a configuração mínima para evitar os sinais óbvios de bot.
- [Guias](guides/index.md): um guia por funcionalidade, do encontro de elementos à interceptação de requisições.
- [Referência da API](api/index.md): cada classe e método público.

## Principais patrocinadores

<div class="sponsor-grid-top">
  <a class="sponsor-card" href="https://substack.thewebscraping.club/p/pydoll-webdriver-scraping?utm_source=github&utm_medium=repo&utm_campaign=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner"><img src="/docs/resources/images/banner-the-webscraping-club.png" alt="The Web Scraping Club" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">The Web Scraping Club</span>
      <span class="sponsor-desc">A newsletter número 1 dedicada a web scraping. Leia a análise completa deles sobre o Pydoll.</span>
    </span>
  </a>
  <a class="sponsor-card" href="https://go.nodemaven.com/pydollaugust" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner"><img src="/docs/resources/images/nodemaven-banner.png" alt="NodeMaven" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">NodeMaven</span>
      <span class="sponsor-desc">Proxies de alta qualidade para scraping e automação. Segmentação por CEP, 99,9% de uptime, sem KYC.</span>
      <span class="sponsor-chips">
        <span class="sponsor-chip"><code>PYDOLL35</code> 35% de desconto</span>
        <span class="sponsor-chip"><code>PYDOLL40</code> 40% de desconto em ISP</span>
      </span>
    </span>
  </a>
  <a class="sponsor-card" href="https://niuproxy.com/?utm_source=pydoll&utm_medium=pydoll&ref=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner sponsor-banner--niuproxy"><img src="/docs/resources/images/niuproxy-banner.jpg" alt="NiuProxy" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">NiuProxy</span>
      <span class="sponsor-desc">Proxies residenciais rotativos: 10TB a $0.35/GB ou 1TB a $0.50/GB para usuários do Pydoll.</span>
      <span class="sponsor-chips">
        <span class="sponsor-chip"><code>PAY2</code> 10% de desconto na recarga</span>
      </span>
    </span>
  </a>
</div>

## Patrocinadores

Os patrocinadores mantêm o projeto funcionando e ajudam a financiar o desenvolvimento contínuo. Obrigado a todos que apoiam o Pydoll.

<div class="sponsor-grid-mini">
  <a class="sponsor-card sponsor-tile" href="https://proxy-seller.com/?partner=8DES01TZ1QGWR3" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="/docs/resources/images/proxy-seller-logo-white.svg" alt="Proxy-Seller" /></span>
    <span class="sponsor-desc">Proxies premium para agentes de IA, scraping &amp; automação</span>
    <span class="sponsor-chip"><code>PYDOLL</code> 15% de desconto</span>
  </a>
  <a class="sponsor-card sponsor-tile" href="https://www.thordata.com/?ls=github&lk=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="/docs/resources/images/Thordata-logo.png" alt="Thordata" /></span>
    <span class="sponsor-desc">Rede de proxies residenciais com mais de 190 localidades</span>
    <span class="sponsor-desc"><b>1GB grátis</b> pelo nosso link</span>
  </a>
  <a class="sponsor-card sponsor-tile" href="https://www.testmuai.com/?utm_medium=sponsor&utm_source=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="/docs/resources/images/logo-lamda-test.svg" alt="TestMu AI by LambdaTest" /></span>
    <span class="sponsor-desc">Nuvem de testes nativa de IA da LambdaTest</span>
  </a>
  <a class="sponsor-card sponsor-tile" href="https://www.swiftproxy.net/?ref=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="/docs/resources/images/swiftproxy-logo.png" alt="Swiftproxy" /></span>
    <span class="sponsor-desc">Proxies para web scraping &amp; automação</span>
  </a>
  <a class="sponsor-card sponsor-tile sponsor-tile--ghost" href="https://github.com/sponsors/thalissonvs" target="_blank" rel="noopener">
    <span class="sponsor-ghost-plus">+</span>
    <span class="sponsor-name">Sua logo aqui</span>
    <span class="sponsor-desc">Torne-se um patrocinador</span>
  </a>
</div>

<p>
  <a class="sponsor-cta" href="https://github.com/sponsors/thalissonvs" target="_blank" rel="noopener">&#10084;&#65039; Torne-se um patrocinador</a>
</p>

## Licença

O Pydoll é distribuído sob a [Licença MIT](https://github.com/autoscrape-labs/pydoll/blob/main/LICENSE), então você pode usá-lo livremente em projetos pessoais e comerciais.
