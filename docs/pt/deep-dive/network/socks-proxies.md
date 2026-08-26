# Proxies SOCKS

Um proxy SOCKS encaminha conexões TCP cruas (e, no SOCKS5, UDP) sem entender o que corre por elas, o que o torna uma forma de baixo nível e agnóstica ao protocolo de rotear tráfego através de outro host. Esta página cobre como o SOCKS funciona, a diferença entre SOCKS4 e SOCKS5, o handshake do SOCKS5, o comportamento de DNS, e a única coisa que morde a automação: o Chrome não faz autenticação SOCKS5.

Para a configuração prática, veja o guia [Proxies](../../guides/proxies.md); esta página é a teoria por trás dele.

## Como o SOCKS difere de proxies HTTP

A diferença é o que cada proxy consegue ver. Um proxy HTTP trabalha na camada de aplicação e entende HTTP: pode ler URLs, headers e cookies (para tráfego não criptografado), modificá-los em trânsito, cachear respostas, e adicionar headers como `Via` e `X-Forwarded-For`. Isso é útil para filtragem, mas significa que você confia seus dados de aplicação ao operador.

Um proxy SOCKS trabalha abaixo da camada de aplicação. Ele vê o endereço de destino, a porta e o volume de dados, e nada mais. HTTP, HTTPS, SSH, WebSocket, ou qualquer protocolo customizado parecem todos iguais para ele: bytes repassados entre dois endpoints. Envie uma requisição HTTPS através do SOCKS5 e o proxy vê `example.com:443` e um stream TLS criptografado. Ele não pode ler a URL, os headers ou a resposta, não adiciona headers identificadores, e não termina o TLS. O túnel criptografado corre de ponta a ponta.

O SOCKS é um protocolo de proxying, não de criptografia. O nome se refere à travessia segura de firewall, não à criptografia. HTTP não criptografado enviado através do SOCKS5 ainda é legível pelo operador do proxy, mesmo que o proxy não seja feito para inspecioná-lo. Para criptografia de fato você precisa de TLS por cima, ou de um túnel criptografado (SSH, VPN) em volta da conexão SOCKS.

!!! note "Modelo de confiança"
    Com um proxy HTTP você confia que o operador não vai logar seu histórico, roubar tokens ou modificar respostas. Com o SOCKS5 você confia nele apenas para encaminhar pacotes e não logar metadados de conexão. A superfície de ataque é menor, não zero.

## SOCKS4 vs SOCKS5

O SOCKS4 veio da NEC no início dos anos 1990 sem RFC formal. O SOCKS5 foi padronizado como RFC 1928 em 1996 para corrigir as limitações do SOCKS4.

| Recurso | SOCKS4 | SOCKS5 |
|---------|--------|--------|
| Padrão | De facto (1992), sem RFC | RFC 1928 (1996) |
| Autenticação | Apenas identificação (USERID, sem senha) | Nenhuma, usuário/senha, ou GSSAPI |
| Versão de IP | Apenas IPv4 | IPv4 e IPv6 |
| Suporte a UDP | Não | Sim (UDP ASSOCIATE) |
| Resolução de DNS | No cliente (SOCKS4A adiciona no servidor) | No servidor para nomes de domínio (ATYP=0x03) |

O SOCKS5 é a melhor escolha em todo caso prático. Use o SOCKS4 apenas quando um proxy não suportar SOCKS5.

## O handshake do SOCKS5

Uma conexão SOCKS5 segue a RFC 1928 em três fases: negociação de método, autenticação opcional, e então a requisição de conexão.

<iframe scrolling="no" src="/docs/resources/visuals/socks5-handshake.html" aria-label="The SOCKS5 handshake in real RFC 1928/1929 bytes: method negotiation, optional username/password auth, then the CONNECT request, decoded field by field" style="width: 100%; height: 860px; border: 0;" loading="lazy"></iframe>

### Fase 1: negociação de método

O cliente abre uma conexão TCP ao proxy e envia a versão do protocolo (`0x05`) e os métodos de autenticação que suporta.

```python
# Client hello
[
    0x05,        # VER: versão 5
    0x02,        # NMETHODS: número de métodos oferecidos
    0x00, 0x02,  # METHODS: sem auth (0x00) e usuário/senha (0x02)
]
```

O proxy responde com o método que escolheu. Se ele exige autenticação e o cliente ofereceu `0x02`, ele seleciona esse. Se nada aceitável foi oferecido, ele responde `0xFF` e fecha a conexão.

```python
# Server response
[
    0x05,  # VER: versão 5
    0x02,  # METHOD: usuário/senha selecionado
]
```

Códigos de método (RFC 1928): `0x00` sem autenticação, `0x01` GSSAPI, `0x02` usuário/senha (RFC 1929), `0xFF` nenhum método aceitável.

### Fase 2: autenticação

Se o proxy selecionou `0x02`, o cliente envia as credenciais conforme a RFC 1929. Essa subnegociação usa seu próprio byte de versão (`0x01`, não `0x05`).

```python
# Client authentication
[
    0x01,             # VER: versão da subnegociação 1
    len(username),    # ULEN: tamanho do username (máx 255)
    *username_bytes,  # UNAME
    len(password),    # PLEN: tamanho da senha (máx 255)
    *password_bytes,  # PASSWD
]

# Server response
[
    0x01,  # VER: versão da subnegociação 1
    0x00,  # STATUS: 0 = sucesso, diferente de zero = falha
]
```

As credenciais viajam em texto claro durante esse handshake; isso é inerente à RFC 1929. Para ambientes sensíveis, envolva a conexão SOCKS em um túnel SSH ou VPN.

### Fase 3: requisição de conexão

Após a autenticação (ou imediatamente, se nenhuma era necessária), o cliente envia o comando, o endereço de destino e a porta.

```python
[
    0x05,           # VER: versão 5
    0x01,           # CMD: 1=CONNECT, 2=BIND, 3=UDP ASSOCIATE
    0x00,           # RSV: reservado
    0x03,           # ATYP: 1=IPv4, 3=domínio, 4=IPv6
    len(domain),    # tamanho do domínio (somente ATYP=0x03)
    *domain_bytes,  # nome do domínio
    *port_bytes,    # porta (2 bytes, big-endian)
]
```

O tipo de endereço (ATYP) define o formato: `0x01` são 4 bytes de IPv4, `0x04` são 16 bytes de IPv6, e `0x03` é um byte de tamanho mais o nome do domínio. Quando o cliente envia um nome de domínio, o proxy resolve o DNS do lado dele, o que mantém o DNS fora da rede local do cliente.

O proxy conecta ao destino e responde:

```python
[
    0x05,        # VER: versão 5
    0x00,        # REP: 0x00 sucesso, 0x01-0x08 erros
    0x00,        # RSV: reservado
    0x01,        # ATYP: tipo de endereço do endereço vinculado
    *bind_addr,  # BND.ADDR
    *bind_port,  # BND.PORT
]
```

Códigos de resposta: `0x00` sucesso, `0x01` falha geral, `0x02` não permitido, `0x03` rede inalcançável, `0x04` host inalcançável, `0x05` conexão recusada, `0x06` TTL expirado, `0x07` comando não suportado, `0x08` tipo de endereço não suportado. Após uma resposta de sucesso, o proxy repassa dados nos dois sentidos. O handshake é binário, então é eficiente mas difícil de ler sem um hex dump.

## Suporte a UDP

O SOCKS5 pode fazer proxy de UDP através do comando `UDP ASSOCIATE` (CMD=0x03). O cliente envia a requisição pela conexão de controle TCP, e o proxy retorna um endereço e porta de relay. O cliente então envia datagramas UDP para esse relay, cada um prefixado com um pequeno header nomeando o destino:

```python
[
    0x00, 0x00,  # RSV: reservado
    0x00,        # FRAG: número do fragmento (0 = nenhum)
    0x01,        # ATYP: tipo de endereço
    *dst_addr,   # DST.ADDR
    *dst_port,   # DST.PORT
    *data,       # dados de aplicação
]
```

A conexão de controle TCP precisa permanecer aberta durante toda a vida da associação; se ela fecha, o proxy descarta o relay de UDP.

!!! warning "O Chrome não faz proxy de UDP sobre SOCKS5"
    Mesmo com um proxy SOCKS5 configurado, o Chrome só faz proxy de TCP. WebRTC, DNS-over-UDP, e outros tráfegos UDP contornam o proxy, então um vazamento de IP por WebRTC ainda é possível. Defina `options.webrtc_leak_protection = True` (que adiciona `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`) para mitigá-lo. Veja [Fundamentos de rede](network-fundamentals.md).

## Resolução de DNS

Uma crença comum é que proxies HTTP vazam DNS enquanto o SOCKS5 não. No Chrome a realidade é mais específica.

Com qualquer proxy configurado (HTTP, HTTPS ou SOCKS5), o Chrome entrega os hostnames ao proxy em vez de resolvê-los localmente. Para um proxy HTTP, o hostname está na linha `CONNECT host:443`; para o SOCKS5, está na requisição de conexão com ATYP=0x03. Em ambos os casos o proxy resolve o DNS, e o Chrome não faz consulta DNS local para tráfego com proxy. A diferença real não é quem resolve o DNS, mas o que o proxy vê: um proxy HTTP vê a URL completa de requisições não criptografadas e o hostname de requisições CONNECT, enquanto um proxy SOCKS5 vê apenas o host e a porta de destino como parâmetros opacos.

Uma ressalva: o prefetcher de DNS do Chrome ainda pode fazer consultas locais para hostnames encontrados no conteúdo da página, o que vaza os domínios que você navega ao seu resolver local. Desabilite o prefetch de DNS para preveni-lo.

!!! note "`socks5://` vs `socks5h://`"
    Muitas ferramentas distinguem `socks5://` (o cliente resolve o DNS) de `socks5h://` (o proxy o resolve). O Chrome sempre resolve o DNS do lado do proxy para o SOCKS5, então ele se comporta como `socks5h://` de qualquer jeito. Se você usa curl, Firefox ou bibliotecas Python junto com o Pydoll, prefira `socks5h://` para evitar vazamentos de DNS ali.

## SOCKS5 e resistência a MITM

O SOCKS5 é frequentemente chamado de resistente a MITM, e em um sentido específico ele é: porque não entende TLS, não tem como terminar e recriptografar uma conexão TLS. Ele repassa bytes criptografados sem tocar.

Um proxy HTTP pode realizar terminação de TLS apresentando seu próprio certificado, descriptografando, inspecionando ou modificando, e recriptografando em direção ao servidor. Isso exige que o cliente confie na CA do proxy, e é detectável através de certificate pinning e Certificate Transparency. O comportamento HTTPS normal de um proxy HTTP (CONNECT) é um túnel transparente sem terminação, mas a possibilidade existe. Com o SOCKS5 ela não existe, porque o proxy nunca toca nos dados de aplicação.

O TLS é o que fornece a proteção criptográfica aqui, não o SOCKS5. A vantagem do SOCKS5 é arquitetural, no sentido de que ele nem exige nem habilita terminação de TLS, não criptográfica.

## Fingerprinting através do SOCKS5

O SOCKS5 não muda o fingerprint do seu navegador. O TLS ClientHello passa byte por byte, então o servidor vê seu fingerprint JA3/JA4 exato, e o mesmo vale para as configurações do HTTP/2, a ordem dos headers, e todo outro sinal da camada de aplicação. O SOCKS5 esconde seu IP e impede o proxy de injetar headers; ele não faz nada pelo fingerprinting de navegador ou comportamental. Para isso, trate as outras camadas também: veja [Técnicas de evasão](../../stealth/evasion-techniques.md).

## Autenticação SOCKS5 no Chrome

O Chrome não suporta autenticação SOCKS5 por usuário/senha, uma limitação de longa data rastreada como [issue 40323993 do Chromium](https://issues.chromium.org/issues/40323993). Durante a negociação de método, o Chrome oferece apenas `0x00` (sem autenticação); se o proxy exige credenciais, a conexão falha silenciosamente. Definir `--proxy-server=socks5://user:pass@proxy:1080` não funciona, porque o Chrome ignora as credenciais embutidas.

Isso difere da autenticação de proxy HTTP. Proxies HTTP autenticam com um status `407 Proxy Authentication Required`, que o Chrome expõe através do domínio Fetch do CDP; o Pydoll responde a esses eventos `Fetch.authRequired` com suas credenciais automaticamente. A autenticação SOCKS5 acontece em um handshake binário antes de qualquer HTTP existir, então não há 407, não há `Fetch.authRequired`, e não há como uma ferramenta baseada em CDP injetar credenciais nela.

### O SOCKS5Forwarder do Pydoll

A correção padrão é um forwarder local: um pequeno servidor SOCKS5 no localhost que aceita conexões não autenticadas do Chrome e as encaminha ao proxy remoto com autenticação completa.

<iframe scrolling="no" src="/docs/resources/visuals/socks5-forwarder.html" aria-label="The pydoll SOCKS5Forwarder bridges two handshakes: a no-auth SOCKS5 handshake to Chrome on one side and a full authenticated handshake to the remote proxy on the other, injecting the credentials Chrome cannot send" style="width: 100%; height: 900px; border: 0;" loading="lazy"></iframe>

O Pydoll traz o `SOCKS5Forwarder` em `pydoll.utils`. É uma implementação assíncrona em Python puro, sem dependências, que lida com o handshake completo com o proxy remoto, incluindo autenticação por usuário/senha e os tipos de endereço IPv4, IPv6 e domínio.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.utils import SOCKS5Forwarder


async def main():
    forwarder = SOCKS5Forwarder(
        remote_host='proxy.example.com',
        remote_port=1080,
        username='myuser',
        password='mypass',
        local_port=1081,   # 0 deixa o SO escolher uma porta livre
    )
    async with forwarder:
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server=socks5://127.0.0.1:{forwarder.local_port}')

        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to('https://httpbin.org/ip')

asyncio.run(main())
```

O forwarder faz bind em `127.0.0.1`, então é alcançável apenas a partir da sua máquina. Não faça bind em `0.0.0.0`, o que exporia um proxy SOCKS5 não autenticado à rede. Como tudo roda pela interface de loopback, ele adiciona latência de sub-milissegundo.

!!! tip "Ambientes restritos"
    Alguns ambientes (containers, serverless, VMs endurecidas) restringem o bind em portas locais. Use `local_port=0` para deixar o SO atribuir uma. Se o bind local estiver totalmente bloqueado, use um proxy HTTP CONNECT em vez disso, que o Chrome suporta nativamente com a autenticação tratada para você (veja [Proxies](../../guides/proxies.md)).

## Relacionado

- [Proxies HTTP/HTTPS](http-proxies.md): a alternativa na camada de aplicação.
- [Fundamentos de rede](network-fundamentals.md): as camadas por baixo.
- [Detecção de proxy](proxy-detection.md): como até proxies SOCKS5 são detectados.
- [Construindo um servidor proxy](build-proxy.md): implemente um servidor SOCKS5 você mesmo.
- [Proxies](../../guides/proxies.md): configure proxies no Pydoll.

## Referências

- RFC 1928: SOCKS Protocol Version 5 (1996) - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 (1996) - https://datatracker.ietf.org/doc/html/rfc1929
- Chromium issue 40323993: SOCKS5 authentication - https://issues.chromium.org/issues/40323993
- BrowserLeaks: WebRTC leak test - https://browserleaks.com/webrtc
