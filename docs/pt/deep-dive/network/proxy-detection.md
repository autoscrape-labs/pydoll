# Detecção de Proxy e Anonimato

## Introdução: A Corrida Armamentista de Detecção e Evasão

A detecção de proxy é um **sistema adversário** sofisticado onde sites implementam técnicas cada vez mais avançadas para identificar usuários de proxy, enquanto usuários e provedores de proxy desenvolvem contramedidas para evadir a detecção. Entender essa corrida armamentista é essencial para qualquer um trabalhando com automação de navegador, web scraping ou aplicações focadas em privacidade.

Este documento revela os mecanismos técnicos que os sites usam para detectar o uso de proxy, desde simples análises de cabeçalho HTTP até reconhecimento complexo de padrões comportamentais. Exploraremos:

- **Detecção baseada em IP** (bancos de dados de reputação, análise de ASN, inconsistências de geolocalização)
- **Fingerprinting de camada de rede** (características da pilha TCP/IP, padrões de TLS ClientHello)
- **Análise de camada de aplicação** (cabeçalhos HTTP, downgrades de protocolo, padrões de conexão)
- **Detecção comportamental** (análise de tempo, movimento do mouse, padrões de navegação)
- **Verificações de consistência** (resolução DNS, desencontros de fuso horário/localidade)

!!! info "Navegação do Módulo"
    - **[← Proxies SOCKS](./socks-proxies.md)** - Fundamentos de proxy de camada de sessão
    - **[← Proxies HTTP/HTTPS](./http-proxies.md)** - Fundamentos de proxy de camada de aplicação
    - **[← Visão Geral de Rede e Segurança](./index.md)** - Introdução do módulo
    - **[→ Construindo Proxies](./build-proxy.md)** - Implementação e tópicos avançados
    
    Para técnicas aprofundadas de fingerprinting, veja **[Network Fingerprinting (Fingerprinting de Rede)](../fingerprinting/network-fingerprinting.md)** e **[Browser Fingerprinting (Fingerprinting de Navegador)](../fingerprinting/browser-fingerprinting.md)**.

### Por que a Detecção Importa

Sites detectam proxies por várias razões legítimas e de negócios:

1.  **Prevenção a Fraudes**: Impedir tomada de contas, credential stuffing, fraudes de pagamento
2.  **Licenciamento de Conteúdo**: Aplicar restrições geográficas para conteúdo licenciado (Netflix, Hulu, streaming de esportes)
3.  **Discriminação de Preço**: Impedir arbitragem através de diferenças regionais de preços
4.  **Mitigação de Bots**: Bloquear scraping automatizado, coleta de dados, bots cambistas (scalping)
5.  **Segurança**: Bloquear tráfego de infraestruturas de proxy maliciosas conhecidas
6.  **Aplicação dos Termos de Serviço**: Impedir evasão de banimento, múltiplas contas

**A Economia:**

- **Para sites**: Detecção previne perda de receita (estimada em $100B+ anuais por tráfego de bots)
- **Para usuários de proxy**: Evasão permite casos de uso legítimos (privacidade, testes, scraping)
- **Para provedores de proxy**: IPs residenciais custam 10-100x mais que IPs de datacenter

!!! danger "Nenhum Proxy é Verdadeiramente Indetectável"
    Até mesmo **proxies residenciais de elite** podem ser detectados através de análise multi-sinal sofisticada:

    - Bancos de dados de reputação de IP agora rastreiam pools de proxies residenciais
    - Análise de tempo detecta inconsistências de latência de rede
    - Análise comportamental identifica padrões não humanos
    - Fingerprinting de navegador revela frameworks de automação
    
    O objetivo é tornar a detecção **difícil e cara**, não impossível. Um adversário determinado com recursos suficientes pode detectar quase qualquer proxy com alta confiança.

## Detecção de Proxy e Fingerprinting

Sites podem detectar o uso de proxy através de várias técnicas. Entender os níveis de anonimato de proxy é crucial para avaliar o risco de detecção.

### Níveis de Anonimato de Proxy

Nem todos os proxies fornecem o mesmo nível de anonimato. Eles são classificados em três categorias com base em quais informações revelam:

| Nível | Descrição | Cabeçalhos Enviados | Detectável | Caso de Uso |
|---|---|---|---|---|
| **Transparente** | Revela IP do cliente e uso de proxy | `X-Forwarded-For: IP_DO_CLIENTE`<br/>`Via: PROXY` | Facilmente detectado | Filtragem de conteúdo, cache (não privacidade) |
| **Anônimo** | Esconde IP do cliente mas revela uso de proxy | `X-Forwarded-For: IP_DO_PROXY`<br/>`Via: PROXY` | Proxy detectável, IP oculto | Privacidade básica, contornar geo-bloqueios |
| **Elite (Alta Anonimidade)** | Esconde tanto IP do cliente quanto uso de proxy | Nenhum cabeçalho relacionado a proxy | Difícil de detectar | Privacidade máxima, scraping, tarefas sensíveis |

#### Exemplo de Proxy Transparente

```http
GET /api/data HTTP/1.1
Host: example.com
X-Forwarded-For: 203.0.113.45        ← Seu IP real vazou!
X-Real-IP: 203.0.113.45               ← Também revela IP real
Via: 1.1 proxy.example.com            ← Revela servidor proxy
Forwarded: for=203.0.113.45;by=proxy  ← Formato RFC 7239
```

**Detecção:**
```python
def is_transparent_proxy(headers):
    """Site pode ver seu IP real apesar do proxy."""
    return (
        'X-Forwarded-For' in headers or
        'X-Real-IP' in headers or
        'Via' in headers or
        'Forwarded' in headers
    )
```

#### Exemplo de Proxy Anônimo

```http
GET /api/data HTTP/1.1
Host: example.com
X-Forwarded-For: 198.51.100.10       ← IP do Proxy, não o seu
Via: 1.1 anonymous-proxy              ← Revela uso de proxy
```

**Detecção:**
```python
def is_anonymous_proxy(headers):
    """Site sabe que você está usando um proxy, mas não vê seu IP real."""
    return 'Via' in headers or check_ip_in_proxy_database(client_ip)
```

#### Exemplo de Proxy Elite

```http
GET /api/data HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0 ...
Accept: text/html,application/xhtml+xml
Accept-Language: en-US,en;q=0.9
                                      ← Nenhum cabeçalho relacionado a proxy
```

**Detecção:**
```python
def is_elite_proxy(headers, client_ip):
    """
    Nenhum cabeçalho óbvio de proxy, mas ainda pode ser detectado através de:
    - Bancos de dados de reputação de IP
    - Fingerprinting de TCP/IP
    - Fingerprinting de TLS
    - Análise comportamental
    """
    return (
        ip_in_datacenter(client_ip) or
        tcp_fingerprint_mismatch(headers) or
        suspicious_connection_pattern()
    )
```

!!! info "Nível de Anonimato na Prática"

    - **Proxies transparentes** são usados para filtragem corporativa, não privacidade
    - **Proxies anônimos** protegem seu IP, mas os sites sabem que você está usando um proxy
    - **Proxies elite** são os mais difíceis de detectar, mas não impossíveis (veja técnicas de detecção abaixo)
    
    A maioria dos serviços de proxy comercial oferece proxies anônimos ou elite. Proxies gratuitos são frequentemente transparentes.


### Técnicas de Detecção

Sites empregam vários métodos para detectar o uso de proxy, independentemente do nível de anonimato:

### 1. Reputação do Endereço IP: A Base da Detecção

A análise de reputação de IP é a técnica de detecção de proxy **mais eficaz e amplamente implantada**. Ela utiliza dados publicamente disponíveis (registros ASN, WHOIS, bancos de dados de geolocalização) e inteligência proprietária para categorizar endereços IP.

#### Como Funciona a Reputação de IP

Sites consultam **bancos de dados de reputação de IP** para classificar o tráfego de entrada:

```python
# Sistema simplificado de reputação de IP
def comprehensive_ip_check(ip_address):
    """
    Análise de reputação de IP multicamada combinando múltiplos sinais.
    """
    signals = {}
    
    # 1. Análise de ASN (Número do Sistema Autônomo)
    asn_info = query_asn_database(ip_address)
    signals['asn'] = asn_info['number']  # ex: AS14061 (DigitalOcean)
    signals['as_name'] = asn_info['name']
    signals['as_type'] = classify_asn_type(asn_info)
    
    # 2. Classificação do Tipo de IP
    if signals['as_type'] in ['hosting', 'datacenter', 'cloud']:
        signals['ip_type'] = 'DATACENTER'
        signals['risk_score'] = 90  # Alto risco
    elif signals['as_type'] == 'isp':
        signals['ip_type'] = 'RESIDENTIAL'
        signals['risk_score'] = 20  # Risco mais baixo
    elif signals['as_type'] == 'mobile':
        signals['ip_type'] = 'MOBILE'
        signals['risk_score'] = 15  # Risco mais baixo
    
    # 3. Verificação em Banco de Dados de Proxies Conhecidos
    if ip_in_proxy_database(ip_address):
        signals['known_proxy'] = True
        signals['proxy_provider'] = get_proxy_provider(ip_address)
        signals['risk_score'] = 100  # Bloqueio instantâneo
    
    # 4. Consistência de Geolocalização
    geo = query_geolocation(ip_address)
    signals['country'] = geo['country_code']
    signals['city'] = geo['city']
    signals['lat_long'] = (geo['latitude'], geo['longitude'])
    
    # 5. Dados Históricos de Abuso
    abuse_score = query_abuse_database(ip_address)
    signals['abuse_score'] = abuse_score  # 0-100
    signals['risk_score'] += abuse_score * 0.5
    
    # 6. Contagem de Conexões (Quantos usuários compartilham este IP?)
    connection_count = get_concurrent_connections(ip_address)
    if connection_count > 100:  # Residencial típico: 1-5
        signals['suspicious_connection_count'] = True
        signals['risk_score'] += 30
    
    return signals
```

#### Provedores Comerciais de Reputação de IP

Principais serviços anti-fraude e de detecção de proxy:

| Provedor | Cobertura | Taxa de Detecção | Casos de Uso |
|---|---|---|---|
| **MaxMind GeoIP2** | 4B+ IPs, 99% cobertura | ~85% detecção datacenter | Geolocalização, identificação ISP, tipo de proxy |
| **IPQualityScore** | Pontuação em tempo real | ~95% detecção proxy | Prevenção a fraudes, bloqueio VPN/proxy |
| **IP2Location** | 240+ países | ~80% detecção proxy | Licenciamento de conteúdo, geo-bloqueio |
| **IPQS Proxy Detection** | 10M+ proxies conhecidos | ~99% detecção proxy conhecido | Bloqueio agressivo de proxy |
| **Spur.us** | Foco em IPs anônimos | ~90% detecção VPN/proxy | Segurança, inteligência de ameaças |
| **Shodan/Censys** | Dados de varredura de porta | N/A (inteligência de infra) | Identificando servidores proxy por portas abertas |

**Estrutura de Custos:**

- **Nível gratuito**: MaxMind GeoLite2 (menos preciso, atualizações atrasadas)
- **Nível pago**: $50-500/mês para consultas em tempo real
- **Empresarial**: $5,000+/mês para análise multi-sinal de alto volume

!!! info "Precisão da Detecção"
    **Detecção de IP Datacenter**: ~95%+ de precisão (ASNs bem conhecidos, fácil de classificar)
    **Detecção de proxy Residencial**: ~40-70% de precisão (mais difícil de distinguir de usuários legítimos)
    **Detecção de proxy Móvel**: ~20-40% de precisão (frequentemente indistinguível de usuários móveis reais)
    
    É por isso que proxies residenciais e móveis têm preços premium.

#### Classificação Baseada em ASN

**Números de Sistema Autônomo (ASNs)** são o identificador primário para propriedade de IP:

```python
# Exemplos de classificação de ASN
ASN_CLASSIFICATIONS = {
    # Nuvem/Hospedagem (Alto Risco)
    'AS16509': {'name': 'Amazon AWS', 'type': 'cloud', 'risk': 95},
    'AS14061': {'name': 'DigitalOcean', 'type': 'hosting', 'risk': 95},
    'AS16276': {'name': 'OVH', 'type': 'hosting', 'risk': 95},
    'AS24940': {'name': 'Hetzner', 'type': 'hosting', 'risk': 95},
    
    # Provedores de Proxy (Bloqueio Instantâneo)
    'AS200000': {'name': 'BrightData (Luminati)', 'type': 'proxy', 'risk': 100},
    'AS62240': {'name': 'Smartproxy', 'type': 'proxy', 'risk': 100},
    'AS63023': {'name': 'GTHost (proxy infrastructure)', 'type': 'proxy', 'risk': 100},
    
    # ISPs Residenciais (Baixo Risco)
    'AS7922': {'name': 'Comcast', 'type': 'isp', 'risk': 10},
    'AS209': {'name': 'CenturyLink', 'type': 'isp', 'risk': 10},
    'AS3320': {'name': 'Deutsche Telekom', 'type': 'isp', 'risk': 10},
    
    # Operadoras Móveis (Risco Muito Baixo)
    'AS22394': {'name': 'Cellco Partnership (Verizon Wireless)', 'type': 'mobile', 'risk': 5},
    'AS20057': {'name': 'AT&T Mobility', 'type': 'mobile', 'risk': 5},
}

def get_risk_from_asn(asn):
    """Consulta banco de dados ASN e retorna avaliação de risco."""
    asn_data = ASN_CLASSIFICATIONS.get(asn, {'type': 'unknown', 'risk': 50})
    return asn_data
```

**Ferramentas para consultar ASN:**

- **Comando `whois`**: `whois -h whois.cymru.com " -v 8.8.8.8"`
- **Bibliotecas Python**: `ipwhois`, `pyasn`
- **APIs**: IPInfo.io, IPAPI, AbuseIPDB

#### Bancos de Dados de IP Específicos de Proxy

Bancos de dados especializados rastreiam **infraestrutura de proxy conhecida**:

1.  **APIs de Detecção de Proxy:**
    - **getipintel.net**: API gratuita, banco de dados de proxy crowdsourced
    - **proxycheck.io**: Detecção de proxy em tempo real com SLA de 99.9% de uptime
    - **ipqs.io**: Suíte de detecção de fraudes incluindo pontuação de proxy

2.  **Listas Open-Source:**
    - **Nós de saída Tor**: Listados publicamente (https://check.torproject.org/torbulkexitlist)
    - **Listas públicas de proxy**: Raspadas de fóruns, sites (proxies de baixa qualidade)
    - **Faixas de IP de VPN**: Compiladas de provedores de VPN conhecidos

3.  **Rastreamento Comportamental:**
    - IPs que rotacionam frequentemente (típico de pools de proxy)
    - IPs com padrões de conexão anormais (100+ sessões concorrentes)
    - IPs associados a comportamento semelhante a bot

#### Inconsistências de Geolocalização

Proxies frequentemente se revelam através de **impossibilidades geográficas**:

```python
def check_geolocation_consistency(ip_address, headers, session_data):
    """
    Detecta desencontros de geolocalização que indicam proxy.
    """
    inconsistencies = []
    
    # Geolocalização baseada em IP
    ip_geo = geolocate_ip(ip_address)  # → "US, California, Los Angeles"
    
    # Fuso horário reportado pelo navegador
    browser_tz = headers.get('Timezone')  # → "Europe/Berlin" (do JavaScript)
    expected_tz = get_timezone_for_location(ip_geo)
    if browser_tz != expected_tz:
        inconsistencies.append({
            'type': 'TIMEZONE_MISMATCH',
            'ip_tz': expected_tz,
            'browser_tz': browser_tz,
            'severity': 'HIGH'
        })
    
    # Idioma reportado pelo navegador
    accept_language = headers.get('Accept-Language')  # → "de-DE,de;q=0.9"
    expected_lang = get_common_language(ip_geo)  # → "en-US"
    if not accept_language.startswith(expected_lang[:2]):
        inconsistencies.append({
            'type': 'LANGUAGE_MISMATCH',
            'ip_lang': expected_lang,
            'browser_lang': accept_language,
            'severity': 'MEDIUM'
        })
    
    # Localização da sessão anterior (se usuário tem cookies)
    if session_data.get('last_known_country'):
        prev_country = session_data['last_known_country']
        curr_country = ip_geo['country']
        time_diff = time.time() - session_data['last_seen']
        
        # Viagem impossível: EUA → China em 10 minutos
        if prev_country != curr_country and time_diff < 3600:
            distance_km = calculate_distance(prev_country, curr_country)
            max_possible_speed = distance_km / (time_diff / 3600)  # km/h
            
            if max_possible_speed > 1000:  # Mais rápido que voo comercial
                inconsistencies.append({
                    'type': 'IMPOSSIBLE_TRAVEL',
                    'distance_km': distance_km,
                    'time_minutes': time_diff / 60,
                    'speed_kmh': max_possible_speed,
                    'severity': 'CRITICAL'
                })
    
    return inconsistencies
```

**Indícios comuns de geolocalização:**

- IP dos EUA + `Accept-Language: zh-CN` (idioma chinês)
- IP da Europa + fuso horário: `America/Los_Angeles`
- IP no Brasil + sessão anterior do Japão (2 minutos atrás)

!!! warning "Falsos Positivos"
    Cenários legítimos que disparam alarmes de geolocalização:

    - **Viajantes**: Usuário no aeroporto conectando por VPN
    - **Expatriados**: Expatriado chinês nos EUA usando navegador chinês
    - **Usuários de VPN**: Usuários conscientes da privacidade com VPN legítima
    - **Corporativo**: Funcionário acessando através da VPN da empresa
    
    Sistemas sofisticados usam **pontuação de risco** (risk scoring) em vez de bloqueio binário.

### 2. Análise de Cabeçalho HTTP

```python
# Cabeçalhos que revelam uso de proxy
suspicious_headers = {
    'X-Forwarded-For': 'Indica que requisição passou por proxy',
    'X-Real-IP': 'IP real antes do proxy',
    'Via': 'Identidade do servidor proxy',
    'Forwarded': 'Cabeçalho de proxy padronizado (RFC 7239)',
    'X-Proxy-ID': 'Alguns proxies adicionam isso',
}

# Cabeçalhos ausentes também são suspeitos
expected_headers = [
    'Accept-Language',  # Navegadores reais enviam isso
    'Accept-Encoding',  # Navegadores reais suportam gzip/deflate
    'User-Agent',       # Deve ser realista
]
```

### 3. Fingerprinting de TCP/IP

```python
# Opções TCP podem revelar proxy
def analyze_tcp_fingerprint(packet):
    """
    SOs diferentes têm implementações de pilha TCP diferentes.
    Se o fingerprint TCP não bate com o User-Agent, é suspeito.
    """
    tcp_options = {
        'window_size': packet.tcp.window,
        'mss': packet.tcp.options.mss,
        'window_scale': packet.tcp.options.window_scale,
        'timestamps': packet.tcp.options.timestamp,
        'ttl': packet.ip.ttl,
    }
    
    # Windows 10 Chrome: TTL esperado ~64, Tamanho Janela 8192
    # Mas pacote mostra TTL ~50, Tamanho Janela 65535
    # → Provavelmente proxyado (TTL diminuiu com saltos)
```

### 4. Fingerprinting de TLS

```python
# Fingerprinting de TLS ClientHello (ja3)
def generate_ja3(client_hello):
    """
    ja3 aplica fingerprinting no handshake TLS.
    Proxies podem alterar suítes de cifras ou extensões.
    """
    ja3_string = f"{version},{ciphers},{extensions},{curves},{formats}"
    ja3_hash = md5(ja3_string).hexdigest()
    
    # Comparar contra fingerprints de navegadores conhecidos
    if ja3_hash not in known_browser_fingerprints:
        return 'SUSPICIOUS_TLS'
```

### 5. Verificação de Consistência DNS

```python
# Verificar se Host HTTP bate com DNS reverso
def check_dns_consistency(connection):
    """
    Servidor pode checar se IP de conexão resolve de volta
    para o domínio esperado. Proxies frequentemente falham nessa checagem.
    """
    connecting_ip = connection.remote_ip
    http_host = connection.headers['Host']
    
    # Pesquisa direta
    forward = dns.resolve(http_host)  # → 93.184.216.34
    
    # Pesquisa reversa
    reverse = dns.reverse(connecting_ip)  # → proxy123.example.com
    
    if forward != connecting_ip:
        return 'IP_MISMATCH'  # Provavelmente proxy
```

## Resumo e Pontos Chave

Detecção de proxy é um **processo probabilístico e multicamada** que combina dúzias de sinais para avaliar a probabilidade de uma conexão ser proxyada. Nenhuma técnica única fornece detecção perfeita, mas combinar múltiplos métodos cria uma defesa robusta.

### Dificuldade de Detecção por Tipo de Proxy

| Tipo de Proxy | Dificuldade de Detecção | Métodos Primários de Detecção | Caso de Uso Típico |
|---|---|---|---|
| **HTTP Transparente** | Trivial | Cabeçalhos HTTP (`Via`, `X-Forwarded-For`) | Filtragem corporativa |
| **HTTP Anônimo** | Fácil | Cabeçalhos HTTP + Reputação de IP | Privacidade básica |
| **HTTP Elite** | Médio | Reputação de IP + Fingerprinting TCP/IP | Usuários conscientes da privacidade |
| **SOCKS5 Datacenter** | Médio | Reputação de IP (análise de ASN) | Operadores de bot |
| **Proxies Residenciais** | Difícil | Análise comportamental + padrões de conexão | Scraping profissional |
| **Proxies Móveis** | Muito Difícil | Sinais limitados, principalmente comportamentais | Furtividade premium |
| **Proxies Rotativos** | Difícil | Inconsistências de sessão | Scraping em larga escala |

### Pontuação de Risco Multi-Sinal

Sistemas de detecção modernos atribuem **pontuações de risco** (0-100) em vez de bloquear/permitir binariamente:

```
Pontuação de Risco = 
    (Reputação_IP × 0.4) +
    (Análise_Cabeçalho × 0.2) +
    (Fingerprint_Rede × 0.2) +
    (Pontuação_Comportamental × 0.15) +
    (Verificações_Consistência × 0.05)

if Pontuação_Risco > 80: BLOQUEAR
elif Pontuação_Risco > 60: CAPTCHA
elif Pontuação_Risco > 40: LIMITAR_TAXA
else: PERMITIR
```

**Limiares variam por indústria:**

- **Bancos**: Bloquear em 50+ (muito agressivo)
- **E-commerce**: CAPTCHA em 70+ (moderado)
- **Sites de conteúdo**: Permitir até 80+ (permissivo, depende de anúncios)

### Estratégias de Evasão (Alto Nível)

Para minimizar o risco de detecção:

1.  **Use IPs Residenciais/Móveis**: Mais difíceis de detectar, valem o premium
2.  **Combine Geolocalização**: Garanta que fuso horário, idioma, localidade estejam alinhados com a localização do IP
3.  **Randomize Fingerprints**: Varie parâmetros TCP/IP e TLS (veja módulos de fingerprinting)
4.  **Realismo Comportamental**: Tempo de digitação humano, movimento do mouse (veja **[Contorno de Captcha Comportamental](../../features/advanced/behavioral-captcha-bypass.md)**)
5.  **Persistência de Sessão**: Não rotacione IPs no meio da sessão (levanta suspeita)
6.  **Cabeçalhos HTTP Limpos**: Remova cabeçalhos identificadores de proxy, use `User-Agent` realista
7.  **Monitore Vazamentos**: Teste vazamentos WebRTC, DNS, fuso horário

!!! danger "Detecção é Inevitável"
    Com recursos suficientes, **qualquer proxy pode ser detectado**. O objetivo é:

    - Tornar a detecção **cara** (forçar adversário a usar múltiplos sinais)
    - Tornar a detecção **lenta** (evitar bloqueios instantâneos, misturar-se ao tráfego legítimo)
    - Tornar a detecção **incerta** (criar negação plausível)
    
    Mesmo proxies residenciais de primeira linha alcançam apenas ~70-90% de taxa de sucesso contra sistemas anti-bot sofisticados.

## Leitura Adicional e Referências

### Documentação Relacionada

**Dentro Deste Módulo:**

- **[Proxies HTTP/HTTPS](./http-proxies.md)** - Como proxies HTTP vazam informação por cabeçalhos
- **[Proxies SOCKS](./socks-proxies.md)** - Por que SOCKS5 é mais furtivo que proxies HTTP
- **[Fundamentos de Rede](./network-fundamentals.md)** - Conceitos de TCP/IP, TLS, WebRTC

**Análises Profundas de Fingerprinting:**

- **[Network Fingerprinting](../fingerprinting/network-fingerprinting.md)** - Técnicas de detecção TCP/IP e TLS
- **[Browser Fingerprinting](../fingerprinting/browser-fingerprinting.md)** - Fingerprinting de HTTP/2, Canvas, WebGL
- **[Técnicas de Evasão](../fingerprinting/evasion-techniques.md)** - Como falsificar fingerprints

**Guias Práticos:**

- **[Configuração de Proxy](../../features/configuration/proxy.md)** - Configurando proxies no Pydoll
- **[Contorno de Captcha Comportamental](../../features/advanced/behavioral-captcha-bypass.md)** - Evadindo detecção comportamental
- **[Opções do Navegador](../../features/configuration/browser-options.md)** - Flags e preferências de furtividade

### Recursos Externos

**Reputação de IP e Geolocalização:**

- **MaxMind GeoIP2**: https://www.maxmind.com/en/geoip2-services-and-databases
- **IPQualityScore Proxy Detection**: https://www.ipqualityscore.com/proxy-vpn-tor-detection-service
- **IP2Location**: https://www.ip2location.com/
- **Spur.us (Anonymous IP Detection)**: https://spur.us/
- **AbuseIPDB**: https://www.abuseipdb.com/ (Reputação de IP crowdsourced)

**Bancos de Dados ASN:**

- **Team Cymru IP to ASN Mapping**: https://www.team-cymru.com/ip-asn-mapping
- **RIPE NCC (Registro ASN Europeu)**: https://www.ripe.net/
- **ARIN (Registro ASN Norte-Americano)**: https://www.arin.net/

**Serviços de Detecção de Proxy:**

- **proxycheck.io**: https://proxycheck.io/ (API de detecção de proxy em tempo real)
- **getipintel.net**: http://getipintel.net/ (Detecção de proxy gratuita)
- **IP2Proxy**: https://www.ip2location.com/proxy-detection (Banco de dados comercial de proxy)

**Padrões e RFCs:**

- **RFC 7239**: Forwarded HTTP Extension (cabeçalhos de proxy padronizados)
- **RFC 7231**: HTTP/1.1 - Método CONNECT (tunelamento de proxy)
- **RFC 9000**: QUIC Transport Protocol (impacta proxying HTTP/3)

**Artigos de Pesquisa:**

- "Detecting Proxies in HTTP Traffic" - Vários artigos acadêmicos sobre detecção baseada em ML
- "TCP Fingerprinting for Network Security" - Técnicas usadas para detecção de proxy
- "TLS Fingerprinting at Scale" - Como JA3/JA3S revelam proxies

**Ferramentas para Teste:**

- **Wireshark**: Análise de pacotes para ver o que proxies revelam
- **https://browserleaks.com/ip**: Teste compreensivo de vazamento de proxy
- **https://whoer.net/**: Verificador de anonimato (detecta uso de proxy)
- **https://ipleak.net/**: Testa vazamentos WebRTC, DNS
- **https://check.torproject.org/**: Detecção de Tor (pode testar qualquer proxy)

### Tópicos Avançados (Além Deste Documento)

**Detecção por Machine Learning:**

- Reconhecimento de padrões comportamentais (movimento do mouse, cadência de digitação)
- Análise de tráfego (tempo de requisição, volume, padrões)
- Modelos ensemble combinando 50+ características

**Detecção Baseada em Tempo:**

- Análise de Round-trip time (RTT)
- Fingerprinting de desvio de relógio (clock skew)
- Distribuição de latência da rede

**Análise Comportamental Avançada:**

- Consistência de renderização Canvas/WebGL
- Tempo de execução de JavaScript
- Padrões de uso de API do navegador

**Técnicas Emergentes:**

- Fingerprinting baseado em HTTP/3 e QUIC
- Análise de logs de Certificate Transparency
- Reputação de IP baseada em Blockchain

---