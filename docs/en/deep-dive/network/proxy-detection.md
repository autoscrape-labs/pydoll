# Proxy Detection and Anonymity

## Introduction: The Arms Race of Detection and Evasion

Proxy detection is a sophisticated **adversarial system** where websites deploy increasingly advanced techniques to identify proxy users, while proxy users and providers develop countermeasures to evade detection. Understanding this arms race is essential for anyone working with browser automation, web scraping, or privacy-focused applications.

This document reveals the technical mechanisms websites use to detect proxy usage, from simple HTTP header analysis to complex behavioral pattern recognition. We'll explore:

- **IP-based detection** (reputation databases, ASN analysis, geolocation inconsistencies)
- **Network-layer fingerprinting** (TCP/IP stack characteristics, TLS ClientHello patterns)
- **Application-layer analysis** (HTTP headers, protocol downgrades, connection patterns)
- **Behavioral detection** (timing analysis, mouse movement, browsing patterns)
- **Consistency checks** (DNS resolution, timezone/locale mismatches)

!!! info "Module Navigation"
    - **[← SOCKS Proxies](./socks-proxies.md)** - Session-layer proxying fundamentals
    - **[← HTTP/HTTPS Proxies](./http-proxies.md)** - Application-layer proxying
    - **[← Network & Security Overview](./index.md)** - Module introduction
    - **[→ Building Proxies](./build-proxy.md)** - Implementation and advanced topics
    
    For in-depth fingerprinting techniques, see **[Network Fingerprinting](../fingerprinting/network-fingerprinting.md)** and **[Browser Fingerprinting](../fingerprinting/browser-fingerprinting.md)**.

### Why Detection Matters

Websites detect proxies for various legitimate and business reasons:

1. **Fraud Prevention**: Preventing account takeover, credential stuffing, payment fraud
2. **Content Licensing**: Enforcing geo-restrictions for licensed content (Netflix, Hulu, sports streaming)
3. **Price Discrimination**: Preventing arbitrage through regional pricing differences
4. **Bot Mitigation**: Blocking automated scraping, data harvesting, scalping bots
5. **Security**: Blocking traffic from known malicious proxy infrastructure
6. **Terms of Service Enforcement**: Preventing ban evasion, multi-accounting

**The Economics:**

- **For websites**: Detection prevents revenue loss (estimated $100B+ annually from bot traffic)
- **For proxy users**: Evasion enables legitimate use cases (privacy, testing, scraping)
- **For proxy providers**: Residential IPs command 10-100x premium over datacenter IPs

!!! danger "No Proxy is Truly Undetectable"
    Even **elite residential proxies** can be detected through sophisticated multi-signal analysis:

    - IP reputation databases now track residential proxy pools
    - Timing analysis detects network latency inconsistencies
    - Behavioral analysis identifies non-human patterns
    - Browser fingerprinting reveals automation frameworks
    
    The goal is to make detection **difficult and expensive**, not impossible. A determined adversary with sufficient resources can detect almost any proxy with high confidence.

## Proxy Detection and Fingerprinting

Websites can detect proxy usage through various techniques. Understanding proxy anonymity levels is crucial for assessing detection risk.

### Proxy Anonymity Levels

Not all proxies provide the same level of anonymity. They are classified into three categories based on what information they reveal:

| Level | Description | Headers Sent | Detectable | Use Case |
|-------|-------------|-------------|------------|----------|
| **Transparent** | Reveals client IP and proxy usage | `X-Forwarded-For: CLIENT_IP`<br/>`Via: PROXY` | Easily detected | Content filtering, caching (not privacy) |
| **Anonymous** | Hides client IP but reveals proxy usage | `X-Forwarded-For: PROXY_IP`<br/>`Via: PROXY` | Proxy detectable, IP hidden | Basic privacy, bypassing geo-blocks |
| **Elite (High Anonymity)** | Hides both client IP and proxy usage | No proxy-related headers | Difficult to detect | Maximum privacy, scraping, sensitive tasks |

#### Transparent Proxy Example

```http
GET /api/data HTTP/1.1
Host: example.com
X-Forwarded-For: 203.0.113.45        ← Your real IP leaked!
X-Real-IP: 203.0.113.45               ← Also reveals real IP
Via: 1.1 proxy.example.com            ← Reveals proxy server
Forwarded: for=203.0.113.45;by=proxy  ← RFC 7239 format
```

**Detection:**
```python
def is_transparent_proxy(headers):
    """Website can see your real IP despite proxy."""
    return (
        'X-Forwarded-For' in headers or
        'X-Real-IP' in headers or
        'Via' in headers or
        'Forwarded' in headers
    )
```

#### Anonymous Proxy Example

```http
GET /api/data HTTP/1.1
Host: example.com
X-Forwarded-For: 198.51.100.10       ← Proxy IP, not yours
Via: 1.1 anonymous-proxy              ← Reveals proxy usage
```

**Detection:**
```python
def is_anonymous_proxy(headers):
    """Website knows you're using a proxy but doesn't see your real IP."""
    return 'Via' in headers or check_ip_in_proxy_database(client_ip)
```

#### Elite Proxy Example

```http
GET /api/data HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0 ...
Accept: text/html,application/xhtml+xml
Accept-Language: en-US,en;q=0.9
                                      ← No proxy-related headers
```

**Detection:**
```python
def is_elite_proxy(headers, client_ip):
    """
    No obvious proxy headers, but can still be detected through:
    - IP reputation databases
    - TCP/IP fingerprinting
    - TLS fingerprinting
    - Behavioral analysis
    """
    return (
        ip_in_datacenter(client_ip) or
        tcp_fingerprint_mismatch(headers) or
        suspicious_connection_pattern()
    )
```

!!! info "Anonymity Level in Practice"

    - **Transparent proxies** are used for corporate filtering, not privacy
    - **Anonymous proxies** protect your IP but websites know you're using a proxy
    - **Elite proxies** are hardest to detect but not impossible (see detection techniques below)
    
    Most commercial proxy services offer anonymous or elite proxies. Free proxies are often transparent.


### Detection Techniques

Websites employ various methods to detect proxy usage, regardless of anonymity level:

### 1. IP Address Reputation: The Foundation of Detection

IP reputation analysis is the **most effective and widely deployed** proxy detection technique. It leverages publicly available data (ASN records, WHOIS, geolocation databases) and proprietary intelligence to categorize IP addresses.

#### How IP Reputation Works

Websites query **IP reputation databases** to classify incoming traffic:

```python
# Simplified IP reputation system
def comprehensive_ip_check(ip_address):
    """
    Multi-layered IP reputation analysis combining multiple signals.
    """
    signals = {}
    
    # 1. ASN (Autonomous System Number) Analysis
    asn_info = query_asn_database(ip_address)
    signals['asn'] = asn_info['number']  # e.g., AS14061 (DigitalOcean)
    signals['as_name'] = asn_info['name']
    signals['as_type'] = classify_asn_type(asn_info)
    
    # 2. IP Type Classification
    if signals['as_type'] in ['hosting', 'datacenter', 'cloud']:
        signals['ip_type'] = 'DATACENTER'
        signals['risk_score'] = 90  # High risk
    elif signals['as_type'] == 'isp':
        signals['ip_type'] = 'RESIDENTIAL'
        signals['risk_score'] = 20  # Lower risk
    elif signals['as_type'] == 'mobile':
        signals['ip_type'] = 'MOBILE'
        signals['risk_score'] = 15  # Lowest risk
    
    # 3. Known Proxy Database Check
    if ip_in_proxy_database(ip_address):
        signals['known_proxy'] = True
        signals['proxy_provider'] = get_proxy_provider(ip_address)
        signals['risk_score'] = 100  # Instant block
    
    # 4. Geolocation Consistency
    geo = query_geolocation(ip_address)
    signals['country'] = geo['country_code']
    signals['city'] = geo['city']
    signals['lat_long'] = (geo['latitude'], geo['longitude'])
    
    # 5. Historical Abuse Data
    abuse_score = query_abuse_database(ip_address)
    signals['abuse_score'] = abuse_score  # 0-100
    signals['risk_score'] += abuse_score * 0.5
    
    # 6. Connection Count (How many users share this IP?)
    connection_count = get_concurrent_connections(ip_address)
    if connection_count > 100:  # Typical residential: 1-5
        signals['suspicious_connection_count'] = True
        signals['risk_score'] += 30
    
    return signals
```

#### Commercial IP Reputation Providers

Major anti-fraud and proxy detection services:

| Provider | Coverage | Detection Rate | Use Cases |
|----------|----------|----------------|-----------|
| **MaxMind GeoIP2** | 4B+ IPs, 99% coverage | ~85% datacenter detection | Geolocation, ISP identification, proxy type |
| **IPQualityScore** | Real-time scoring | ~95% proxy detection | Fraud prevention, VPN/proxy blocking |
| **IP2Location** | 240+ countries | ~80% proxy detection | Content licensing, geo-blocking |
| **IPQS Proxy Detection** | 10M+ known proxies | ~99% known proxy detection | Aggressive proxy blocking |
| **Spur.us** | Focus on anonymous IPs | ~90% VPN/proxy detection | Security, threat intelligence |
| **Shodan/Censys** | Port scan data | N/A (infrastructure intel) | Identifying proxy servers by open ports |

**Cost Structure:**

- **Free tier**: MaxMind GeoLite2 (less accurate, delayed updates)
- **Paid tier**: $50-500/month for real-time queries
- **Enterprise**: $5,000+/month for high-volume, multi-signal analysis

!!! info "Detection Accuracy"
    **Datacenter IP detection**: ~95%+ accuracy (well-known ASNs, easy to classify)  
    **Residential proxy detection**: ~40-70% accuracy (harder to distinguish from legitimate users)  
    **Mobile proxy detection**: ~20-40% accuracy (often indistinguishable from real mobile users)
    
    This is why residential and mobile proxies command premium pricing.

#### ASN-Based Classification

**Autonomous System Numbers (ASNs)** are the primary identifier for IP ownership:

```python
# ASN classification examples
ASN_CLASSIFICATIONS = {
    # Cloud/Hosting (High Risk)
    'AS16509': {'name': 'Amazon AWS', 'type': 'cloud', 'risk': 95},
    'AS14061': {'name': 'DigitalOcean', 'type': 'hosting', 'risk': 95},
    'AS16276': {'name': 'OVH', 'type': 'hosting', 'risk': 95},
    'AS24940': {'name': 'Hetzner', 'type': 'hosting', 'risk': 95},
    
    # Proxy Providers (Instant Block)
    'AS200000': {'name': 'BrightData (Luminati)', 'type': 'proxy', 'risk': 100},
    'AS62240': {'name': 'Smartproxy', 'type': 'proxy', 'risk': 100},
    'AS63023': {'name': 'GTHost (proxy infrastructure)', 'type': 'proxy', 'risk': 100},
    
    # Residential ISPs (Low Risk)
    'AS7922': {'name': 'Comcast', 'type': 'isp', 'risk': 10},
    'AS209': {'name': 'CenturyLink', 'type': 'isp', 'risk': 10},
    'AS3320': {'name': 'Deutsche Telekom', 'type': 'isp', 'risk': 10},
    
    # Mobile Carriers (Very Low Risk)
    'AS22394': {'name': 'Cellco Partnership (Verizon Wireless)', 'type': 'mobile', 'risk': 5},
    'AS20057': {'name': 'AT&T Mobility', 'type': 'mobile', 'risk': 5},
}

def get_risk_from_asn(asn):
    """Query ASN database and return risk assessment."""
    asn_data = ASN_CLASSIFICATIONS.get(asn, {'type': 'unknown', 'risk': 50})
    return asn_data
```

**Tools to query ASN:**

- **`whois` command**: `whois -h whois.cymru.com " -v 8.8.8.8"`
- **Python libraries**: `ipwhois`, `pyasn`
- **APIs**: IPInfo.io, IPAPI, AbuseIPDB

#### Proxy-Specific IP Databases

Specialized databases track **known proxy infrastructure**:

1. **Proxy Detection APIs:**

   - **getipintel.net**: Free API, crowdsourced proxy database
   - **proxycheck.io**: Real-time proxy detection with 99.9% uptime SLA
   - **ipqs.io**: Fraud detection suite including proxy scoring

2. **Open-Source Lists:**

   - **Tor exit nodes**: Publicly listed (https://check.torproject.org/torbulkexitlist)
   - **Public proxy lists**: Scraped from forums, websites (low-quality proxies)
   - **VPN IP ranges**: Compiled from known VPN providers

3. **Behavioral Tracking:**

   - IPs that rotate frequently (typical of proxy pools)
   - IPs with abnormal connection patterns (100+ concurrent sessions)
   - IPs associated with bot-like behavior

#### Geolocation Inconsistencies

Proxies often reveal themselves through **geographic impossibilities**:

```python
def check_geolocation_consistency(ip_address, headers, session_data):
    """
    Detect geolocation mismatches that indicate proxying.
    """
    inconsistencies = []
    
    # IP-based geolocation
    ip_geo = geolocate_ip(ip_address)  # → "US, California, Los Angeles"
    
    # Browser-reported timezone
    browser_tz = headers.get('Timezone')  # → "Europe/Berlin" (from JavaScript)
    expected_tz = get_timezone_for_location(ip_geo)
    if browser_tz != expected_tz:
        inconsistencies.append({
            'type': 'TIMEZONE_MISMATCH',
            'ip_tz': expected_tz,
            'browser_tz': browser_tz,
            'severity': 'HIGH'
        })
    
    # Browser-reported language
    accept_language = headers.get('Accept-Language')  # → "de-DE,de;q=0.9"
    expected_lang = get_common_language(ip_geo)  # → "en-US"
    if not accept_language.startswith(expected_lang[:2]):
        inconsistencies.append({
            'type': 'LANGUAGE_MISMATCH',
            'ip_lang': expected_lang,
            'browser_lang': accept_language,
            'severity': 'MEDIUM'
        })
    
    # Previous session location (if user has cookies)
    if session_data.get('last_known_country'):
        prev_country = session_data['last_known_country']
        curr_country = ip_geo['country']
        time_diff = time.time() - session_data['last_seen']
        
        # Impossible travel: US → China in 10 minutes
        if prev_country != curr_country and time_diff < 3600:
            distance_km = calculate_distance(prev_country, curr_country)
            max_possible_speed = distance_km / (time_diff / 3600)  # km/h
            
            if max_possible_speed > 1000:  # Faster than commercial flight
                inconsistencies.append({
                    'type': 'IMPOSSIBLE_TRAVEL',
                    'distance_km': distance_km,
                    'time_minutes': time_diff / 60,
                    'speed_kmh': max_possible_speed,
                    'severity': 'CRITICAL'
                })
    
    return inconsistencies
```

**Common geolocation tells:**

- US IP + `Accept-Language: zh-CN` (Chinese language)
- Europe IP + timezone: `America/Los_Angeles`
- IP in Brazil + previous session from Japan (2 minutes ago)

!!! warning "False Positives"
    Legitimate scenarios that trigger geolocation alarms:

    - **Travelers**: User at airport connecting through VPN
    - **Expats**: Chinese expat in US using Chinese browser
    - **VPN users**: Privacy-conscious users with legitimate VPN
    - **Corporate**: Employee accessing through company VPN
    
    Sophisticated systems use **risk scoring** rather than binary blocking.

### 2. HTTP Header Analysis

```python
# Headers that reveal proxy usage
suspicious_headers = {
    'X-Forwarded-For': 'Indicates request passed through proxy',
    'X-Real-IP': 'Real IP before proxy',
    'Via': 'Proxy server identity',
    'Forwarded': 'Standardized proxy header (RFC 7239)',
    'X-Proxy-ID': 'Some proxies add this',
}

# Missing headers are suspicious too
expected_headers = [
    'Accept-Language',  # Real browsers send this
    'Accept-Encoding',  # Real browsers support gzip/deflate
    'User-Agent',       # Must be realistic
]
```

### 3. TCP/IP Fingerprinting

```python
# TCP options can reveal proxy
def analyze_tcp_fingerprint(packet):
    """
    Different OS have different TCP stack implementations.
    If TCP fingerprint doesn't match User-Agent, it's suspicious.
    """
    tcp_options = {
        'window_size': packet.tcp.window,
        'mss': packet.tcp.options.mss,
        'window_scale': packet.tcp.options.window_scale,
        'timestamps': packet.tcp.options.timestamp,
        'ttl': packet.ip.ttl,
    }
    
    # Windows 10 Chrome: Expected TTL ~64, Window Size 8192
    # But packet shows TTL ~50, Window Size 65535
    # → Likely proxied (TTL decreased by hops)
```

### 4. TLS Fingerprinting

```python
# TLS ClientHello fingerprinting (ja3)
def generate_ja3(client_hello):
    """
    ja3 fingerprints the TLS handshake.
    Proxies may alter cipher suites or extensions.
    """
    ja3_string = f"{version},{ciphers},{extensions},{curves},{formats}"
    ja3_hash = md5(ja3_string).hexdigest()
    
    # Compare against known browser fingerprints
    if ja3_hash not in known_browser_fingerprints:
        return 'SUSPICIOUS_TLS'
```

### 5. DNS Consistency Check

```python
# Check if HTTP Host matches reverse DNS
def check_dns_consistency(connection):
    """
    Server can check if connecting IP resolves back to expected domain.
    Proxies often fail this check.
    """
    connecting_ip = connection.remote_ip
    http_host = connection.headers['Host']
    
    # Forward lookup
    forward = dns.resolve(http_host)  # → 93.184.216.34
    
    # Reverse lookup
    reverse = dns.reverse(connecting_ip)  # → proxy123.example.com
    
    if forward != connecting_ip:
        return 'IP_MISMATCH'  # Likely proxy
```

## Summary and Key Takeaways

Proxy detection is a **multi-layered, probabilistic process** that combines dozens of signals to assess the likelihood that a connection is proxied. No single technique provides perfect detection, but combining multiple methods creates a robust defense.

### Detection Difficulty by Proxy Type

| Proxy Type | Detection Difficulty | Primary Detection Methods | Typical Use Case |
|------------|----------------------|---------------------------|------------------|
| **Transparent HTTP** | Trivial | HTTP headers (`Via`, `X-Forwarded-For`) | Corporate filtering |
| **Anonymous HTTP** | Easy | HTTP headers + IP reputation | Basic privacy |
| **Elite HTTP** | Medium | IP reputation + TCP/IP fingerprinting | Privacy-conscious users |
| **Datacenter SOCKS5** | Medium | IP reputation (ASN analysis) | Bot operators |
| **Residential Proxies** | Difficult | Behavioral analysis + connection patterns | Professional scraping |
| **Mobile Proxies** | Very Difficult | Limited signals, mostly behavioral | Premium stealth |
| **Rotating Proxies** | Difficult | Session inconsistencies | Large-scale scraping |

### Multi-Signal Risk Scoring

Modern detection systems assign **risk scores** (0-100) rather than binary block/allow:

```
Risk Score = 
    (IP_Reputation × 0.4) +
    (Header_Analysis × 0.2) +
    (Network_Fingerprint × 0.2) +
    (Behavioral_Score × 0.15) +
    (Consistency_Checks × 0.05)

if Risk_Score > 80: BLOCK
elif Risk_Score > 60: CAPTCHA
elif Risk_Score > 40: RATE_LIMIT
else: ALLOW
```

**Thresholds vary by industry:**

- **Banking**: Block at 50+ (very aggressive)
- **E-commerce**: CAPTCHA at 70+ (moderate)
- **Content sites**: Allow up to 80+ (permissive, rely on ads)

### Evasion Strategies (High-Level)

To minimize detection risk:

1. **Use Residential/Mobile IPs**: Hardest to detect, worth the premium
2. **Match Geolocation**: Ensure timezone, language, locale align with IP location
3. **Randomize Fingerprints**: Vary TCP/IP and TLS parameters (see fingerprinting modules)
4. **Behavioral Realism**: Human-like timing, mouse movement (see **[Behavioral Captcha Bypass](../../features/advanced/behavioral-captcha-bypass.md)**)
5. **Session Persistence**: Don't rotate IPs mid-session (raises suspicion)
6. **Clean HTTP Headers**: Remove proxy-identifying headers, use realistic `User-Agent`
7. **Monitor for Leaks**: Test for WebRTC leaks, DNS leaks, timezone leaks

!!! danger "Detection is Inevitable"
    With sufficient resources, **any proxy can be detected**. The goal is to:

    - Make detection **expensive** (force adversary to use multiple signals)
    - Make detection **slow** (avoid instant blocks, blend in with legitimate traffic)
    - Make detection **uncertain** (create plausible deniability)
    
    Even top-tier residential proxies achieve only ~70-90% success rates against sophisticated anti-bot systems.

## Further Reading and References

### Related Documentation

**Within This Module:**

- **[HTTP/HTTPS Proxies](./http-proxies.md)** - How HTTP proxies leak information through headers
- **[SOCKS Proxies](./socks-proxies.md)** - Why SOCKS5 is more stealthy than HTTP proxies
- **[Network Fundamentals](./network-fundamentals.md)** - TCP/IP, TLS, WebRTC concepts

**Fingerprinting Deep Dives:**

- **[Network Fingerprinting](../fingerprinting/network-fingerprinting.md)** - TCP/IP and TLS detection techniques
- **[Browser Fingerprinting](../fingerprinting/browser-fingerprinting.md)** - HTTP/2, Canvas, WebGL fingerprinting
- **[Evasion Techniques](../fingerprinting/evasion-techniques.md)** - How to spoof fingerprints

**Practical Guides:**

- **[Proxy Configuration](../../features/configuration/proxy.md)** - Configuring proxies in Pydoll
- **[Behavioral Captcha Bypass](../../features/advanced/behavioral-captcha-bypass.md)** - Evading behavioral detection
- **[Browser Options](../../features/configuration/browser-options.md)** - Stealth flags and preferences

### External Resources

**IP Reputation and Geolocation:**

- **MaxMind GeoIP2**: https://www.maxmind.com/en/geoip2-services-and-databases
- **IPQualityScore Proxy Detection**: https://www.ipqualityscore.com/proxy-vpn-tor-detection-service
- **IP2Location**: https://www.ip2location.com/
- **Spur.us (Anonymous IP Detection)**: https://spur.us/
- **AbuseIPDB**: https://www.abuseipdb.com/ (Crowdsourced IP reputation)

**ASN Databases:**

- **Team Cymru IP to ASN Mapping**: https://www.team-cymru.com/ip-asn-mapping
- **RIPE NCC (European ASN registry)**: https://www.ripe.net/
- **ARIN (North American ASN registry)**: https://www.arin.net/

**Proxy Detection Services:**

- **proxycheck.io**: https://proxycheck.io/ (Real-time proxy detection API)
- **getipintel.net**: http://getipintel.net/ (Free proxy detection)
- **IP2Proxy**: https://www.ip2location.com/proxy-detection (Commercial proxy database)

**Standards and RFCs:**

- **RFC 7239**: Forwarded HTTP Extension (standardized proxy headers)
- **RFC 7231**: HTTP/1.1 - CONNECT method (proxy tunneling)
- **RFC 9000**: QUIC Transport Protocol (impacts HTTP/3 proxying)

**Research Papers:**

- "Detecting Proxies in HTTP Traffic" - Various academic papers on ML-based detection
- "TCP Fingerprinting for Network Security" - Techniques used for proxy detection
- "TLS Fingerprinting at Scale" - How JA3/JA3S reveal proxies

**Tools for Testing:**

- **Wireshark**: Packet analysis to see what proxies reveal
- **https://browserleaks.com/ip**: Comprehensive proxy leak testing
- **https://whoer.net/**: Anonymity checker (detects proxy usage)
- **https://ipleak.net/**: Tests for WebRTC leaks, DNS leaks
- **https://check.torproject.org/**: Tor detection (can test any proxy)

### Advanced Topics (Beyond This Document)

**Machine Learning Detection:**

- Behavioral pattern recognition (mouse movement, typing cadence)
- Traffic analysis (request timing, volume, patterns)
- Ensemble models combining 50+ features

**Timing-Based Detection:**

- Round-trip time (RTT) analysis
- Clock skew fingerprinting
- Network latency distribution

**Advanced Behavioral Analysis:**

- Canvas/WebGL rendering consistency
- JavaScript execution timing
- Browser API usage patterns

**Emerging Techniques:**

- HTTP/3 and QUIC-based fingerprinting
- Certificate Transparency log analysis
- Blockchain-based IP reputation

---


