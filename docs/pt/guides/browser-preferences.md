# Preferências do navegador

Preferências são as configurações que vivem dentro de um perfil do Chromium: a pasta de downloads, os idiomas aceitos, se pop-ups e notificações são permitidos, e centenas de outras. Você as define em `ChromiumOptions` antes de iniciar o navegador, e o Pydoll as aplica ao perfil que ele lança.

Preferências não são o mesmo que [argumentos de linha de comando](browser-options.md). Argumentos são flags passadas ao binário do Chromium na inicialização (`--headless`, `--proxy-server`); preferências são entradas nas configurações do perfil, as mesmas que a UI de Configurações escreve. Use argumentos para como o processo inicia, e preferências para como o perfil se comporta.

## Definir preferências comuns {#set-common-preferences}

As preferências do dia a dia têm métodos e propriedades auxiliares, então você as define sem memorizar as chaves internas do Chromium ou números mágicos.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.set_default_download_directory('/tmp/downloads')
    options.set_accept_languages('en-US,en')
    options.block_notifications = True
    options.block_popups = True

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://news.ycombinator.com')

asyncio.run(main())
```

Os helpers disponíveis:

| Helper | O que define |
|--------|--------------|
| `options.set_default_download_directory(path)` | Onde os downloads são salvos |
| `options.set_accept_languages('en-US,en')` | O header `Accept-Language` e `navigator.languages` |
| `options.prompt_for_download = False` | Se o Chrome pergunta antes de cada download |
| `options.allow_automatic_downloads = True` | Se uma página pode disparar vários downloads |
| `options.block_popups = True` | Bloquear janelas pop-up |
| `options.block_notifications = True` | Bloquear pedidos de notificação de sites |
| `options.password_manager_enabled = False` | Ligar ou desligar o gerenciador de senhas do Chrome |
| `options.open_pdf_externally = True` | Baixar PDFs em vez de abrir o visualizador |

Cada helper escreve a chave aninhada certa com o valor certo, então `block_notifications = True` vira a configuração de notificação que o Chromium espera, não um número que você precisa procurar.

!!! tip "Idioma, downloads e detecção"
    `set_accept_languages` deve combinar com o locale que você apresenta em outros lugares; um idioma dos EUA em um IP fora dos EUA é uma inconsistência que sistemas anti-bot checam. Veja [Ficando indetectável](../stealth/index.md).

## Definir qualquer preferência

Para uma preferência sem helper, atribua a `options.browser_preferences`. Ela recebe um dict aninhado e o mescla com o que já estiver definido, então você pode montá-lo ao longo de várias atribuições.

```python
options = ChromiumOptions()

options.browser_preferences = {
    'download': {'default_directory': '/tmp/downloads'},
    'intl': {'accept_languages': 'en-US,en'},
}

# uma atribuição posterior mescla, não substitui
options.browser_preferences = {
    'profile': {'default_content_setting_values': {'images': 2}},
}
```

O Chromium documenta preferências como caminhos com pontos (por exemplo `download.default_directory`). Cada ponto é um nível do dict: `download.default_directory` vira `{'download': {'default_directory': ...}}`. Aninhe as chaves para casar com o caminho.

!!! note "Não envolva em `prefs`"
    Atribua a árvore de preferências diretamente. Envolvê-la em uma chave de topo `{'prefs': {...}}` levanta um erro; os helpers e o dict esperam os caminhos reais no nível de topo.

## Montar um perfil realista para stealth {#build-a-realistic-profile-for-stealth}

Sistemas anti-bot leem o perfil, não só a página. Um perfil novo e vazio com todo recurso de conveniência desativado não se parece nada com um usuário real, então as preferências são uma alavanca para parecer normal. A ideia norteadora vai no sentido oposto da maioria dos conselhos de privacidade:

- **Habilite, não desabilite.** Usuários reais deixam Safe Browsing, autofill e sugestões de busca ligados. Um perfil com tudo desligado é em si um sinal.
- **Envelheça o perfil.** Um perfil criado segundos atrás é um alerta. Retroaja os timestamps de uso para que ele pareça ter semanas ou meses.
- **Combine com o seu Chrome real.** Qualquer string de versão que você definir (em `profile` ou `extensions`) precisa combinar com o binário do Chrome que você realmente está rodando, ou a inconsistência te entrega.

```python
import asyncio
import time

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


def realistic_options() -> ChromiumOptions:
    now = int(time.time())
    installed = now - (90 * 24 * 60 * 60)   # 90 dias atrás
    last_used = now - (3 * 60 * 60)         # 3 horas atrás

    options = ChromiumOptions()
    options.browser_preferences = {
        'profile': {
            'created_by_version': '130.0.6723.91',   # combine com seu Chrome real
            'creation_time': str(installed),
            'last_engagement_time': str(last_used),
            'exit_type': 'Normal',
            'name': 'Person 1',
            'default_content_setting_values': {
                'cookies': 1, 'images': 1, 'javascript': 1,
                'notifications': 2, 'geolocation': 0, 'media_stream': 0,
            },
        },
        'extensions': {'last_chrome_version': '130.0.6723.91'},
        'intl': {'selected_languages': 'en-US,en'},
        'spellcheck': {'dictionaries': ['en-US']},
        'session': {'restore_on_startup': 1, 'startup_urls': ['https://www.google.com']},
        'homepage': 'https://www.google.com',
        'safebrowsing': {'enabled': True},
        'autofill': {'enabled': True},
        'search': {'suggest_enabled': True},
        'dns_prefetching': {'enabled': True},
        'enable_do_not_track': False,
        'webrtc': {'ip_handling_policy': 'default', 'multiple_routes_enabled': True},
    }
    return options


async def main():
    async with Chrome(options=realistic_options()) as browser:
        tab = await browser.start()
        await tab.go_to('https://news.ycombinator.com')

asyncio.run(main())
```

!!! note "Preferências são uma camada, não o fingerprint inteiro"
    Preferências moldam a identidade do perfil (histórico de uso, recursos habilitados, idiomas). Elas não mudam o User-Agent, o WebGL, o canvas nem o fingerprint de camada de rede. Para esses, e para manter cada camada consistente, veja [Injeção de fingerprint](../stealth/fingerprint-injection.md).

## Referência de preferências

Os blocos abaixo listam preferências do Chromium que vale conhecer, agrupadas por área. São as próprias configurações do Chromium, não do Pydoll, então as chaves exatas e os valores aceitos são definidos pelo Chromium e podem mudar entre versões; o Pydoll passa direto o que você definir. Valores de content-setting seguem a convenção do Chromium: `0` = perguntar, `1` = permitir, `2` = bloquear. Trate isto como uma consulta, e recorra primeiro aos [métodos auxiliares](#set-common-preferences) quando um existir.

??? example "Configurações de conteúdo e mídia"


    ```python
    options.browser_preferences = {
        'profile': {
            'default_content_setting_values': {
                # Controle de conteúdo (0=perguntar, 1=permitir, 2=bloquear)
                'cookies': 1,                    # Permitir cookies
                'images': 1,                     # Permitir imagens (2 para bloquear)
                'javascript': 1,                 # Permitir JavaScript (2 para bloquear)
                'plugins': 2,                    # Bloquear plugins (Flash, etc.)
                'popups': 0,                     # Bloquear pop-ups
                'geolocation': 2,                # Bloquear pedidos de localização
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


??? example "Rede e desempenho"


    ```python
    options.browser_preferences = {
        'net': {
            # Predição de rede: 0=sempre, 1=apenas wifi, 2=nunca
            'network_prediction_options': 2,

            # Checagem rápida de alcançabilidade do servidor
            'quick_check_enabled': False
        },

        # Prefetch de DNS
        'dns_prefetching': {
            'enabled': False  # Desative para reduzir o tráfego de rede
        },

        # Preconexão aos resultados de busca
        'search': {
            'suggest_enabled': False,           # Desativa sugestões de busca
            'instant_enabled': False            # Desativa resultados instantâneos
        },

        # Páginas de erro alternativas
        'alternate_error_pages': {
            'enabled': False  # Não sugerir alternativas para 404s
        }
    }
    ```


??? example "Preferências de download"


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
            'partial_view_enabled': True        # Mostrar a bolha de progresso de download
        },

        'safebrowsing': {
            'enabled': False  # Desativar avisos de download do Safe Browsing
        }
    }
    ```


??? example "Privacidade e segurança"


    ```python
    options.browser_preferences = {
        # Do Not Track
        'enable_do_not_track': True,

        # Referrers
        'enable_referrers': False,

        # Safe Browsing
        'safebrowsing': {
            'enabled': False,                   # Desativar Safe Browsing
            'enhanced': False                   # Desativar proteção aprimorada
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

        # WebRTC (pode vazar o IP real)
        'webrtc': {
            'ip_handling_policy': 'default_public_interface_only',
            'multiple_routes_enabled': False,
            'nonproxied_udp_enabled': False
        }
    }
    ```


??? example "Autofill e senhas"


    ```python
    options.browser_preferences = {
        'autofill': {
            'enabled': False,                   # Desativar preenchimento automático de formulários
            'profile_enabled': False,           # Desativar autofill de endereço
            'credit_card_enabled': False,       # Desativar autofill de cartão de crédito
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


??? example "Comportamento e UI do navegador"


    ```python
    import time

    options.browser_preferences = {
        # Página inicial e inicialização
        'homepage': 'https://www.google.com',
        'homepage_is_newtabpage': False,
        'newtab_page_location_override': 'https://www.google.com',

        'session': {
            'restore_on_startup': 1,            # 0=nova aba, 1=restaurar, 4=URLs específicas, 5=página de nova aba
            'startup_urls': ['https://www.google.com'],
            'session_data_status': 3            # Status dos dados de sessão (interno)
        },

        # Página de boas-vindas e janela
        'browser': {
            'has_seen_welcome_page': True,      # Pular a tela de boas-vindas
            'window_placement': {
                'bottom': 1032,                 # Posição inferior da janela
                'left': 2247,                   # Posição esquerda da janela
                'right': 3192,                  # Posição direita da janela
                'top': 31,                      # Posição superior da janela
                'maximized': False,             # Janela está maximizada
                'work_area_bottom': 1080,       # Base da área de trabalho da tela
                'work_area_left': 1920,         # Esquerda da área de trabalho da tela
                'work_area_right': 3840,        # Direita da área de trabalho da tela
                'work_area_top': 0              # Topo da área de trabalho da tela
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
            'last_chrome_version': '130.0.6723.91'  # Precisa combinar com sua versão
        },

        # Tradução
        'translate': {
            'enabled': False                    # Desativar prompts de tradução
        },
        'translate_blocked_languages': ['en'],  # Nunca traduzir inglês
        'translate_site_blacklist': [],         # Legado (use blocklist_with_time)

        # Favoritos
        'bookmark_bar': {
            'show_on_all_tabs': False
        },

        # Abas
        'tabs': {
            'new_tab_position': 0               # 0=direita, 1=após a atual
        },
        'pinned_tabs': [],                      # Lista de URLs de abas fixadas

        # Página de nova aba (timestamps no formato do Chrome)
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

    !!! note "Formato de timestamp do Chrome"
        O Chrome usa o formato FILETIME do Windows: microssegundos desde 1 de janeiro de 1601 UTC.

        Converta um timestamp do Python:
        ```python
        import time
        chrome_time = int(time.time() * 1000000) + 11644473600000000
        ```


??? example "Ortografia e idioma"


    ```python
    options.browser_preferences = {
        'browser': {
            'enable_spellchecking': False       # Desativar verificação ortográfica
        },

        'spellcheck': {
            'dictionaries': ['en-US', 'pt-BR'], # Idiomas da verificação ortográfica
            'dictionary': '',                   # Preferência legada (mantenha vazia)
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

        # Contadores de modelo de idioma (estatísticas de uso)
        'language_model_counters': {
            'en': 2,                            # Contagem de palavras em inglês
            'pt': 10                            # Contagem de palavras em português
        }
    }
    ```

    !!! note "Contadores de modelo de idioma"
        Estes contadores rastreiam estatísticas de uso de idioma para os modelos de machine learning do Chrome:

        - Usados para prever as preferências de idioma do usuário
        - Afetam sugestões de busca e autocompletar
        - Contagens mais altas indicam uso mais frequente
        - Valores realistas: 0-1000 para uso ocasional, 1000+ para uso intenso


??? example "Acessibilidade"


    ```python
    options.browser_preferences = {
        'accessibility': {
            'image_labels_enabled': False       # Não obter rótulos de imagem do Google
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


??? example "Mídia e áudio"


    ```python
    options.browser_preferences = {
        # Áudio
        'audio': {
            'mute_enabled': False               # Iniciar com áudio ligado/desligado
        },

        # Reprodução automática
        'media': {
            'autoplay_policy': 0,               # 0=permitir, 1=gesto do usuário, 2=ativação do documento pelo usuário
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


??? example "Impressão"


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

    !!! tip "Formato do appState de impressão"
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

        # Converter para string no appState
        options.browser_preferences = {
            'printing': {
                'print_preview_sticky_settings': {
                    'appState': json.dumps(app_state)
                }
            }
        }
        ```


??? example "WebRTC e peer-to-peer"


    ```python
    options.browser_preferences = {
        'webrtc': {
            # Política de tratamento de IP
            'ip_handling_policy': 'default_public_interface_only',

            # Opções de transporte UDP
            'udp_port_range': '10000-10100',    # Restringir a faixa de portas UDP

            # Desativar peer-to-peer
            'multiple_routes_enabled': False,
            'nonproxied_udp_enabled': False,

            # Coleta de log de texto
            'text_log_collection_allowed': False
        }
    }
    ```


??? example "Isolamento de site e segurança"


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
                'enabled': True                 # Checar revogação de certificado
            }
        }
    }
    ```


??? example "Metadados de instalação e país"


    ```python
    import uuid
    from pydoll.browser.options import ChromiumOptions

    options = ChromiumOptions()
    options.browser_preferences = {
        # ID do país na instalação (afeta configurações padrão e locale)
        'countryid_at_install': 16978,          # Varia por país (ex.: 16978 para o Brasil)

        # Estado de instalação dos apps padrão
        'default_apps_install_state': 3,        # 0=não instalado, 1=instalado, 3=migrado

        # GUID de perfil corporativo (para navegadores gerenciados)
        'enterprise_profile_guid': str(uuid.uuid4()),

        # Provedor de busca padrão
        'default_search_provider': {
            'guid': ''                          # Vazio para o padrão (Google)
        }
    }
    ```

    !!! note "Valores de ID de país"
        `countryid_at_install` é um código numérico que representa o país onde o Chrome foi instalado pela primeira vez:

        - **16978**: Brasil (BR)
        - **16965**: Estados Unidos (US)
        - **16967**: Grã-Bretanha (GB)
        - **16966**: Alemanha (DE)
        - **16972**: Japão (JP)
        - E muitos outros...

        Isso afeta idioma padrão, moeda e configurações regionais. Para fingerprinting realista, combine isto com a sua região alvo.


??? example "Recursos experimentais"


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
            'enabled': False                    # Desativar pré-carregamento de páginas
        },

        # Rolagem suave
        'smooth_scrolling': {
            'enabled': True
        },

        # Aceleração de hardware
        'hardware_acceleration_mode': {
            'enabled': True                     # Desative para desempenho headless
        }
    }
    ```


??? example "DevTools e opções de desenvolvedor"


    ```python
    options.browser_preferences = {
        'devtools': {
            'preferences': {
                # Aparência do DevTools
                'currentDockState': '"right"',              # "bottom", "right", "undocked"
                'uiTheme': '"dark"',                        # "dark", "light", "system"

                # Configurações do console
                'consoleTimestampsEnabled': 'true',
                'preserveConsoleLog': 'true',

                # Painel de rede
                'network.disableCache': 'false',
                'network.color-code-resource-types': 'true',
                'network-panel-split-view-state': '{"vertical":{"size":0}}',

                # Source maps
                'cssSourceMapsEnabled': 'true',
                'jsSourceMapsEnabled': 'true',

                # Painel de elementos
                'elements.styles.sidebar.width': '{"vertical":{"size":0,"showMode":"OnlyMain"}}',

                # Versionamento do inspetor
                'inspectorVersion': '37',

                # Painel selecionado
                'panel-selected-tab': '"network"',          # Último painel aberto

                # Categorias expandidas de informações de requisição
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

    !!! tip "Formato das preferências do DevTools"
        As preferências do DevTools usam um formato único onde valores booleanos e de string são armazenados como **strings codificadas em JSON** (por exemplo, `'true'` e não `True`, `'"dark"'` e não `'dark'`). Isso ocorre porque as configurações do DevTools são serializadas diretamente para JSON.

        Para objetos complexos, faça codificação dupla:
        ```python
        import json

        # Criar o objeto
        split_view = {'vertical': {'size': 0}}

        # Codificação dupla para o DevTools
        devtools_value = json.dumps(json.dumps(split_view))
        # Resultado: '"{\\"vertical\\":{\\"size\\":0}}"'
        ```


??? example "Controle de sincronização e login"


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
                'signin_scoped_device_id': '<your-device-id>'  # Gerar ID único
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


??? example "Otimização e rastreamento de desempenho"


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

        # Clusters de histórico (agrupamento de navegação relacionada)
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

    !!! note "Preferências de rastreamento de desempenho"
        Estas preferências são normalmente usadas pelo Chrome para rastrear e otimizar desempenho. Para automação, você pode deixá-las vazias ou definir valores realistas para parecer mais com um navegador normal.


??? example "Eventos de sessão e tratamento de crashes"


    O Chrome rastreia o histórico de sessão para recuperação e telemetria:

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
                    'type': 2,                  # 2=dados de sessão salvos
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
        A maioria dos navegadores reais **trava de vez em quando**. Mostrar sempre uma saída `'Normal'` é suspeito.

        **Estratégia realista**: Defina `'Crashed'` para ~10-20% dos perfis para simular a experiência normal de um usuário. Ironicamente, ter "crashes" ocasionais faz sua automação parecer mais humana.

    !!! tip "Tipos de evento de sessão"
        - **Tipo 0**: Início da sessão
        - **Tipo 1**: Sessão encerrada normalmente
        - **Tipo 2**: Dados de sessão salvos (abas, janelas)
        - **Tipo 3**: Sessão restaurada

        O `event_log` constrói um histórico de sessões do navegador ao longo do tempo.

## Próximos passos

- [Opções do navegador](browser-options.md): as flags de linha de comando que controlam como o navegador é lançado.
- [Configuração de proxy](proxies.md): roteie o navegador por um proxy.
- [Injeção de fingerprint](../stealth/fingerprint-injection.md): a camada de User-Agent, WebGL e canvas que as preferências não cobrem.
- [Ficando indetectável](../stealth/index.md): mantenha as configurações do seu perfil consistentes com a identidade que você apresenta.
