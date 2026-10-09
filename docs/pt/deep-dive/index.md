# Deep Dive

Os guias mostram como usar o Pydoll. Esta seção entra nos assuntos ao redor dele: o conhecimento de fundo que faz a automação séria funcionar. Você não precisa de nada disso para começar, mas quando um scraper é bloqueado, ou um proxy se comporta de forma estranha, ou você quer entender o que um sistema de detecção realmente enxerga, é aqui que ficam as explicações.

Ela cobre três áreas:

## Chrome DevTools Protocol

O [Chrome DevTools Protocol](cdp.md) é o que o Pydoll usa para falar com o navegador. Entendê-lo explica por que não existe webdriver, o que é um comando e um evento do CDP, e de onde vêm as capacidades do Pydoll.

## Rede e proxies

Como o tráfego realmente se move, e como os proxies se encaixam nisso.

- [Fundamentos de rede](network/network-fundamentals.md): as camadas pelas quais uma requisição passa, do TCP ao TLS ao HTTP.
- [Proxies HTTP/HTTPS](network/http-proxies.md) e [Proxies SOCKS](network/socks-proxies.md): como cada tipo de proxy funciona e quando usar cada um.
- [Detecção de proxy](network/proxy-detection.md): os sinais que entregam um proxy.
- [Construindo um servidor proxy](network/build-proxy.md): um proxy funcional do zero, para entender a mecânica.
- [Uso legal e ético](network/proxy-legal.md): os limites que vale conhecer.

## Fingerprinting

Como os sistemas de detecção identificam um navegador, camada por camada. Esta é a teoria por trás dos guias de [Stealth](../stealth/index.md).

- [Fingerprinting de rede](fingerprinting/network-fingerprinting.md): assinaturas de TCP/IP, TLS (JA3/JA4) e HTTP/2.
- [Fingerprinting de navegador](fingerprinting/browser-fingerprinting.md): canvas, WebGL, fontes e propriedades do navigator.
- [Fingerprinting comportamental](fingerprinting/behavioral-fingerprinting.md): análise de mouse, teclado e timing.
