# Fingerprinting

Fingerprinting é como um site identifica um navegador sem cookies ou endereço de IP, lendo características que a própria conexão expõe por conta própria. Isoladamente, cada característica parece inofensiva; combinadas, elas identificam um dispositivo ou uma instância de navegador, e revelam automação quando as peças não se encaixam.

Esta seção é a teoria por trás dos guias de [Stealth](../../stealth/index.md). Você não precisa dela para permanecer indetectável na prática, mas ela explica o que um sistema de detecção realmente mede e por que uma única inconsistência te entrega.

## A detecção acontece em três camadas

Uma requisição é fingerprinted em três níveis, e os sistemas anti-bot modernos correlacionam todos eles:

- **Rede**: a pilha TCP/IP, o handshake TLS e as configurações de HTTP/2, todos lidos antes de qualquer JavaScript rodar.
- **Navegador**: renderização de canvas e WebGL, fontes, áudio e propriedades do `navigator`, lidas assim que a página carrega.
- **Comportamental**: movimento do mouse, ritmo das teclas e padrões de rolagem, lidos conforme você interage.

As camadas são checadas umas contra as outras. Um User-Agent de Chrome sobre um fingerprint TLS de Firefox, ou um fingerprint de navegador impecável com movimento robótico de mouse, é pego por qualquer coisa que compare sinais. A consistência entre as três importa mais do que a perfeição em qualquer uma delas.

!!! note "A regra central"
    Toda camada tem que contar a mesma história. Se o seu fingerprint TLS diz Chrome 120, então as suas configurações de HTTP/2, o seu User-Agent e o seu canvas renderizado também têm que dizer Chrome 120. Uma contradição já basta para marcar a sessão.

## As três camadas em profundidade

- [Network fingerprinting](network-fingerprinting.md): identificação nas camadas de transporte e de sessão, antes da renderização. TCP/IP (TTL, tamanho de janela, ordem das opções), TLS (JA3/JA4, cipher suites, ALPN) e HTTP/2 (SETTINGS, prioridades). A camada mais difícil de mudar, porque vem do sistema operacional e do binário real.
- [Browser fingerprinting](browser-fingerprinting.md): identificação através de APIs JavaScript e da renderização. Artefatos de canvas e WebGL da GPU real, áudio, enumeração de fontes e propriedades do `navigator`. É aqui que a maioria dos eventos de detecção acontece.
- [Behavioral fingerprinting](behavioral-fingerprinting.md): identificação a partir de como você interage. Trajetória e velocidade do mouse, ritmo das teclas e dinâmica de rolagem, às vezes pontuados por modelos treinados em grandes conjuntos de dados comportamentais. Pode pegar automação mesmo quando as outras camadas estão limpas.

## Relacionado

Esta seção explica a detecção. Para o que o Pydoll faz a respeito dela e as alavancas que você controla, veja os guias de Stealth:

- [Evasion techniques](../../stealth/evasion-techniques.md): o que o Pydoll te dá de graça e como manter as camadas consistentes.
- [Fingerprint injection](../../stealth/fingerprint-injection.md): aplicar uma identidade coerente entre as camadas.
- [Human-like interactions](../../stealth/human-like-interactions.md): a camada comportamental.

!!! warning "Nenhuma camada te torna indetectável"
    O conhecimento sobre fingerprinting reduz a distância; ele não a elimina. Acertar uma camada enquanto outra a contradiz é pior do que um navegador não modificado. Use isso para entender o que você está enfrentando, não como uma garantia.
