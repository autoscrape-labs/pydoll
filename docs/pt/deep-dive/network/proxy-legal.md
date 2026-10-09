# Uso legal e ético

Proxies mudam de onde seu tráfego parece vir, mas não mudam o que você tem permissão de fazer. Esta página cobre as questões legais e éticas que acompanham proxies e o acesso automatizado, para que você possa fazer escolhas defensáveis. É informação geral, não aconselhamento jurídico; as leis variam por jurisdição e situação, então consulte um advogado qualificado para o seu caso.

## Um proxy não é permissão

Um endereço IP é um detalhe técnico. Ele não concede direitos. Rotear através de um proxy não te isenta dos termos de serviço de um site, de seus controles de acesso, nem da lei que se aplica onde você e o site operam. As perguntas que vale fazer antes de automatizar um site são as mesmas com ou sem um proxy:

- Os termos de serviço do site permitem acesso automatizado?
- Você está contornando um controle de acesso (um login, um paywall, um bloqueio) em vez de ler dados públicos?
- A taxa e o volume das suas requisições são algo que o servidor consegue absorver sem dano?
- Você está coletando dados pessoais, e tem uma base legal para isso?

## Termos de serviço e controles de acesso

Muitos sites proíbem acesso automatizado em seus termos independentemente do IP. Usar proxies rotativos especificamente para derrotar um rate limit, uma restrição geográfica, ou um limite de conta é o tipo de contorno que transforma uma violação de termos em algo que um tribunal pode tratar mais seriamente.

Dois temas percorrem a jurisprudência que vale conhecer (como pano de fundo, não como aconselhamento):

- **Dados públicos vs restritos.** Fazer scraping de dados que estão publicamente disponíveis, sem autenticar, é geralmente tratado com mais leniência do que acessar dados atrás de um login ou de um controle de acesso que você teve que contornar.
- **O impacto importa.** Mesmo dados públicos, coletados de forma agressiva o bastante para sobrecarregar ou degradar um servidor, já foram tratados como um dano por si só. O volume e o efeito contam, não apenas se você tecnicamente entrou.

## Dados pessoais e privacidade

Se você coleta dados sobre pessoas identificáveis, a lei de privacidade se aplica. Sob a GDPR, um endereço IP é dado pessoal, e processá-lo precisa de uma base legal; para scraping, isso geralmente significa a base de interesses legítimos, que exige ponderar seu propósito contra os direitos dos indivíduos. Regimes semelhantes existem em outros lugares (CCPA na Califórnia, e outros).

Dois princípios carregam a maior parte do peso na prática:

- **Minimização de dados.** Colete apenas os campos que você de fato precisa. Só porque uma página expõe e-mails ou endereços não significa que você deva armazená-los.
- **Propósito e retenção.** Tenha uma razão clara para os dados, e apague-os quando essa razão terminar.

## Faça scraping de forma responsável

Além do que é legal, alguns hábitos evitam que sua automação cause dano:

- **Honre o `robots.txt`** e qualquer orientação de crawl publicada, mesmo que um proxy te deixasse ignorá-la.
- **Imponha um rate limit a si mesmo.** Adicione atrasos entre requisições e limite a concorrência por site, para que você nunca se aproxime da carga que um pool de proxy te deixaria gerar.
- **Recue no `429`.** Quando um servidor retorna Too Many Requests, desacelere em vez de rotacionar para um IP novo para furar o limite.
- **Seja identificável quando apropriado.** Para pesquisa ou monitoramento, um User-Agent descritivo com um endereço de contato é mais defensável do que fingir ser um navegador.

!!! tip "A posição defensável"
    O uso de proxy é mais fácil de sustentar quando é transparente (você consegue explicar por quê), necessário (uma razão real, como monitoramento ou pesquisa), proporcional (métodos ajustados à necessidade, não excessivos), e em conformidade (dentro das leis aplicáveis e dos termos do site).

## Quando ficar longe

Alguns alvos carregam risco suficiente para que um proxy seja a ferramenta errada por completo: sites de bancos e financeiros, portais de governo, sistemas de saúde (onde regras de proteção de dados como a HIPAA carregam penalidades severas), e sistemas corporativos internos regidos por suas próprias políticas. Para esses, use acesso autorizado ou uma API oficial, não automação disfarçada para parecer um usuário normal.

!!! warning "Não é aconselhamento jurídico"
    Esta página é informação geral para engenheiros, não aconselhamento jurídico. Se uma atividade específica é lícita depende da jurisdição, do site, e dos detalhes do que você faz. Consulte um advogado qualificado antes de implantar automação que possa ter consequências legais.

## Relacionado

- [Proxies](../../guides/proxies.md): configurando proxies no Pydoll.
- [Fundamentos de rede](network-fundamentals.md) e [Proxies HTTP/HTTPS](http-proxies.md): como o tráfego de fato flui.
- [RFC 1928](https://tools.ietf.org/html/rfc1928) (SOCKS5) e [RFC 9298](https://datatracker.ietf.org/doc/html/rfc9298) (CONNECT-UDP): as especificações de protocolo por trás do proxying.
