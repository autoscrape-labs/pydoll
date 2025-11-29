# Preferências Personalizadas do Navegador

Uma das funcionalidades mais poderosas do Pydoll é o acesso direto ao sistema interno de preferências do Chromium. Diferente das ferramentas tradicionais de automação de navegador que expõem apenas um conjunto limitado de opções, o Pydoll oferece o mesmo nível de controle que extensões e administradores corporativos têm, permitindo que você configure **qualquer** configuração de navegador disponível no código-fonte do Chromium.

## Por que as Preferências do Navegador Importam

As preferências do navegador controlam cada aspecto de como o Chromium se comporta:

- **Desempenho**: Desabilite recursos que você não precisa para carregamentos de página mais rápidos
- **Privacidade**: Controle quais dados o navegador coleta e envia
- **Automação**: Remova prompts e confirmações do usuário que quebram fluxos de trabalho
- **Furtividade (Stealth)**: Crie fingerprints de navegador realistas para evitar detecção
- **Corporativo**: Aplique políticas tipicamente disponíveis apenas através de Política de Grupo (Group Policy)

!!! info "O Poder do Acesso Direto"
    A maioria das ferramentas de automação expõe apenas 10-20 configurações comuns. O Pydoll lhe dá acesso a **centenas** de preferências, desde o comportamento de download até sugestões de busca, da predição de rede ao gerenciamento de plugins. Se o Chromium pode fazer, você pode configurar.

## Guia Rápido

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def preferences_example():
    options = ChromiumOptions()
    
    # Definir preferências usando um dict
    options.browser_preferences = {
        'download': {
            'default_directory': '/tmp/downloads',
            'prompt_for_download': False
        },
        'profile': {
            'default_content_setting_values': {
                'notifications': 2  # Bloquear notificações
            }
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Downloads vão para /tmp/downloads automaticamente
        # Nenhum prompt de notificação aparecerá

asyncio.run(preferences_example())
```

## Entendendo as Preferências do Navegador

### O que são Preferências?

O Chromium armazena todas as configurações configuráveis pelo usuário em um arquivo JSON chamado `Preferences`, localizado no diretório de dados do usuário do navegador. Este arquivo contém **tudo**, desde a URL da sua página inicial até se as imagens carregam automaticamente.

**Localização típica:**

- **Linux**: `~/.config/google-chrome/Default/Preferences`
- **macOS**: `~/Library/Application Support/Google/Chrome/Default/Preferences`
- **Windows**: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Preferences`

### Estrutura do Arquivo de Preferências

O arquivo Preferences é um objeto JSON aninhado:

```json
{
  "download": {
    "default_directory": "/home/user/Downloads",
    "prompt_for_download": true
  },
  "profile": {
    "default_content_setting_values": {
      "notifications": 1,
      "popups": 0
    },
    "password_manager_enabled": true
  },
  "search": {
    "suggest_enabled": true
  },
  "net": {
    "network_prediction_options": 1
  }
}
```

Cada nome de preferência separado por pontos no código-fonte do Chromium mapeia para um caminho JSON aninhado:

- `download.default_directory` → `{'download': {'default_directory': ...}}`
- `profile.password_manager_enabled` → `{'profile': {'password_manager_enabled': ...}}`

### Como o Chromium Usa as Preferências

Quando o Chromium inicia:

1.  **Lê** o arquivo Preferences do disco
2.  **Aplica** essas configurações para configurar o comportamento do navegador
3.  **Atualiza** o arquivo quando os usuários alteram configurações via UI
4.  **Recorre aos padrões** se as preferências estiverem ausentes

O Pydoll intercepta o passo 1 pré-populando o arquivo Preferences antes do navegador iniciar, garantindo que suas configurações personalizadas sejam aplicadas desde o primeiro carregamento da página.

## Como Funciona no Pydoll

### Definindo Preferências

Use a propriedade `browser_preferences` para definir qualquer preferência:

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()

# Atribuição direta - mescla com preferências existentes
options.browser_preferences = {
    'download': {'default_directory': '/tmp'},
    'intl': {'accept_languages': 'pt-BR,en-US'}
}

# Múltiplas atribuições são mescladas, não substituídas
options.browser_preferences = {
    'profile': {'password_manager_enabled': False}
}

# Ambos os conjuntos de preferências estão agora ativos
```

!!! warning "Preferências São Mescladas, Não Substituídas"
    Quando você define `browser_preferences` múltiplas vezes, as novas preferências são **mescladas** com as existentes. Apenas as chaves específicas que você define são atualizadas; todo o resto é preservado.
    
    ```python
    options.browser_preferences = {'download': {'prompt': False}}
    options.browser_preferences = {'profile': {'password_manager_enabled': False}}
    
    # Resultado: AMBAS as preferências são definidas
    # {'download': {'prompt': False}, 'profile': {'password_manager_enabled': False}}
    ```

### Sintaxe de Caminho Aninhado

As preferências usam dicionários aninhados que espelham a notação de pontos do Chromium:

```python
# Constante do código-fonte do Chromium:
# const char kDownloadDefaultDirectory[] = "download.default_directory";

# Traduz para dict Python:
options.browser_preferences = {
    'download': {
        'default_directory': '/path/to/downloads'
    }
}
```

Quanto mais profundo o aninhamento, mais específica a preferência:

```python
# Nível superior: profile
# Segundo nível: default_content_setting_values  
# Terceiro nível: notifications

options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            'notifications': 2,  # Bloquear
            'geolocation': 2,    # Bloquear
            'media_stream': 2    # Bloquear
        }
    }
}
```

## Casos de Uso Práticos

### 1. Otimização de Desempenho

Desabilite recursos que consomem muitos recursos para automação mais rápida:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def performance_optimized_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        # Desabilitar predição de rede e prefetching
        'net': {
            'network_prediction_options': 2  # 2 = Nunca prever
        },
        # Desabilitar carregamento de imagens
        'profile': {
            'default_content_setting_values': {
                'images': 2  # 2 = Bloquear, 1 = Permitir
            }
        },
        # Desabilitar plugins
        'webkit': {
            'webprefs': {
                'plugins_enabled': False
            }
        },
        # Desabilitar verificação ortográfica
        'browser': {
            'enable_spellchecking': False
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Páginas carregam 3-5x mais rápido sem imagens e recursos desnecessários
        await tab.go_to('https://example.com')
        print("Carregamento rápido completo!")

asyncio.run(performance_optimized_browser())
```

!!! tip "Impacto no Desempenho"
    Apenas desabilitar imagens pode reduzir o tempo de carregamento da página em 50-70% para sites pesados em imagens. Combine com a desabilitação de prefetch, verificação ortográfica e plugins para velocidade máxima.

### 2. Privacidade e Anti-Rastreamento

Crie uma configuração de navegador focada em privacidade:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def privacy_focused_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        # Habilitar Do Not Track
        'enable_do_not_track': True,
        
        # Desabilitar referrers
        'enable_referrers': False,
        
        # Desabilitar Safe Browsing (envia URLs para o Google)
        'safebrowsing': {
            'enabled': False
        },
        
        # Desabilitar gerenciador de senhas
        'profile': {
            'password_manager_enabled': False
        },
        
        # Desabilitar preenchimento automático
        'autofill': {
            'enabled': False,
            'profile_enabled': False
        },
        
        # Desabilitar sugestões de busca (envia consultas para o motor de busca)
        'search': {
            'suggest_enabled': False
        },
        
        # Desabilitar telemetria e métricas
        'user_experience_metrics': {
            'reporting_enabled': False
        },
        
        # Bloquear cookies de terceiros
        'profile': {
            'block_third_party_cookies': True,
            'cookie_controls_mode': 1
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        print("Navegador focado em privacidade pronto!")

asyncio.run(privacy_focused_browser())
```

### 3. Downloads Silenciosos

Automatize downloads de arquivos sem interação do usuário:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def silent_download_automation():
    download_dir = Path.home() / 'automation_downloads'
    download_dir.mkdir(exist_ok=True)
    
    options = ChromiumOptions()
    options.browser_preferences = {
        'download': {
            'default_directory': str(download_dir),
            'prompt_for_download': False,
            'directory_upgrade': True
        },
        'profile': {
            'default_content_setting_values': {
                'automatic_downloads': 1  # 1 = Permitir, 2 = Bloquear
            }
        },
        # Sempre baixar PDFs em vez de abrir no visualizador
        'plugins': {
            'always_open_pdf_externally': True
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/downloads')
        
        # Clicar em links de download - arquivos salvam automaticamente
        download_link = await tab.find(text='Download Report')
        await download_link.click()
        
        await asyncio.sleep(3)
        print(f"Arquivo baixado para: {download_dir}")

asyncio.run(silent_download_automation())
```

### 4. Bloquear Elementos de UI Intrusivos

Remova popups, notificações e prompts que quebram a automação:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def clean_ui_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        'profile': {
            'default_content_setting_values': {
                'notifications': 2,      # Bloquear notificações
                'popups': 0,             # Bloquear popups
                'geolocation': 2,        # Bloquear requisições de localização
                'media_stream': 2,       # Bloquear acesso à câmera/microfone
                'media_stream_mic': 2,   # Bloquear microfone
                'media_stream_camera': 2 # Bloquear câmera
            }
        },
        # Desabilitar prompts de tradução
        'translate': {
            'enabled': False
        },
        # Desabilitar prompt de salvar senha
        'credentials_enable_service': False,
        
        # Desabilitar infobar "O Chrome está sendo controlado por automação"
        'devtools': {
            'preferences': {
                'currentDockState': '"undocked"'
            }
        }
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        # Sem popups, sem prompts, automação limpa!

asyncio.run(clean_ui_browser())
```

### 5. Internacionalização e Localização

Configure preferências de idioma e localidade:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def localized_browser():
    options = ChromiumOptions()
    options.browser_preferences = {
        # Idiomas aceitos (ordem de prioridade)
        'intl': {
            'accept_languages': 'pt-BR,pt,en-US,en'
        },
        
        # Idiomas da verificação ortográfica
        'spellcheck': {
            'dictionaries': ['pt-BR', 'en-US']
        },
        
        # Configurações de tradução
        'translate': {
            'enabled': True
        },
        'translate_blocked_languages': ['en'],  # Não oferecer para traduzir Inglês
        
        # Codificação de caracteres padrão
        'default_charset': 'UTF-8'
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        # Navegador configurado para Português do Brasil

asyncio.run(localized_browser())
```

## Métodos Auxiliares

Para cenários comuns, o Pydoll fornece métodos de conveniência:

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()

# Gerenciamento de download
options.set_default_download_directory('/tmp/downloads')
options.prompt_for_download = False
options.allow_automatic_downloads = True
options.open_pdf_externally = True

# Bloqueio de conteúdo
options.block_notifications = True
options.block_popups = True

# Privacidade
options.password_manager_enabled = False

# Internacionalização
options.set_accept_languages('pt-BR,en-US,en')
```

Esses métodos são atalhos que definem as preferências aninhadas corretas para você:

```python
# Este auxiliar:
options.set_default_download_directory('/tmp')

# É equivalente a:
options.browser_preferences = {
    'download': {
        'default_directory': '/tmp'
    }
}
```

!!! tip "Combine Auxiliares com Preferências Diretas"
    Use auxiliares para configurações comuns e `browser_preferences` para configurações avançadas:
    
    ```python
    # Comece com auxiliares
    options.block_notifications = True
    options.prompt_for_download = False
    
    # Adicione preferências avançadas
    options.browser_preferences = {
        'net': {'network_prediction_options': 2},
        'webkit': {'webprefs': {'plugins_enabled': False}}
    }
    ```

## Encontrando Preferências no Código-Fonte do Chromium

### Referência do Código-Fonte

O Chromium define todas as constantes de preferência em `pref_names.cc`:

**Fonte oficial**: [chromium/src/+/main/chrome/common/pref_names.cc](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.cc)

### Lendo o Código-Fonte

As constantes de preferência usam notação de pontos que mapeia diretamente para dicts aninhados:

```cpp
// Do código-fonte do Chromium (pref_names.cc):
const char kDownloadDefaultDirectory[] = "download.default_directory";
const char kPromptForDownload[] = "download.prompt_for_download";
const char kSafeBrowsingEnabled[] = "safebrowsing.enabled";
const char kBlockThirdPartyCookies[] = "profile.block_third_party_cookies";
```

**Converte para Python:**

```python
options.browser_preferences = {
    'download': {
        'default_directory': '/path/to/dir',
        'prompt_for_download': False
    },
    'safebrowsing': {
        'enabled': False
    },
    'profile': {
        'block_third_party_cookies': True
    }
}
```

### Processo de Descoberta

1.  **Pesquise no código-fonte**: Vá para [pref_names.cc](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.cc)
2.  **Encontre sua preferência**: Pesquise por palavras-chave (ex: "download", "password", "notification")
3.  **Anote o nome da constante**: ex: `kDownloadDefaultDirectory[] = "download.default_directory"`
4.  **Converta para dict**: Divida pelos pontos e crie a estrutura aninhada

**Exemplo - Encontrando preferências de notificação:**

```cpp
// Pesquise por "notification" em pref_names.cc:
const char kPushMessagingAppIdentifierMap[] = 
    "gcm.push_messaging_application_id_map";
const char kDefaultNotificationsSetting[] = 
    "profile.default_content_setting_values.notifications";
```

```python
# Torna-se:
options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            'notifications': 2  # 2 = bloquear, 1 = permitir, 0 = perguntar
        }
    }
}
```

### Padrões Comuns de Preferência

| Categoria | Exemplo de Constante | Caminho do Dict Python |
|---|---|---|
| Downloads | `download.default_directory` | `{'download': {'default_directory': ...}}` |
| Config. de Conteúdo | `profile.default_content_setting_values.X` | `{'profile': {'default_content_setting_values': {'X': ...}}}` |
| Rede | `net.network_prediction_options` | `{'net': {'network_prediction_options': ...}}` |
| Privacidade | `safebrowsing.enabled` | `{'safebrowsing': {'enabled': ...}}` |
| Sessão | `session.restore_on_startup` | `{'session': {'restore_on_startup': ...}}` |

!!! warning "Preferências Não Documentadas"
    Nem todas as preferências estão documentadas. Algumas são:
    
    - **Experimentais**: Podem mudar ou ser removidas em futuras versões do Chromium
    - **Internas**: Usadas pelos sistemas internos do Chromium
    - **Específicas da plataforma**: Funcionam apenas em certos sistemas operacionais
    
    Teste exaustivamente antes de confiar em preferências não documentadas.

## Referência de Preferências Úteis

Aqui está uma lista selecionada de preferências interessantes e úteis do `pref_names.cc` do Chromium:

### Configurações de Conteúdo e Mídia

```python
options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            # Controle de conteúdo (0=perguntar, 1=permitir, 2=bloquear)
            'cookies': 1,                    # Permitir cookies
            'images': 1,                     # Permitir imagens (2 para bloquear)
            'javascript': 1,                 # Permitir JavaScript (2 para bloquear)
            'plugins': 2,                    # Bloquear plugins (Flash, etc.)
            'popups': 0,                     # Bloquear popups
            'geolocation': 2,                # Bloquear requisições de localização
            'notifications': 2,              # Bloquear notificações
            'media_stream': 2,               # Bloquear câmera/microfone
            'media_stream_mic': 2,           # Bloquear apenas microfone
            'media_stream_camera': 2,        # Bloquear apenas câmera
            'automatic_downloads': 1,        # Permitir downloads automáticos
            'midi_sysex': 2,                 # Bloquear acesso MIDI
            'clipboard': 1,                  # Permitir acesso à área de transferência
            'sensors': 2,                    # Bloquear sensores de movimento
            'usb_guard': 2,                  # Bloquear acesso a dispositivos USB
            'serial_guard': 2,               # Bloquear acesso à porta serial
            'bluetooth_guard': 2,            # Bloquear Bluetooth
            'file_system_write_guard': 2,    # Bloquear escrita no sistema de arquivos
        }
    }
}
```

### Rede e Desempenho

```python
options.browser_preferences = {
    'net': {
        # Predição de rede: 0=sempre, 1=apenas wifi, 2=nunca
        'network_prediction_options': 2,
        
        # Verificação rápida de alcançabilidade do servidor
        'quick_check_enabled': False
    },
    
    # Prefetching de DNS
    'dns_prefetching': {
        'enabled': False  # Desabilitar para reduzir tráfego de rede
    },
    
    # Pré-conectar a resultados de busca
    'search': {
        'suggest_enabled': False,           # Desabilitar sugestões de busca
        'instant_enabled': False            # Desabilitar resultados instantâneos
    },
    
    # Páginas de erro alternativas
    'alternate_error_pages': {
        'enabled': False  # Não sugerir alternativas para 404s
    }
}
```

### Preferências de Download

```python
options.browser_preferences = {
    'download': {
        'default_directory': '/path/to/downloads',
        'prompt_for_download': False,
        'directory_upgrade': True,
        'extensions_to_open': '',           # Tipos de arquivo para abrir automaticamente
        'open_pdf_externally': True,        # Não usar o visualizador de PDF interno
    },
    
    'download_bubble': {
        'partial_view_enabled': True        # Mostrar balão de progresso do download
    },
    
    'safebrowsing': {
        'enabled': False  # Desabilitar avisos de download do Safe Browsing
    }
}
```

### Privacidade e Segurança

```python
options.browser_preferences = {
    # Do Not Track
    'enable_do_not_track': True,
    
    # Referrers
    'enable_referrers': False,
    
    # Safe Browsing
    'safebrowsing': {
        'enabled': False,                   # Desabilitar Safe Browsing
        'enhanced': False                   # Desabilitar proteção avançada
    },
    
    # Privacy Sandbox (substituto de cookies do Google)
    'privacy_sandbox': {
        'apis_enabled': False,
        'topics_enabled': False,
        'fledge_enabled': False
    },
    
    # Cookies de terceiros
    'profile': {
        'block_third_party_cookies': True,
        'cookie_controls_mode': 1,          # Bloquear terceiros no modo anônimo
        
        # Configurações de conteúdo
        'default_content_setting_values': {
            'cookies': 1,
            'third_party_cookie_blocking_enabled': True
        }
    },
    
    # WebRTC (pode vazar IP real)
    'webrtc': {
        'ip_handling_policy': 'default_public_interface_only',
        'multiple_routes_enabled': False,
        'nonproxied_udp_enabled': False
    }
}
```

### Preenchimento Automático e Senhas

```python
options.browser_preferences = {
    'autofill': {
        'enabled': False,                   # Desabilitar preenchimento automático de formulários
        'profile_enabled': False,           # Desabilitar preenchimento automático de endereço
        'credit_card_enabled': False,       # Desabilitar preenchimento automático de cartão de crédito
        'credit_card_fido_auth_enabled': False
    },
    
    'profile': {
        'password_manager_enabled': False,
        'password_manager_leak_detection': False
    },
    
    'credentials_enable_service': False,
    'credentials_enable_autosignin': False
}
```

### Comportamento do Navegador e UI

```python
import time

options.browser_preferences = {
    # Página inicial e inicialização
    'homepage': 'https://www.google.com',
    'homepage_is_newtabpage': False,
    'newtab_page_location_override': 'https://www.google.com',
    
    'session': {
        'restore_on_startup': 1,            # 0=nova aba, 1=restaurar, 4=URLs específicas, 5=página nova aba
        'startup_urls': ['https://www.google.com'],
        'session_data_status': 3            # Status dos dados da sessão (interno)
    },
    
    # Página de boas-vindas e janela
    'browser': {
        'has_seen_welcome_page': True,      # Pular tela de boas-vindas
        'window_placement': {
            'bottom': 1032,                 # Posição inferior da janela
            'left': 2247,                   # Posição esquerda da janela
            'right': 3192,                  # Posição direita da janela
            'top': 31,                      # Posição superior da janela
            'maximized': False,             # Janela está maximizada
            'work_area_bottom': 1080,       # Área de trabalho inferior da tela
            'work_area_left': 1920,         # Área de trabalho esquerda da tela
            'work_area_right': 3840,        # Área de trabalho direita da tela
            'work_area_top': 0              # Área de trabalho superior da tela
        }
    },
    
    # Extensões
    'extensions': {
        'ui': {
            'developer_mode': False
        },
        'alerts': {
            'initialized': True
        },
        'theme': {
            'system_theme': 2               # 0=padrão, 1=claro, 2=escuro
        },
        'last_chrome_version': '130.0.6723.91'  # Deve corresponder à sua versão
    },
    
    # Tradução
    'translate': {
        'enabled': False                    # Desabilitar prompts de tradução
    },
    'translate_blocked_languages': ['en'],  # Nunca oferecer para traduzir Inglês
    'translate_site_blacklist': [],         # Legado (use blocklist_with_time)
    
    # Barra de favoritos
    'bookmark_bar': {
        'show_on_all_tabs': False
    },
    
    # Abas
    'tabs': {
        'new_tab_position': 0               # 0=à direita, 1=após atual
    },
    'pinned_tabs': [],                      # Lista de URLs de abas fixadas
    
    # Página Nova Aba (timestamps em formato Chrome)
    'NewTabPage': {
        'PrevNavigationTime': str(int(time.time() * 1000000) + 11644473600000000)  # Timestamp do Chrome
    },
    'ntp': {
        'num_personal_suggestions': 6       # Número de sugestões (0-10)
    },
    
    # Personalização da barra de ferramentas
    'toolbar': {
        'pinned_chrome_labs_migration_complete': True
    }
}
```

!!! info "Formato de Timestamp do Chrome"
    O Chrome usa o formato Windows FILETIME: microssegundos desde 1º de janeiro de 1601 UTC.
    
    Converter timestamp do Python:
    ```python
    import time
    chrome_time = int(time.time() * 1000000) + 11644473600000000
    ```

### Ortografia e Idioma

```python
options.browser_preferences = {
    'browser': {
        'enable_spellchecking': False       # Desabilitar verificação ortográfica
    },
    
    'spellcheck': {
        'dictionaries': ['en-US', 'pt-BR'], # Idiomas da verificação ortográfica
        'dictionary': '',                   # Preferência legada (manter vazio)
        'use_spelling_service': False       # Não enviar ao Google
    },
    
    'intl': {
        'accept_languages': 'pt-BR,pt,en-US,en',
        'selected_languages': 'pt-BR,pt,en-US,en'  # Selecionados explicitamente
    },
    
    # Comportamento e histórico de tradução
    'translate': {
        'enabled': True
    },
    'translate_accepted_count': {
        'pt-BR': 0,
        'es': 5                             # Aceitou 5 traduções de espanhol
    },
    'translate_denied_count_for_language': {
        'en': 10                            # Nunca traduzir inglês
    },
    'translate_ignored_count_for_language': {
        'en': 1
    },
    'translate_site_blocklist_with_time': {},  # Sites para nunca traduzir
    
    # Idioma das legendas de acessibilidade
    'accessibility': {
        'captions': {
            'live_caption_language': 'pt-BR'
        }
    },
    
    # Contadores do modelo de idioma (estatísticas de uso)
    'language_model_counters': {
        'en': 2,                            # Contagem de palavras em inglês
        'pt': 10                            # Contagem de palavras em português
    }
}
```

!!! info "Contadores do Modelo de Idioma"
    Esses contadores rastreiam estatísticas de uso de idioma para os modelos de aprendizado de máquina do Chrome:
    
    - Usados para prever as preferências de idioma do usuário
    - Afeta sugestões de busca e autocompletar
    - Contagens mais altas indicam uso mais frequente
    - Valores realistas: 0-1000 para uso ocasional, 1000+ para uso intenso

### Acessibilidade

```python
options.browser_preferences = {
    'accessibility': {
        'image_labels_enabled': False       # Não obter legendas de imagem do Google
    },
    
    # Configurações de fonte
    'webkit': {
        'webprefs': {
            'default_font_size': 16,
            'default_fixed_font_size': 13,
            'minimum_font_size': 0,
            'minimum_logical_font_size': 6,
            'fonts': {
                'standard': {
                    'Zyyy': 'Arial'
                },
                'serif': {
                    'Zyyy': 'Times New Roman'
                }
            }
        }
    }
}
```

### Mídia e Áudio

```python
options.browser_preferences = {
    # Áudio
    'audio': {
        'mute_enabled': False               # Iniciar com áudio ligado/desligado
    },
    
    # Autoplay
    'media': {
        'autoplay_policy': 0,               # 0=permitir, 1=gesto do usuário, 2=ativação do usuário no documento
        'video_fullscreen_orientation_lock': False
    },
    
    # WebGL
    'webkit': {
        'webprefs': {
            'webgl_enabled': True,          # Habilitar/desabilitar WebGL
            'webgl2_enabled': True
        }
    }
}
```

### Impressão

```python
options.browser_preferences = {
    'printing': {
        'print_preview_sticky_settings': {
            'appState': '{\"version\":2,\"recentDestinations\":[{\"id\":\"Save as PDF\",\"origin\":\"local\"}],\"marginsType\":3,\"customMargins\":{\"marginTop\":63,\"marginRight\":192,\"marginBottom\":240,\"marginLeft\":260}}'
        }
    },
    
    'savefile': {
        'default_directory': '/tmp'         # Local padrão para salvar PDFs
    }
}
```

!!! tip "Formato appState da Impressão"
    O `appState` é uma string codificada em JSON. Para manipulação mais fácil:
    
    ```python
    import json
    
    app_state = {
        'version': 2,
        'recentDestinations': [{
            'id': 'Save as PDF',
            'origin': 'local'
        }],
        'marginsType': 3,                   # 0=padrão, 1=sem margens, 2=mínimo, 3=personalizado
        'customMargins': {
            'marginTop': 63,
            'marginRight': 192,
            'marginBottom': 240,
            'marginLeft': 260
        },
        'isHeaderFooterEnabled': False,
        'scaling': '100',
        'scalingType': 3,                   # 0=padrão, 1=ajustar à página, 2=ajustar ao papel, 3=personalizado
        'isColorEnabled': True,
        'isDuplexEnabled': False,
        'isCssBackgroundEnabled': True,
        'dpi': {
            'horizontal_dpi': 300,
            'vertical_dpi': 300,
            'is_default': True
        },
        'mediaSize': {
            'name': 'ISO_A4',
            'width_microns': 210000,
            'height_microns': 297000,
            'custom_display_name': 'A4',
            'is_default': True
        }
    }
    
    # Converter para string para o appState
    options.browser_preferences = {
        'printing': {
            'print_preview_sticky_settings': {
                'appState': json.dumps(app_state)
            }
        }
    }
    ```

### WebRTC e Peer-to-Peer

```python
options.browser_preferences = {
    'webrtc': {
        # Política de manuseio de IP
        'ip_handling_policy': 'default_public_interface_only',
        
        # Opções de transporte UDP
        'udp_port_range': '10000-10100',    # Restringir intervalo de portas UDP
        
        # Desabilitar peer-to-peer
        'multiple_routes_enabled': False,
        'nonproxied_udp_enabled': False,
        
        # Coleta de log de texto
        'text_log_collection_allowed': False
    }
}
```

### Isolamento de Site e Segurança

```python
options.browser_preferences = {
    # Isolamento de site
    'site_isolation': {
        'isolate_origins': '',              # Origens separadas por vírgula para isolar
        'site_per_process': True            # Isolamento total de site
    },
    
    # Conteúdo misto
    'mixed_content': {
        'auto_upgrade_enabled': True        # Atualizar HTTP para HTTPS
    },
    
    # SSL/TLS
    'ssl': {
        'rev_checking': {
            'enabled': True                 # Verificar revogação de certificado
        }
    }
}
```

### Metadados de Instalação e País

```python
import uuid
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    # ID do país na instalação (afeta config. padrão e localidade)
    'countryid_at_install': 16978,          # Varia por país (ex: 16978 para Brasil)
    
    # Estado de instalação de aplicativos padrão
    'default_apps_install_state': 3,        # 0=não inst., 1=inst., 3=migrado
    
    # GUID do perfil corporativo (para navegadores gerenciados)
    'enterprise_profile_guid': str(uuid.uuid4()),
    
    # Provedor de busca padrão
    'default_search_provider': {
        'guid': ''                          # Vazio para padrão (Google)
    }
}
```

!!! info "Valores de ID de País"
    `countryid_at_install` é um código numérico que representa o país onde o Chrome foi instalado pela primeira vez:
    
    - **16978**: Brasil (BR)
    - **16965**: Estados Unidos (US)
    - **16967**: Grã-Bretanha (GB)
    - **16966**: Alemanha (DE)
    - **16972**: Japão (JP)
    - E muitos outros...
    
    Isso afeta o idioma padrão, moeda e configurações regionais. Para um fingerprinting realista, combine isso com sua região alvo.

### Recursos Experimentais

```python
options.browser_preferences = {
    # Experimentos do Chrome Labs
    'browser': {
        'labs': {
            'enabled': False
        }
    },
    
    # Pré-carregamento
    'preload': {
        'enabled': False                    # Desabilitar pré-carregamento de página
    },
    
    # Rolagem suave
    'smooth_scrolling': {
        'enabled': True
    },
    
    # Aceleração de hardware
    'hardware_acceleration_mode': {
        'enabled': True                     # Desabilitar para desempenho headless
    }
}
```

### DevTools e Opções de Desenvolvedor

```python
options.browser_preferences = {
    'devtools': {
        'preferences': {
            # Aparência do DevTools
            'currentDockState': '"right"',              # "bottom", "right", "undocked"
            'uiTheme': '"dark"',                        # "dark", "light", "system"
            
            # Configurações do Console
            'consoleTimestampsEnabled': 'true',
            'preserveConsoleLog': 'true',
            
            # Painel de Rede
            'network.disableCache': 'false',
            'network.color-code-resource-types': 'true',
            'network-panel-split-view-state': '{"vertical":{"size":0}}',
            
            # Mapas de origem
            'cssSourceMapsEnabled': 'true',
            'jsSourceMapsEnabled': 'true',
            
            # Painel de Elementos
            'elements.styles.sidebar.width': '{"vertical":{"size":0,"showMode":"OnlyMain"}}',
            
            # Versionamento do Inspetor
            'inspectorVersion': '37',
            
            # Painel selecionado
            'panel-selected-tab': '"network"',          # Último painel aberto
            
            # Categorias expandidas de info de requisição
            'request-info-general-category-expanded': 'true',
            'request-info-request-headers-category-expanded': 'true',
            'request-info-response-headers-category-expanded': 'true'
        },
        'synced_preferences_sync_disabled': {
            'adorner-settings': '[{"adorner":"grid","isEnabled":true},{"adorner":"flex","isEnabled":true}]',
            'syncedInspectorVersion': '37'
        }
    },
    
    # GCM (Google Cloud Messaging)
    'gcm': {
        'product_category_for_subtypes': 'com.chrome.linux'  # com.chrome.windows, com.chrome.macos
    }
}
```

!!! tip "Formato das Preferências do DevTools"
    As preferências do DevTools usam um formato único onde valores booleanos e strings são armazenados como **strings codificadas em JSON** (ex: `'true'` em vez de `True`, `'"dark"'` em vez de `'dark'`). Isso ocorre porque as configurações do DevTools são serializadas diretamente para JSON.
    
    Para objetos complexos, codifique duas vezes:
    ```python
    import json
    
    # Crie o objeto
    split_view = {'vertical': {'size': 0}}
    
    # Codifique duas vezes para o DevTools
    devtools_value = json.dumps(json.dumps(split_view))
    # Resultado: '"{\\"vertical\\":{\\"size\\":0}}"'
    ```

### Controle de Sincronização e Login

```python
import time
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    'signin': {
        'allowed': True,                        # Permitir login no Google
        'cookie_clear_on_exit_migration_notice_complete': True
    },
    
    'sync': {
        'data_type_status_for_sync_to_signin': {
            'bookmarks': False,
            'history': False,
            'passwords': False,
            'preferences': False
        },
        'encryption_bootstrap_token_per_account_migration_done': True,
        'passwords_per_account_pref_migration_done': True,
        'feature_status_for_sync_to_signin': 5
    },
    
    # Serviços do Google
    'google': {
        'services': {
            'signin_scoped_device_id': '<your-device-id>'  # Gere um ID único
        }
    },
    
    # GAIA (Google Accounts Infrastructure)
    'gaia_cookie': {
        'changed_time': str(int(time.time())),
        'hash': '',
        'last_list_accounts_data': '[]'
    }
}
```

### Otimização e Rastreamento de Desempenho

```python
import time
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    # Guia de otimização (dicas de desempenho do Google)
    'optimization_guide': {
        'hintsfetcher': {
            'hosts_successfully_fetched': {}
        },
        'predictionmodelfetcher': {
            'last_fetch_attempt': str(int(time.time())),
            'last_fetch_success': str(int(time.time()))
        },
        'previously_registered_optimization_types': {}
    },
    
    # Clusters de histórico (agrupando navegação relacionada)
    'history_clusters': {
        'all_cache': {
            'all_keywords': {},
            'all_timestamp': str(int(time.time()))
        },
        'last_selected_tab': 0,
        'short_cache': {
            'short_keywords': {},
            'short_timestamp': '0'
        }
    },
    
    # Métricas de diversidade de domínio
    'domain_diversity': {
        'last_reporting_timestamp': str(int(time.time()))
    },
    
    # Plataforma de segmentação (análise de comportamento do usuário)
    'segmentation_platform': {
        'device_switcher_util': {
            'result': {
                'labels': ['NotSynced']
            }
        },
        'last_db_compaction_time': str(int(time.time()))
    },
    
    # Zero suggest (previsões da omnibox)
    'zerosuggest': {
        'cachedresults': '',
        'cachedresults_with_url': {}
    }
}
```

!!! info "Preferências de Rastreamento de Desempenho"
    Essas preferências são tipicamente usadas pelo Chrome para rastrear e otimizar o desempenho. Para automação, você pode deixá-las vazias ou definir valores realistas para parecer mais com um navegador normal.

### Eventos de Sessão e Tratamento de Falhas

O Chrome rastreia o histórico da sessão para recuperação e telemetria:

```python
import time
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    'sessions': {
        'event_log': [
            {
                'crashed': False,
                'time': str(int(time.time() * 1000000) + 11644473600000000),
                'type': 0                   # 0=início da sessão
            },
            {
                'crashed': False,
                'did_schedule_command': True,
                'first_session_service': True,
                'tab_count': 1,
                'time': str(int(time.time() * 1000000) + 11644473600000000),
                'type': 2,                  # 2=dados da sessão salvos
                'window_count': 1
            }
        ],
        'session_data_status': 3            # 0=desconhecido, 1=sem dados, 2=alguns dados, 3=dados completos
    },
    
    # Tipo de saída do perfil (importante para fingerprinting)
    'profile': {
        'exit_type': 'Crashed'              # 'Normal', 'Crashed', 'SessionEnded'
    }
}
```

!!! warning "Crashed vs Normal"
    A maioria dos navegadores reais **falha ocasionalmente**. Mostrar sempre a saída `'Normal'` é suspeito.
    
    **Estratégia realista**: Defina `'Crashed'` para ~10-20% dos perfis para simular a experiência normal do usuário. Ironicamente, ter falhas ocasionais faz sua automação parecer mais humana.

!!! tip "Tipos de Eventos de Sessão"
    - **Tipo 0**: Início da sessão
    - **Tipo 1**: Sessão terminada normalmente
    - **Tipo 2**: Dados da sessão salvos (abas, janelas)
    - **Tipo 3**: Sessão restaurada
    
    O `event_log` constrói um histórico de sessões do navegador ao longo do tempo.

## Furtividade (Stealth) e Fingerprinting

Criar um fingerprint de navegador realista é crucial para evitar sistemas de detecção de bots. Esta seção cobre técnicas básicas e avançadas.

### Configuração Rápida de Furtividade

Para a maioria dos casos de uso, esta configuração simples fornece boa anti-detecção:

```python
import asyncio
import time
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def quick_stealth():
    options = ChromiumOptions()
    
    # Simular um navegador com 60 dias de uso
    fake_timestamp = int(time.time()) - (60 * 24 * 60 * 60)
    
    options.browser_preferences = {
        # Histórico de uso falso
        'profile': {
            'last_engagement_time': fake_timestamp,
            'exited_cleanly': True,
            'exit_type': 'Normal'
        },
        
        # Página inicial realista
        'homepage': 'https://www.google.com',
        'session': {
            'restore_on_startup': 1,
            'startup_urls': ['https://www.google.com']
        },
        
        # Habilitar recursos que usuários reais têm
        'enable_do_not_track': False,  # A maioria dos usuários não habilita isso
        'safebrowsing': {'enabled': True},
        'autofill': {'enabled': True},
        'search': {'suggest_enabled': True},
        'dns_prefetching': {'enabled': True}
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://bot-detection-site.com')
        print("Modo furtivo ativado!")

asyncio.run(quick_stealth())
```

!!! tip "Princípios Chave da Furtividade"
    **Habilite, não desabilite**: Usuários reais têm Safe Browsing, preenchimento automático e sugestões de busca habilitados. Desabilitar tudo parece suspeito.
    
    **Envelheça seu perfil**: Instalações novas são um sinal de alerta. Simule um navegador que foi usado por semanas ou meses.
    
    **Combine com a maioria**: Use configurações padrão que 90% dos usuários têm, não configurações focadas em privacidade.

### Fingerprinting Avançado

Para máximo realismo, simule um histórico detalhado de uso do navegador:

```python
import time
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

def create_realistic_browser() -> ChromiumOptions:
    """Cria um navegador com resistência abrangente a fingerprinting."""
    options = ChromiumOptions()
    
    # Timestamps
    current_time = int(time.time())
    install_time = current_time - (90 * 24 * 60 * 60)  # 90 dias atrás
    last_use = current_time - (3 * 60 * 60)            # 3 horas atrás
    
    options.browser_preferences = {
        # Metadados do perfil (crítico para fingerprinting)
        'profile': {
            'created_by_version': '130.0.6723.91',      # Deve corresponder à sua versão do Chrome
            'creation_time': str(install_time),
            'last_engagement_time': str(last_use),
            'exit_type': 'Crashed',                     # 'Normal', 'Crashed', 'SessionEnded'
            'name': 'Pessoa 1',                         # Nome de perfil realista
            'avatar_index': 26,                         # 0-26 avatares disponíveis
            
            # Configurações de conteúdo realistas
            'default_content_setting_values': {
                'cookies': 1,
                'images': 1,
                'javascript': 1,
                'popups': 0,
                'notifications': 2,
                'geolocation': 0,           # Perguntar (não bloquear)
                'media_stream': 0           # Perguntar (realista)
            },
            
            'password_manager_enabled': False,
            'cookie_controls_mode': 0,
            'content_settings': {
                'pref_version': 1,
                'enable_quiet_permission_ui': {
                    'notifications': False
                },
                'enable_quiet_permission_ui_enabling_method': {
                    'notifications': 1
                }
            },
            
            # Metadados de segurança
            'family_member_role': 'not_in_family',
            'managed_user_id': '',
            'were_old_google_logins_removed': True
        },
        
        # Metadados de uso do navegador
        'browser': {
            'has_seen_welcome_page': True,
            'window_placement': {
                'work_area_bottom': 1080,
                'work_area_left': 0,
                'work_area_right': 1920,
                'work_area_top': 0
            }
        },
        
        # Metadados de instalação
        'countryid_at_install': 16978,              # Varia por país
        'default_apps_install_state': 3,
        
        # Metadados de extensões
        'extensions': {
            'last_chrome_version': '130.0.6723.91',  # Deve corresponder à sua versão
            'alerts': {'initialized': True},
            'theme': {'system_theme': 2}
        },
        
        # Atividade da sessão (mostra uso regular)
        'in_product_help': {
            'session_start_time': str(current_time),
            'session_last_active_time': str(current_time),
            'recent_session_start_times': [
                str(current_time - (24 * 60 * 60)),
                str(current_time - (48 * 60 * 60)),
                str(current_time - (72 * 60 * 60))
            ]
        },
        
        # Restauração de sessão
        'session': {
            'restore_on_startup': 1,
            'startup_urls': ['https://www.google.com']
        },
        
        # Página inicial
        'homepage': 'https://www.google.com',
        'homepage_is_newtabpage': False,
        
        # Histórico de tradução (mostra uso multilíngue)
        'translate': {'enabled': True},
        'translate_accepted_count': {'es': 2, 'fr': 1},
        'translate_denied_count_for_language': {'en': 1},
        
        # Verificação ortográfica
        'spellcheck': {
            'dictionaries': ['en-US', 'pt-BR'],
            'dictionary': ''
        },
        
        # Idiomas
        'intl': {
            'selected_languages': 'en-US,en,pt-BR'
        },
        
        # Metadados de login
        'signin': {
            'allowed': True,
            'cookie_clear_on_exit_migration_notice_complete': True
        },
        
        # Safe Browsing (a maioria dos usuários tem isso)
        'safebrowsing': {
            'enabled': True,
            'enhanced': False
        },
        
        # Preenchimento automático (comum para usuários reais)
        'autofill': {
            'enabled': True,
            'profile_enabled': True
        },
        
        # Sugestões de busca
        'search': {'suggest_enabled': True},
        
        # DNS prefetch
        'dns_prefetching': {'enabled': True},
        
        # Do NOT Track (geralmente desligado)
        'enable_do_not_track': False,
        
        # WebRTC (configurações padrão)
        'webrtc': {
            'ip_handling_policy': 'default',
            'multiple_routes_enabled': True
        },
        
        # Privacy Sandbox (novo sistema de rastreamento do Google - usuários realistas têm isso)
        'privacy_sandbox': {
            'first_party_sets_data_access_allowed_initialized': True,
            'm1': {
                'ad_measurement_enabled': True,
                'fledge_enabled': True,
                'row_notice_acknowledged': True,
                'topics_enabled': True
            }
        },
        
        # Engajamento de mídia
        'media': {
            'engagement': {'schema_version': 5}
        },
        
        # Web apps
        'web_apps': {
            'did_migrate_default_chrome_apps': ['app-id'],
            'last_preinstall_synchronize_version': '130'
        }
    }
    
    return options

# Uso
async def advanced_stealth():
    options = create_realistic_browser()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://advanced-bot-detection.com')
        # O navegador aparece como uma instalação genuína de 90 dias

```

!!! warning "Consistência de Versão é Crítica"
    **Sempre combine as versões do Chrome**: Garanta que `profile.created_by_version` e `extensions.last_chrome_version` correspondam à sua versão real do Chrome. Versões incompatíveis são um sinal de alerta instantâneo.
    
    ```python
    # Obtenha sua versão do Chrome programaticamente:
    async with Chrome() as browser:
        tab = await browser.start()
        version = await browser.get_version()
        chrome_version = version['product'].split('/')[1]  # ex: '130.0.6723.91'
        print(f"Use esta versão: {chrome_version}")
    ```

!!! info "O que as Preferências de Fingerprinting Fazem"
    **Idade do perfil**: `creation_time` e `last_engagement_time` provam que o navegador não é uma instalação nova.
    
    **Histórico de uso**: `recent_session_start_times` mostra padrões regulares de navegação.
    
    **Histórico de tradução**: `translate_accepted_count` indica uma pessoa real usando múltiplos idiomas.
    
    **Posicionamento da janela**: Dimensões de tela realistas que correspondem a resoluções de monitor reais.
    
    **Privacy Sandbox**: Novo sistema de rastreamento do Google. Desabilitá-lo é incomum e suspeito.

## Impacto no Desempenho

Entender as implicações de desempenho das preferências do navegador ajuda a otimizar para seu caso de uso específico:

| Categoria de Preferência | Impacto Esperado | Caso de Uso |
|---|---|---|
| Desabilitar imagens | 50-70% carregamentos mais rápidos | Raspagem de conteúdo de texto |
| Desabilitar prefetch | 10-20% carregamentos mais rápidos | Reduzir uso de banda |
| Desabilitar plugins | 5-10% carregamentos mais rápidos | Segurança e desempenho |
| Bloquear notificações | Elimina popups | Automação limpa |
| Downloads silenciosos | Elimina prompts | Downloads automatizados de arquivos |

!!! tip "Troca entre Velocidade e Furtividade"
    **Para velocidade**: Desabilite imagens, prefetch, plugins e verificação ortográfica.
    
    **Para furtividade**: Habilite Safe Browsing, preenchimento automático, sugestões de busca e DNS prefetch (mesmo que eles tornem as coisas mais lentas).
    
    **Abordagem equilibrada**: Habilite recursos de furtividade, mas desabilite imagens e plugins. Isso dá 40-50% de ganho de velocidade enquanto mantém um fingerprint realista.

## Veja Também

- **[Análise Profunda: Preferências do Navegador](../../deep-dive/browser-preferences.md)** - Detalhes arquitetônicos e internos
- **[Estado de Carregamento da Página](page-load-state.md)** - Controle quando as páginas são consideradas carregadas
- **[Configuração de Proxy](proxy.md)** - Configure proxies de rede
- **[Cookies e Sessões](../browser-management/cookies-sessions.md)** - Gerencie o estado do navegador
- **[Código-Fonte do Chromium: pref_names.cc](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.cc)** - Constantes oficiais de preferência
- **[Código-Fonte do Chromium: pref_names.h](https://github.com/chromium/chromium/blob/main/chrome/common/pref_names.h)** - Arquivo de cabeçalho com definições

As preferências personalizadas do navegador oferecem um controle sem precedentes sobre o comportamento do navegador, permitindo automação sofisticada, otimização de desempenho e configuração de privacidade que simplesmente não são possíveis com ferramentas de automação tradicionais. Este nível de acesso transforma o Pydoll de uma simples biblioteca de automação em um sistema completo de controle de navegador.