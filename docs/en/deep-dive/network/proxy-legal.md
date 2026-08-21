# Legal and ethical use

Proxies change where your traffic appears to come from, but they do not change what you are allowed to do. This page covers the legal and ethical questions that come with proxies and automated access, so you can make defensible choices. It is general information, not legal advice; laws vary by jurisdiction and situation, so consult qualified counsel for yours.

## A proxy is not permission

An IP address is a technical detail. It does not grant rights. Routing through a proxy does not exempt you from a site's terms of service, its access controls, or the law that applies where you and the site operate. The questions worth asking before automating a site are the same with or without a proxy:

- Does the site's terms of service allow automated access?
- Are you circumventing an access control (a login, a paywall, a block) rather than reading public data?
- Are your request rate and volume something the server can absorb without harm?
- Are you collecting personal data, and do you have a lawful basis to?

## Terms of service and access controls

Many sites prohibit automated access in their terms regardless of IP. Using rotating proxies specifically to defeat a rate limit, a geo-restriction, or an account limit is the kind of circumvention that turns a terms violation into something a court may treat more seriously.

Two themes run through the case law worth knowing (as background, not advice):

- **Public vs gated data.** Scraping data that is publicly available, without authenticating, is generally treated more leniently than accessing data behind a login or an access control you had to get around.
- **Impact matters.** Even public data, scraped aggressively enough to burden or degrade a server, has been treated as a harm in its own right. Volume and effect count, not just whether you technically got in.

## Personal data and privacy

If you collect data about identifiable people, privacy law applies. Under the GDPR, an IP address is personal data, and processing it needs a lawful basis; for scraping, that usually means the legitimate-interests basis, which requires weighing your purpose against the individuals' rights. Similar regimes exist elsewhere (CCPA in California, and others).

Two principles carry most of the weight in practice:

- **Data minimization.** Collect only the fields you actually need. Just because a page exposes emails or addresses does not mean you should store them.
- **Purpose and retention.** Have a clear reason for the data, and delete it when that reason ends.

## Scrape responsibly

Beyond what is legal, a few habits keep your automation from causing harm:

- **Honor `robots.txt`** and any published crawl guidance, even though a proxy would let you ignore it.
- **Rate-limit yourself.** Add delays between requests and cap concurrency per site, so you never approach the load a proxy pool would let you generate.
- **Back off on `429`.** When a server returns Too Many Requests, slow down rather than rotating to a fresh IP to push through.
- **Be identifiable when appropriate.** For research or monitoring, a descriptive User-Agent with a contact address is more defensible than pretending to be a browser.

!!! tip "The defensible position"
    Proxy usage is easiest to stand behind when it is transparent (you can explain why), necessary (a real reason, such as monitoring or research), proportional (methods matched to the need, not excessive), and compliant (within the applicable laws and the site's terms).

## When to stay away

Some targets carry enough risk that a proxy is the wrong tool entirely: banking and financial sites, government portals, healthcare systems (where data-protection rules like HIPAA carry severe penalties), and internal corporate systems governed by their own policies. For these, use authorized access or an official API, not automation dressed up to look like a normal user.

!!! warning "Not legal advice"
    This page is general information for engineers, not legal advice. Whether a specific activity is lawful depends on the jurisdiction, the site, and the details of what you do. Consult qualified legal counsel before deploying automation that could have legal consequences.

## Related

- [Proxies](../../guides/proxies.md): configuring proxies in Pydoll.
- [Network fundamentals](network-fundamentals.md) and [HTTP/HTTPS proxies](http-proxies.md): how the traffic actually flows.
- [RFC 1928](https://tools.ietf.org/html/rfc1928) (SOCKS5) and [RFC 9298](https://datatracker.ietf.org/doc/html/rfc9298) (CONNECT-UDP): the protocol specs behind proxying.
