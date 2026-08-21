# Rede e proxies

Proxies são como você muda de onde seu tráfego parece vir, e como ele aparece na rede. Acertá-los (e entender como eles são pegos) significa saber o que de fato acontece em cada camada de uma requisição. Esta seção é o pano de fundo; para configurar um proxy no Pydoll, veja o guia [Proxies](../../guides/proxies.md).

## Comece por aqui

- [Fundamentos de rede](network-fundamentals.md): as camadas pelas quais uma requisição passa, do TCP ao TLS ao HTTP, e qual camada um proxy consegue alcançar.

## Tipos de proxy

- [Proxies HTTP/HTTPS](http-proxies.md): o forward proxy e o túnel CONNECT, o que cada um enxerga, e como a interceptação MITM muda o fingerprint TLS.
- [Proxies SOCKS](socks-proxies.md): o handshake da camada de transporte, SOCKS4 vs SOCKS5, DNS remoto, e a limitação de autenticação do SOCKS5 no Chrome.

## Detecção e mecânica

- [Detecção de proxy](proxy-detection.md): os sinais que entregam um proxy, da reputação de IP a divergências de header e fingerprint.
- [Construindo um servidor proxy](build-proxy.md): um proxy HTTP e SOCKS5 mínimo em Python, para ver como o encaminhamento realmente funciona.
- [Uso legal e ético](proxy-legal.md): termos de serviço, privacidade e scraping responsável.

## Relacionado

- [Proxies](../../guides/proxies.md): o guia prático para configurar proxies no Pydoll.
- [Fingerprinting de rede](../fingerprinting/network-fingerprinting.md): o que a camada de rede revela sobre um cliente.
