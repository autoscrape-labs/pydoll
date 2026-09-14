# GPU, containers e o que um perfil não alcança

Um perfil de fingerprint muda o que o navegador *reporta*. Ele não consegue mudar o que o host *computa*. Todo sinal de GPU existe nas duas formas, e a divisão entre elas decide o que um host específico pode alegar, por que um Mac que nomeia a placa de outro vendor é um caso diferente de um container sem GPU, e o que o Xvfb muda e não muda.

Ela aplica a regra de [Os limites do spoofing](spoofing-limits.md), uma string pode ser movida mas a saída renderizada permanece real, a uma única pergunta: que hardware este host pode alegar? Ela expande o [parágrafo sobre containers](../../stealth/fingerprint-injection.md#containers) do guia de injeção.

!!! warning "Tudo aqui depende do alvo"
    Não existe bala de prata. Cada site lê o próprio subconjunto de sinais e o pondera do próprio jeito: os coletores passivos rastreados em [Auditando um fingerprint](auditing.md#what-passive-collectors-read) nunca leem a GPU, enquanto um agente comercial de fingerprinting faz o hash dela. Toda afirmação abaixo na forma "um detector vê X" significa "um detector que lê X vê isso". Antes de gastar com fontes, proxies ou uma instância com GPU, rastreie o que o alvo de fato lê; uma contradição que ninguém lê não custa nada, e um sinal em que você nunca pensou pode ser o que decide.

## Reportado e computado

| Camada | Exemplos | Alcançada pelo perfil |
|---|---|---|
| Reportada | string do renderer, limites e extensões do WebGL, precisão de shader, `adapter.info`, limites e features do WebGPU | sim: as seções `webgl` e `webgpu` a substituem |
| Computada | pixels renderizados (o hash de uma cena de teste), resultados de compute, o tempo deles, a checagem de contexto sem caveat | não: o hardware a executa |

A camada reportada é substituída nos prototypes reais com os brand checks nativos intactos (veja [Injeção de fingerprint](../../stealth/fingerprint-injection.md#native-first)). A camada computada é o que [Os limites do spoofing](spoofing-limits.md) chama de piso intransponível: um hash de renderização é o hash dos pixels que uma cena de teste desenha, e a checagem sem caveat é `getContext('webgl', {failIfMajorPerformanceCaveat: true})`, um contexto que o Chrome só concede quando considera o renderizador rápido o bastante.

Um detector que lê apenas a camada reportada vê o que o perfil disser. Um detector que lê a camada computada vê o host. O que ele consegue concluir a partir disso depende do que o host é.

## A GPU de outro vendor: uma aposta nos dados de referência do alvo

Tome o caso medido neste branch: um Apple M4 rodando o perfil de Windows, que nomeia uma placa NVIDIA nas duas seções. A camada reportada é coerente, NVIDIA em todo lugar. A camada computada é uma GPU real: anti-aliasing por hardware, precisão por hardware, uma renderização concluída em tempo de hardware. Por si só, essa saída não diz nada além de "uma GPU desenhou isto". Para transformá-la numa contradição, o detector precisa de uma referência: "uma RTX 3060 no Windows produz o hash X e leva Y milissegundos". Comparada com isso, a saída do M4 não bate.

Só um detector com dados de referência por placa consegue pegar a mentira. A Castle documenta cruzamentos de strings (o renderer contra o OS do User-Agent); uma comparação de hash contra referência é o que um agente comercial de fingerprinting poderia fazer com os hashes de renderização que coleta, e nenhuma fonte pública mostra um fazendo isso por placa. As leituras passivas do reCAPTCHA e do hCaptcha, [rastreadas](auditing.md#what-passive-collectors-read), nunca tocaram WebGL nem WebGPU, e um perfil de Windows neste Mac passou uma vez numa busca digitada no Google.

A saída computada nunca diz "automação" ou "container" por si só, porque é saída de hardware genuíno; headless e headful neste Mac mediram idênticos em todo sinal de GPU. Então um perfil da GPU de outro vendor numa GPU real é uma aposta calibrada: passa em quem lê valores e consistência entre valores, e falha em quem compara a saída renderizada com um banco de dados de placas. O perfil da própria GPU do host é sempre o mais forte, porque as duas camadas concordam sem precisar de referência nenhuma.

## Sem GPU: uma contradição que não precisa de referência

Aqui a camada computada é reconhecível por si só. Sem GPU, o Chrome atual ou não cria contexto WebGL nenhum (o fallback para o SwiftShader foi removido desde o Chrome 139 e precisa de `--enable-unsafe-swiftshader` nas builds atuais) ou renderiza pelo SwiftShader, o rasterizador de CPU do Chrome. Medido no Chrome 152 com a GPU desativada:

- O contexto sem caveat é recusado quando o Chrome caiu para o SwiftShader, o que nenhuma placa dedicada faz. Escolher o SwiftShader explicitamente com `--use-angle=swiftshader` ainda o concede, então isto é o caso sem GPU, não uma propriedade do SwiftShader.
- O hash de renderização é o mesmo em todo Chrome sem GPU da mesma build, seja qual for a CPU, um valor que qualquer detector que mantenha uma tabela deles reconhece.
- Uma cena renderizada leva tempo de CPU: uma cena trivial mediu dezenas de vezes mais lenta do que no M4.
- `navigator.gpu.requestAdapter()` resolve para `null` sem as flags abaixo, então a seção `webgpu` não tem adapter onde ancorar os valores.

Um perfil que nomeia uma placa dedicada num host desses contradiz cada um desses pontos sem que ninguém precise saber o que a placa teria produzido. Essa é a diferença em relação ao Mac: a camada computada do Mac só trai o perfil para um detector com referência; a do container o trai para uma checagem de uma linha.

### Contar uma história de software em vez disso

O que um container realmente é, um navegador renderizado por software, é também o que milhões de sessões reais são. O Windows em desktops virtuais (VDI, Citrix, VMs em nuvem) renderiza pelo Microsoft Basic Render Driver (o rasterizador de CPU do próprio Windows, o WARP), e o Chrome ali reporta um renderer da forma `ANGLE (Microsoft, Microsoft Basic Render Driver (0x0000008C) Direct3D11 vs_5_0 ps_5_0, D3D11-10.0.19041.5794)`. O Chromium classifica o WARP como renderização por software, então um contexto sem caveat recusado e um adapter WebGPU `null` são esperados ali também; esse par ainda precisa ser confirmado numa VM Windows. Renderizadores por software pontuam como suspeitos por si só, mas descrevem máquinas reais; uma placa dedicada num host por software não descreve nenhuma.

Os valores de um perfil assim (limites do WebGL, extensões, a tabela de precisão) têm que ser capturados numa VM Windows real, a mesma regra de todo outro perfil. A lacuna que sobra é o hash de renderização: o SwiftShader e o WARP desenham diferente, então um detector com referência para o WARP ainda vê a diferença. Isso é questão de pontuação, não uma contradição.

### Fazer as APIs existirem

`--enable-unsafe-swiftshader` dá à página um contexto WebGL para ler; um desktop sem WebGL nenhum é mais raro do que um com renderizador por software. `--enable-unsafe-webgpu --use-webgpu-adapter=swiftshader` expõe um adapter WebGPU por software que reporta vendor `google`, architecture `swiftshader` e `adapter.info.isFallbackAdapter` true, para a seção `webgpu` se ancorar (defina `is_fallback_adapter` no perfil com o que o dispositivo alegado reporta, ou a flag continua visível). Juntos, eles dão aos detectores que leem parâmetros e existência algo coerente para ler. Não mudam nada na saída renderizada, e combiná-los com uma alegação de GPU de hardware recria a contradição acima.

## O Xvfb remove os sinais de display, não os de GPU

O Xvfb (um display X virtual sem tela conectada) dá um display ao Chrome, então o navegador roda headful: existe uma superfície apresentada (o termo de apresentação, o sinal do Cloudflare para um navegador desenhando num display real, ponderado num IP marginal em [O managed challenge do Cloudflare](cloudflare-challenge.md)), `screen` é o display virtual que você configura, a janela tem chrome real e barras de rolagem do Linux, e a entrada pode vir do sistema operacional (`xdotool`) em vez do DevTools protocol. Os sinais que vêm de não ter display desaparecem; o que um alvo específico faz com isso é a pontuação dele.

Ele não adiciona GPU nenhuma. O Xvfb é um framebuffer em memória; a renderização continua SwiftShader ou o llvmpipe do Mesa (o rasterizador de CPU do Linux), um renderizador por software igualmente reconhecível na string do renderer. O kernel, as fontes e o IP de saída também não mudam.

## A ordem de valor num servidor

1. **Um IP residencial limpo de saída.** Lido antes de qualquer script rodar, e nada abaixo compensa isso num alvo que pondera reputação de IP, o que é a maioria deles.
2. **Um perfil que combine com o que o host computa.** Num host com GPU, o vendor da própria GPU do host; num host sem GPU, uma história de Windows renderizado por software em vez de uma placa dedicada.
3. **APIs que existem.** As flags do SwiftShader acima, e `--use-fake-device-for-media-stream` para que o próprio Chrome exponha um microfone, uma câmera e um alto-falante.
4. **Fontes do OS alegado instaladas**, e `available_fonts` listando exatamente essas; uma fonte de emoji colorido daquele OS também.
5. **Xvfb** quando o alvo pondera apresentação.
6. **O kernel.** Um SYN de Linux sob um User-Agent de Windows é lido na borda ([Fingerprinting de rede](network-fingerprinting.md)); uma saída de proxy no OS alegado é a única solução limpa, e se um alvo pondera o SYN ainda é uma medição em aberto.
7. **Uma GPU real.** Uma instância com GPU (classe T4/L4) é a única coisa que torna genuínos o hash de renderização, o adapter WebGPU e o timing; com o mesmo vendor que o perfil nomeia, as camadas reportada e computada finalmente concordam.

!!! note "Um modelo, não um veredito"
    O primeiro e o último item são sustentados pela literatura e pelas medições; a ordem do meio depende do alvo. Um site que nunca lê WebGL não é ajudado por uma instância com GPU, e um site que faz o hash dela não é enganado por nada menos do que uma. Meça o alvo primeiro, e espere que dois alvos discordem.

## Relacionado

- [Os limites do spoofing](spoofing-limits.md): a regra geral que esta página aplica ao hardware.
- [Injeção de fingerprint](../../stealth/fingerprint-injection.md): aplicando as seções `webgl` e `webgpu`.
- [Auditando um fingerprint](auditing.md): lendo o que um alvo de fato coleta.
- [O managed challenge do Cloudflare](cloudflare-challenge.md): o termo de apresentação e o caso headless.
