# Network and proxies

Proxies are how you change where your traffic appears to come from, and how it looks on the wire. Getting them right (and understanding how they get caught) means knowing what actually happens at each layer of a request. This section is the background; for setting a proxy in Pydoll, see the [Proxies](../../guides/proxies.md) guide.

## Start here

- [Network fundamentals](network-fundamentals.md): the layers a request passes through, from TCP to TLS to HTTP, and which layer a proxy can reach.

## Proxy types

- [HTTP/HTTPS proxies](http-proxies.md): the forward proxy and the CONNECT tunnel, what each can see, and how MITM interception changes the TLS fingerprint.
- [SOCKS proxies](socks-proxies.md): the transport-layer handshake, SOCKS4 vs SOCKS5, remote DNS, and Chrome's SOCKS5 auth limitation.

## Detection and mechanics

- [Proxy detection](proxy-detection.md): the signals that give a proxy away, from IP reputation to header and fingerprint mismatches.
- [Building a proxy server](build-proxy.md): a minimal HTTP and SOCKS5 proxy in Python, to see how forwarding actually works.
- [Legal and ethical use](proxy-legal.md): terms of service, privacy, and responsible scraping.

## Related

- [Proxies](../../guides/proxies.md): the practical guide to configuring proxies in Pydoll.
- [Network fingerprinting](../fingerprinting/network-fingerprinting.md): what the network layer reveals about a client.
