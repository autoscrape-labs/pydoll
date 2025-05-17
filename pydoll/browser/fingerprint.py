import json
import random
import string
import uuid
from typing import Dict, List, Union


class FingerprintGenerator:
    """
    Class for generating browser fingerprint spoofing data.

    This class is responsible for generating unique browser fingerprints for each session
    to disguise the browser environment and avoid tracking and fingerprint identification.
    """

    # Common operating system list
    OS_LIST = [
        {'name': 'Windows', 'version': '10.0'},
        {'name': 'Windows', 'version': '11.0'},
        {'name': 'Macintosh', 'version': '10.15.7'},
        {'name': 'Macintosh', 'version': '11.6.8'},
        {'name': 'Linux', 'version': 'x86_64'},
        {'name': 'Windows', 'version': '10.0'},
        {'name': 'Windows', 'version': '11.0'},
        {'name': 'Windows', 'version': '7.0'},
        {'name': 'Windows', 'version': '8.1'},
        {'name': 'Macintosh', 'version': '10.15.7'},
        {'name': 'Macintosh', 'version': '11.6.8'},
        {'name': 'Macintosh', 'version': '12.4'},
        {'name': 'Macintosh', 'version': '13.2'},
        {'name': 'Linux', 'version': 'x86_64'},
        {'name': 'Linux', 'version': 'arm64'},
        {'name': 'Linux', 'version': 'i386'},
        {'name': 'Linux', 'version': 'aarch64'},
        {'name': 'Linux', 'version': 'ppc64le'},
        {'name': 'Linux', 'version': 's390x'},
        {'name': 'Windows', 'version': 'XP'},
        {'name': 'Windows', 'version': '2003'},
        {'name': 'Windows', 'version': '2008'},
        {'name': 'Windows', 'version': '2012'},
        {'name': 'Windows', 'version': '2016'},
        {'name': 'Windows', 'version': '2019'},
        {'name': 'Windows', 'version': '2022'},
        {'name': 'Macintosh', 'version': '10.14.6'},
        {'name': 'Macintosh', 'version': '10.13.6'},
        {'name': 'Macintosh', 'version': '10.12.6'},
        {'name': 'Macintosh', 'version': '10.11.6'},
        {'name': 'Macintosh', 'version': '10.10.5'},
        {'name': 'Linux', 'version': 'armv7l'},
        {'name': 'Linux', 'version': 'mips64'},
        {'name': 'Linux', 'version': 'mips'},
        {'name': 'Linux', 'version': 'sparc64'},
        {'name': 'Linux', 'version': 'riscv64'},
    ]

    # Mobile device operating systems list
    MOBILE_OS_LIST = [
        {
            'name': 'Android',
            'version': '10',
            'device': 'SM-G970F',  # Samsung Galaxy S10e
        },
        {
            'name': 'Android',
            'version': '11',
            'device': 'SM-G991B',  # Samsung Galaxy S21
        },
        {
            'name': 'Android',
            'version': '12',
            'device': 'Pixel 6',  # Google Pixel 6
        },
        {
            'name': 'Android',
            'version': '13',
            'device': 'Pixel 7',  # Google Pixel 7
        },
        {
            'name': 'iOS',
            'version': '15.4',
            'device': 'iPhone13,1',  # iPhone 12 Mini
        },
        {
            'name': 'iOS',
            'version': '16.3',
            'device': 'iPhone14,7',  # iPhone 14
        },
        {
            'name': 'iOS',
            'version': '17.0',
            'device': 'iPhone15,4',  # iPhone 15
        },
        {'name': 'Android', 'version': '10', 'device': 'SM-G970F'},
        {'name': 'Android', 'version': '11', 'device': 'SM-G991B'},
        {'name': 'Android', 'version': '12', 'device': 'Pixel 6'},
        {'name': 'Android', 'version': '13', 'device': 'Pixel 7'},
        {'name': 'Android', 'version': '14', 'device': 'SM-S918B'},
        {'name': 'Android', 'version': '15', 'device': 'SM-F946U'},
        {'name': 'iOS', 'version': '15.4', 'device': 'iPhone13,1'},
        {'name': 'iOS', 'version': '16.3', 'device': 'iPhone14,7'},
        {'name': 'iOS', 'version': '17.0', 'device': 'iPhone15,4'},
        {'name': 'iOS', 'version': '18.0', 'device': 'iPhone16,1'},
        {'name': 'Android', 'version': '5', 'device': 'SM-G925F'},
        {'name': 'Android', 'version': '4', 'device': 'SM-G910F'},
        {'name': 'Android', 'version': '3', 'device': 'SM-G710F'},
        {'name': 'Android', 'version': '2', 'device': 'SM-G610F'},
        {'name': 'iOS', 'version': '10.0', 'device': 'iPhone9,1'},
        {'name': 'iOS', 'version': '9.0', 'device': 'iPhone8,1'},
        {'name': 'iOS', 'version': '8.0', 'device': 'iPhone7,2'},
        {'name': 'iOS', 'version': '7.0', 'device': 'iPhone6,1'},
        {'name': 'iOS', 'version': '6.0', 'device': 'iPhone5,1'},
        {'name': 'iOS', 'version': '5.0', 'device': 'iPhone4,1'},
    ]

    # Common browser versions
    CHROME_VERSIONS = [
        '110.0.5481.178',
        '111.0.5563.147',
        '112.0.5615.138',
        '113.0.5672.127',
        '114.0.5735.199',
        '115.0.5790.171',
        '116.0.5845.187',
        '117.0.5938.132',
        '118.0.5993.88',
        '119.0.6045.106',
        '120.0.6099.129',
        '121.0.6167.139',
        '122.0.6261.69',
        '123.0.6312.86',
        '124.0.6367.62',
        '125.0.6422.76',
        '126.0.6478.55'
        '127.0.6539.110',
        '128.0.6597.150',
        '129.0.6655.200',
        '130.0.6723.100',
        '131.0.6781.150',
        '132.0.6839.200',
        '133.0.6897.250',
        '134.0.6955.300',
        '135.0.7013.350',
        '136.0.7071.400',
    ]

    # Edge versions
    EDGE_VERSIONS = [
        '110.0.1587.69',
        '111.0.1661.54',
        '112.0.1722.64',
        '113.0.1774.57',
        '114.0.1823.67',
        '115.0.1901.188',
        '116.0.1938.69',
        '117.0.2045.47',
        '118.0.2088.69',
        '119.0.2151.58',
        '120.0.2210.89',
        '121.0.2277.98',
        '122.0.2365.59',
        '123.0.2420.53',
        '124.0.2478.49',
        '125.0.2535.33',
        '126.0.2592.20'
        '127.0.2653.75',
        '128.0.2705.100',
        '129.0.2757.150',
    ]

    # Common languages
    LANGUAGES = [
        'en-US,en;q=0.9',
        'en-GB,en;q=0.9',
        'zh-CN,zh;q=0.9,en;q=0.8',
        'ja-JP,ja;q=0.9,en;q=0.8',
        'es-ES,es;q=0.9,en;q=0.8',
        'fr-FR,fr;q=0.9,en;q=0.8',
        'de-DE,de;q=0.9,en;q=0.8',
        'ru-RU,ru;q=0.9,en;q=0.8',
        'pt-BR,pt;q=0.9,en;q=0.8',
        'it-IT,it;q=0.9,en;q=0.8',
        'ko-KR,ko;q=0.9,en;q=0.8',
        'nl-NL,nl;q=0.9,en;q=0.8',
        'sv-SE,sv;q=0.9,en;q=0.8',
        'pl-PL,pl;q=0.9,en;q=0.8',
        'tr-TR,tr;q=0.9,en;q=0.8',
        'ar-SA,ar;q=0.9,en;q=0.8',  # Arabic (Saudi Arabia)
        'he-IL,he;q=0.9,en;q=0.8',  # Hebrew (Israel)
        'el-GR,el;q=0.9,en;q=0.8',  # Greek (Greece)
        'hu-HU,hu;q=0.9,en;q=0.8',  # Hungarian (Hungary)
        'ro-RO,ro;q=0.9,en;q=0.8',  # Romanian (Romania)
        'bg-BG,bg;q=0.9,en;q=0.8',  # Bulgarian (Bulgaria)
        'cs-CZ,cs;q=0.9,en;q=0.8',  # Czech (Czech Republic)
        'sk-SK,sk;q=0.9,en;q=0.8',  # Slovak (Slovakia)
        'th-TH,th;q=0.9,en;q=0.8',  # Thai (Thailand)
        'vi-VN,vi;q=0.9,en;q=0.8',  # Vietnamese (Vietnam)
        'uk-UA,uk;q=0.9,en;q=0.8',  # Ukrainian (Ukraine)
        'hr-HR,hr;q=0.9,en;q=0.8',  # Croatian (Croatia)
        'sr-RS,sr;q=0.9,en;q=0.8',  # Serbian (Serbia)
        'ms-MY,ms;q=0.9,en;q=0.8',  # Malay (Malaysia)
        'id-ID,id;q=0.9,en;q=0.8',  # Indonesian (Indonesia)
        'fi-FI,fi;q=0.9,en;q=0.8',  # Finnish (Finland)
        'sv-SE,sv;q=0.9,en;q=0.8',  # Swedish (Sweden)
        'da-DK,da;q=0.9,en;q=0.8',  # Danish (Denmark)
        'no-NO,no;q=0.9,en;q=0.8',  # Norwegian (Norway)
        'nl-BE,nl;q=0.9,en;q=0.8',  # Dutch (Belgium)
        'fr-BE,fr;q=0.9,en;q=0.8',  # French (Belgium)
        'de-BE,de;q=0.9,en;q=0.8',  # German (Belgium)
        'it-CH,it;q=0.9,en;q=0.8',  # Italian (Switzerland)
        'fr-CH,fr;q=0.9,en;q=0.8',  # French (Switzerland)
        'de-CH,de;q=0.9,en;q=0.8',  # German (Switzerland)
        'pt-PT,pt;q=0.9,en;q=0.8',  # Portuguese (Portugal)
        'zh-TW,zh;q=0.9,en;q=0.8',  # Chinese (Taiwan)
        'zh-HK,zh;q=0.9,en;q=0.8',  # Chinese (Hong Kong)
        'fa-IR,fa;q=0.9,en;q=0.8',  # Persian (Iran)
        'tr-TR,tr;q=0.9,en;q=0.8',  # Turkish (Turkey)
        'pl-PL,pl;q=0.9,en;q=0.8',  # Polish (Poland)
        'cs-CZ,cs;q=0.9,en;q=0.8',  # Czech (Czech Republic)
        'et-EE,et;q=0.9,en;q=0.8',  # Estonian (Estonia)
        'lv-LV.lv;q=0.9,en;q=0.8',  # Latvian (Latvia)
        'lt-LT,lt;q=0.9,en;q=0.8',  # Lithuanian (Lithuania)
        'ka-GE,ka;q=0.9,en;q=0.8',  # Georgian (Georgia)
        'hy-AM,hy;q=0.9,en;q=0.8',  # Armenian (Armenia)
        'az-AZ,az;q=0.9,en;q=0.8',  # Azerbaijani (Azerbaijan)
        'mn-MN,mn;q=0.9,en;q=0.8',  # Mongolian (Mongolia)
        'ku-IQ,ku;q=0.9,en;q=0.8',  # Kurdish (Iraq)
        'mk-MK,mk;q=0.9,en;q=0.8',  # Macedonian (North Macedonia)
        'sq-AL,sq;q=0.9,en;q=0.8',  # Albanian (Albania)
        'mt-MT,mt;q=0.9,en;q=0.8',  # Maltese (Malta)
        'is-IS,is;q=0.9,en;q=0.8',  # Icelandic (Iceland)
        'ga-IE,ga;q=0.9,en;q=0.8',  # Irish (Ireland)
        'gd-GB,gd;q=0.9,en;q=0.8',  # Scottish Gaelic (UK)
        'cy-GB,cy;q=0.9,en;q=0.8',  # Welsh (UK)
        'br-FR,br;q=0.9,en;q=0.8',  # Breton (France)
        'eu-ES,eu;q=0.9,en;q=0.8',  # Basque (Spain)
        'ca-ES,ca;q=0.9,en;q=0.8',  # Catalan (Spain)
        'gl-ES,gl;q=0.9,en;q=0.8',  # Galician (Spain)
        'eo,en;q=0.9',  # Esperanto
        'af-ZA,af;q=0.9,en;q=0.8',  # Afrikaans (South Africa)
        'xh-ZA,xh;q=0.9,en;q=0.8',  # Xhosa (South Africa)
        'zu-ZA,zu;q=0.9,en;q=0.8',  # Zulu (South Africa)
        'st-ZA,st;q=0.9,en;q=0.8',  # Sotho (South Africa)
        'tn-ZA,tn;q=0.9,en;q=0.8',  # Tswana (South Africa)
        'ss-ZA,ss;q=0.9,en;q=0.8',  # Swati (South Africa)
        've-ZA,ve;q=0.9,en;q=0.8',  # Venda (South Africa)
        'nso-ZA,nso;q=0.9,en;q=0.8',  # Northern Sotho (South Africa)
        'tg-TJ,tg;q=0.9,en;q=0.8',  # Tajik (Tajikistan)
        'ps-AF,ps;q=0.9,en;q=0.8',  # Pashto (Afghanistan)
        'dv-MV,dv;q=0.9,en;q=0.8',  # Maldivian (Maldives)
        'mi-NZ,mi;q=0.9,en;q=0.8',  # Maori (New Zealand)
        'tk-TM,tk;q=0.9,en;q=0.8',  # Turkmen (Turkmenistan)
        'km-KH,km;q=0.9,en;q=0.8',  # Khmer (Cambodia)
        'lo-LA,lo;q=0.9,en;q=0.8',  # Lao (Laos)
        'my-MM,my;q=0.9,en;q=0.8',  # Burmese (Myanmar)
        'ne-NP,ne;q=0.9,en;q=0.8',  # Nepali (Nepal)
        'si-LK,si;q=0.9,en;q=0.8',  # Sinhala (Sri Lanka)
        'mn-CN,mn;q=0.9,en;q=0.8',  # Mongolian (China)
        'bo-CN,bo;q=0.9,en;q=0.8',  # Tibetan (China)
        'ug-CN,ug;q=0.9,en;q=0.8',  # Uyghur (China)
        'kk-KZ,kk;q=0.9,en;q=0.8',  # Kazakh (Kazakhstan)
        'uz-UZ,uz;q=0.9,en;q=0.8',  # Uzbek (Uzbekistan)
        'tt-RU,tt;q=0.9,en;q=0.8',  # Tatar (Russia)
        'ba-RU,ba;q=0.9,en;q=0.8',  # Bashkir (Russia)
        'cv-RU,cv;q=0.9,en;q=0.8',  # Chuvash (Russia)
        'os-RU,os;q=0.9,en;q=0.8',  # Ossetian (Russia)
        'av-RU,av;q=0.9,en;q=0.8',  # Avar (Russia)
        'ce-RU,ce;q=0.9,en;q=0.8',  # Chechen (Russia)
        'kaa-KZ,kaa;q=0.9,en;q=0.8',  # Karakalpak (Kazakhstan)
        'tr-CY,tr;q=0.9,en;q=0.8',  # Turkish (Cyprus)
        'el-CY,el;q=0.9,en;q=0.8',  # Greek (Cyprus)
        'hy-AM,hy;q=0.9,en;q=0.8',  # Armenian (Armenia)
        'ru-MD,ru;q=0.9,en;q=0.8',  # Russian (Moldova)
        'uk-MD,uk;q=0.9,en;q=0.8',  # Ukrainian (Moldova)
        'ro-MD,ro;q=0.9,en;q=0.8',  # Romanian (Moldova)
        'tr-DE,tr;q=0.9,en;q=0.8',  # Turkish (Germany)
        'ar-DE,ar;q=0.9,en;q=0.8',  # Arabic (Germany)
        'ru-DE,ru;q=0.9,en;q=0.8',  # Russian (Germany)
        'es-DE,es;q=0.9,en;q=0.8',  # Spanish (Germany)
        'it-DE,it;q=0.9,en;q=0.8',  # Italian (Germany)
        'pl-DE,pl;q=0.9,en;q=0.8',  # Polish (Germany)
        'tr-FR,tr;q=0.9,en;q=0.8',  # Turkish (France)
        'ar-FR,ar;q=0.9,en;q=0.8',  # Arabic (France)
        'ru-FR,ru;q=0.9,en;q=0.8',  # Russian (France)
        'es-FR,es;q=0.9,en;q=0.8',  # Spanish (France)
        'it-FR,it;q=0.9,en;q=0.8',  # Italian (France)
        'pl-FR,pl;q=0.9,en;q=0.8',  # Polish (France)
        'tr-GB,tr;q=0.9,en;q=0.8',  # Turkish (UK)
        'ar-GB,ar;q=0.9,en;q=0.8',  # Arabic (UK)
        'ru-GB,ru;q=0.9,en;q=0.8',  # Russian (UK)
        'es-GB,es;q=0.9,en;q=0.8',  # Spanish (UK)
        'it-GB,it;q=0.9,en;q=0.8',  # Italian (UK)
        'pl-GB,pl;q=0.9,en;q=0.8',  # Polish (UK)
        'tr-US,tr;q=0.9,en;q=0.8',  # Turkish (US)
        'ar-US,ar;q=0.9,en;q=0.8',  # Arabic (US)
        'ru-US,ru;q=0.9,en;q=0.8',  # Russian (US)
        'es-US,es;q=0.9,en;q=0.8',  # Spanish (US)
        'it-US,it;q=0.9,en;q=0.8',  # Italian (US)
        'pl-US,pl;q=0.9,en;q=0.8',  # Polish (US)
        'tr-CA,tr;q=0.9,en;q=0.8',  # Turkish (Canada)
        'ar-CA,ar;q=0.9,en;q=0.8',  # Arabic (Canada)
        'ru-CA,ru;q=0.9,en;q=0.8',  # Russian (Canada)
        'es-CA,es;q=0.9,en;q=0.8',  # Spanish (Canada)
        'it-CA,it;q=0.9,en;q=0.8',  # Italian (Canada)
        'pl-CA,pl;q=0.9,en;q=0.8',  # Polish (Canada)
        'tr-AU,tr;q=0.9,en;q=0.8',  # Turkish (Australia)
        'ar-AU,ar;q=0.9,en;q=0.8',  # Arabic (Australia)
        'ru-AU,ru;q=0.9,en;q=0.8',  # Russian (Australia)
        'es-AU,es;q=0.9,en;q=0.8',  # Spanish (Australia)
        'it-AU,it;q=0.9,en;q=0.8',  # Italian (Australia)
        'pl-AU,pl;q=0.9,en;q=0.8',  # Polish (Australia)
        'tr-NZ,tr;q=0.9,en;q=0.8',  # Turkish (New Zealand)
        'ar-NZ,ar;q=0.9,en;q=0.8',  # Arabic (New Zealand)
    ]

    # Common WebGL vendors and renderers
    WEBGL_VENDORS = [
        'Google Inc. (NVIDIA)',
        'Google Inc. (Intel)',
        'Google Inc. (AMD)',
        'Google Inc. (Apple)',
        'Microsoft Corporation (NVIDIA)',
        'Microsoft Corporation (Intel)',
        'Microsoft Corporation (AMD)',
        'Apple Computer, Inc.',
        'NVIDIA Corporation',
        'Intel Inc.',
        'AMD Inc.',
        'Qualcomm Incorporated',
        'ARM Limited',
        'Imagination Technologies',
        'Broadcom Inc.',
        'NXP Semiconductors',
        'Texas Instruments Incorporated',
        'Samsung Electronics Co., Ltd.',
        'AMD Inc. (NVIDIA)',
        'AMD Inc. (Intel)',
        'AMD Inc. (Qualcomm)',
        'Hisilicon Technologies Co., Ltd.',
        'Rockchip Electronics Co., Ltd.',
        'MediaTek Inc.',
        'Intel Inc. (AMD)',
        'Intel Inc. (Qualcomm)',
        'NVIDIA Corporation (AMD)',
        'NVIDIA Corporation (Qualcomm)',
        'Google Inc. (Broadcom)',
        'Google Inc. (Texas Instruments)',
        'Microsoft Corporation (ARM)',
        'Microsoft Corporation (Samsung)',
        'Apple Inc. (NVIDIA)',
        'Apple Inc. (Intel)',
        'Apple Inc. (AMD)',
        'Mozilla Corporation',
        'Opera Software',
        'Adobe Systems Incorporated',
        'Unity Technologies',
        'Epic Games',
        'Amazon.com, Inc.',
        'Facebook, Inc.',
        'Google Inc. (Samsung)',
        'Google Inc. (MediaTek)',
        'Google Inc. (Hisilicon)',
        'Google Inc. (Rockchip)',
    ]

    WEBGL_RENDERERS = [
        'ANGLE (NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (NVIDIA GeForce GTX 1660 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX 6800 XT Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)',
        'Metal GPU Family Apple 8 (Apple M1)',
        'Metal GPU Family Apple 7 (Apple A14)',
        'ANGLE (Apple M2 GPU Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon R9 390 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Intel(R) HD Graphics 530 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Qualcomm Adreno 650 Direct3D11 vs_6_0 ps_6_0)',
        'ANGLE (ARM Mali-G76 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Imagination PowerVR GMA 2500 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Broadcom VideoCore IV Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (NXP i.MX6 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Texas Instruments AM62x Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Samsung Exynos Mali-T880 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon Vega 8 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 11 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Hisilicon Kirin 970 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Rockchip RK3399 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (MediaTek MT8173 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Intel(R) Iris(TM) Plus Graphics Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (NVIDIA GeForce GTX 1050 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (NVIDIA GeForce GTX 950 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (NVIDIA Tegra X1 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (NVIDIA Tegra K1 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7750 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7870 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Broadcom VideoCore IV Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Texas Instruments AM5728 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Samsung Exynos 5420 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX 560 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX 460 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX 550 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 3 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 5 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 7 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 9 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX 540 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX 530 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX 520 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX 570 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 11 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon Vega Frontier Edition Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega M GL Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon Pro Duo Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 64 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 56 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 33 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 31 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 30 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 20 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon RX Vega 10 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7990 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7970 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7950 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7890 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7870 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7850 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7830 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7770 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7750 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7730 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7710 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7670 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7650 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7630 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7610 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7570 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7550 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7530 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7510 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7490 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7470 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7450 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7430 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7400 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7390 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7370 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7350 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7330 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7300 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7290 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7270 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7260 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7250 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7230 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7210 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7200 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7190 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7180 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7170 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7160 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7150 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7140 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7130 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7120 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7110 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7100 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7090 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7080 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7070 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7060 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7050 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7040 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7030 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7020 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD Radeon HD 7010 Direct3D11 vs_5_0 ps_5_0)',
    ]

    @staticmethod
    def _generate_random_id() -> str:
        """Generate a random unique identifier"""
        return str(uuid.uuid4())

    @staticmethod
    def _random_viewport_size() -> Dict[str, int]:
        """Generate a random viewport size"""
        common_widths = [1366, 1440, 1536, 1600, 1920, 2560]
        common_heights = [768, 900, 864, 1024, 1080, 1440]

        width = random.choice(common_widths)
        height = random.choice(common_heights)

        return {"width": width, "height": height}

    @staticmethod
    def _generate_user_agent(
        os_info: Dict[str, str],
        browser_type: str,
        browser_version: str,
        is_mobile: bool = False,
    ) -> str:
        """
        Generate User-Agent based on operating system information and browser
        version
        """
        ua = None
        if is_mobile:
            if os_info['name'] == 'Android':
                ua = (
                    f"Mozilla/5.0 (Linux; Android {os_info['version']}; "
                    f"{os_info['device']}) "
                    f"AppleWebKit/537.36 (KHTML, like Gecko) "
                    f"Chrome/{browser_version} Mobile Safari/537.36"
                )
            elif os_info['name'] == 'iOS':
                ios_version = os_info['version'].replace('.', '_')
                ua = (
                    f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version} "
                    f"like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    f"Version/16.0 Mobile/15E148 Safari/604.1"
                )
        else:
            base_ua = ""
            if os_info['name'] == 'Windows':
                base_ua = (
                    f"Mozilla/5.0 (Windows NT {os_info['version']}; "
                    f"Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                )
            elif os_info['name'] == 'Macintosh':
                base_ua = (
                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X "
                    f"{os_info['version'].replace('.', '_')}) "
                    f"AppleWebKit/537.36 (KHTML, like Gecko) "
                )
            else:
                base_ua = (
                    f"Mozilla/5.0 (X11; Linux {os_info['version']}) "
                    f"AppleWebKit/537.36 (KHTML, like Gecko) "
                )
            if browser_type.lower() == 'chrome':
                ua = f"{base_ua}Chrome/{browser_version} Safari/537.36"
            elif browser_type.lower() == 'edge':
                ua = (
                    f"{base_ua}Chrome/{browser_version} Safari/537.36 "
                    f"Edg/{browser_version}"
                )
            else:
                ua = (
                    f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    f"AppleWebKit/537.36 (KHTML, like Gecko) "
                    f"Chrome/{browser_version} Safari/537.36"
                )
        return ua

    def generate_fingerprint(
        self,
        browser_type: str = 'chrome',
        is_mobile: bool = False,
    ) -> Dict[str, Union[str, Dict, List]]:
        """
        Generate a complete browser fingerprint configuration

        Args:
            browser_type (str): Browser type, 'chrome' or 'edge'
            is_mobile (bool): Whether to generate mobile device fingerprint

        Returns:
            Dict: Dictionary containing complete fingerprint information
        """
        # Randomly select operating system
        if is_mobile:
            os_info = random.choice(self.MOBILE_OS_LIST)
        else:
            os_info = random.choice(self.OS_LIST)

        # Select version based on browser type
        if browser_type.lower() == 'edge':
            browser_version = random.choice(self.EDGE_VERSIONS)
        else:
            browser_version = random.choice(self.CHROME_VERSIONS)

        # Generate User-Agent string
        user_agent = self._generate_user_agent(
            os_info,
            browser_type,
            browser_version,
            is_mobile,
        )

        # Generate random viewport size
        if is_mobile:
            viewport = {
                "width": random.choice([360, 375, 390, 414, 428]),
                "height": random.choice([
                    640, 720, 780, 844, 926
                ]),
            }
        else:
            viewport = self._random_viewport_size()

        # Generate fingerprint data
        fingerprint = {
            "id": self._generate_random_id(),
            "user_agent": user_agent,
            "language": random.choice(self.LANGUAGES),
            "color_depth": random.choice([24, 30, 32]),
            "device_memory": (
                random.choice([2, 4, 8]) if is_mobile else random.choice([
                    2, 4, 8, 16
                ])
            ),
            "hardware_concurrency": (
                random.choice([2, 4, 6, 8]) if is_mobile else random.choice([
                    2, 4, 6, 8, 12, 16
                ])
            ),
            "viewport": viewport,
            "platform": (
                "Android" if os_info.get('name') == 'Android' else (
                    "iPhone" if os_info.get('name') == 'iOS'
                    else os_info['name']
                )
            ),
            "plugins": [],  # Default to empty array
            "timezone": random.choice([
                -480, -420, -360, -300, -240, -180, 0, 60, 120, 180,
                240, 300, 360, 480, 540
            ]),
            "webgl": {
                "vendor": random.choice(self.WEBGL_VENDORS),
                "renderer": random.choice(self.WEBGL_RENDERERS),
            },
            "do_not_track": random.choice(["1", "0", None]),
            "canvas_fingerprint": ''.join(
                random.choices(string.ascii_letters + string.digits, k=64)
            ),
            "audio_fingerprint": ''.join(
                random.choices(string.ascii_letters + string.digits, k=64)
            ),
            "fonts": [],  # Default to empty array
            "is_mobile": is_mobile,
            "mobile_info": os_info if is_mobile else None,
        }

        return fingerprint

    @staticmethod
    def get_fingerprint_arguments(
        fingerprint: Dict[str, any],
        browser_type: str = 'chrome',
    ) -> List[str]:
        """
        Convert fingerprint to command line argument list
        """
        args = []
        args.append(f"--user-agent={fingerprint['user_agent']}")
        args.append(f"--lang={fingerprint['language'].split(',')[0]}")
        args.append(
            f"--js-flags=--cpu-count={fingerprint['hardware_concurrency']}"
        )
        args.append(
            f"--window-size={fingerprint['viewport']['width']},"
            f"{fingerprint['viewport']['height']}"
        )
        args.append(f"--platform={fingerprint['platform']}")
        if browser_type.lower() == 'chrome':
            args.append("--disable-blink-features=AutomationControlled")
        elif browser_type.lower() == 'edge':
            args.append("--disable-blink-features=AutomationControlled")
            args.append("--edge-compat")
        return args


def generate_fingerprint_js(fingerprint: Dict[str, any]) -> str:
    """
    Generate JavaScript code to inject into browser, to override fingerprint
    attributes

    Args:
        fingerprint (Dict): Fingerprint data

    Returns:
        str: JavaScript injection code
    """
    fingerprint_json = json.dumps(fingerprint)
    js_template = """
    (function() {
        const fingerprint = JSON_DATA;

        // Override navigator attributes
        Object.defineProperty(navigator, 'userAgent', {
            value: fingerprint.user_agent
        });
        Object.defineProperty(navigator, 'languages', {
            value: [fingerprint.language.split(',')[0]]
        });
        Object.defineProperty(navigator, 'platform', {
            value: fingerprint.platform
        });
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            value: fingerprint.hardware_concurrency
        });
        Object.defineProperty(navigator, 'deviceMemory', {
            value: fingerprint.device_memory
        });

        if (fingerprint.do_not_track !== null) {
            Object.defineProperty(navigator, 'doNotTrack', {
                value: fingerprint.do_not_track
            });
        }

        // Override screen attributes
        Object.defineProperty(screen, 'width', {
            value: fingerprint.viewport.width
        });
        Object.defineProperty(screen, 'height', {
            value: fingerprint.viewport.height
        });
        Object.defineProperty(screen, 'colorDepth', {
            value: fingerprint.color_depth
        });

        // Enhance WebGL spoofing
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // UNMASKED_VENDOR_WEBGL
            if (parameter === 37445) {
                return fingerprint.webgl.vendor;
            }
            // UNMASKED_RENDERER_WEBGL
            if (parameter === 37446) {
                return fingerprint.webgl.renderer;
            }
            // MAX_TEXTURE_SIZE
            if (parameter === 3379) {
                return 16384;
            }
            // MAX_VIEWPORT_DIMS
            if (parameter === 3386) {
                return [32767, 32767];
            }
            // ALIASED_LINE_WIDTH_RANGE
            if (parameter === 33902) {
                return [1, 1];
            }
            // ALIASED_POINT_SIZE_RANGE
            if (parameter === 33901) {
                return [1, 1024];
            }
            return getParameter.call(this, parameter);
        };

        // Enhance WebGL2 spoofing
        if (typeof WebGL2RenderingContext !== 'undefined') {
            const getParameterWebGL2 =
                WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter =
                function(parameter) {
                // Reuse same parameter processing logic
                if (parameter === 37445 || parameter === 37446 ||
                    parameter === 3379 || parameter === 3386 ||
                    parameter === 33902 || parameter === 33901) {
                    return WebGLRenderingContext.prototype.getParameter.call(
                        this, parameter
                    );
                }
                return getParameterWebGL2.call(this, parameter);
            };
        }

        // Override Canvas fingerprint
        const oldToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            if (this.width > 5 && this.height > 5) {
                // Only modify possible canvas used for fingerprint recognition
                const modifiedDataURL = oldToDataURL.call(this, type);
                // Add small change to make each time different but visually
                // similar
                return modifiedDataURL.slice(0, modifiedDataURL.length - 8) +
                    fingerprint.canvas_fingerprint.slice(0, 8);
            }
            return oldToDataURL.call(this, type);
        };

        // Override AudioContext fingerprint
        const oldGetChannelData = AudioBuffer.prototype.getChannelData;
        AudioBuffer.prototype.getChannelData = function() {
            const array = oldGetChannelData.apply(this, arguments);
            // Only modify data used for audio fingerprint
            if (array.length > 100) {
                // Add small change
                const fingerprint_seed = parseInt(
                    fingerprint.audio_fingerprint.slice(0, 8), 16
                );
                for (let i = 0; i < 8; i++) {
                    const index = Math.floor(array.length / 8 * i);
                    array[index] = array[index] + (
                        fingerprint_seed % 100
                    ) / 1000000;
                }
            }
            return array;
        };

        // Modify plugin information
        Object.defineProperty(navigator, 'plugins', {
            get: function() {
                const plugins = fingerprint.plugins.length > 0
                    ? fingerprint.plugins
                    : [];
                const pluginArray = Array.from(plugins);
                pluginArray.item = function(index) {
                    return this[index];
                };
                pluginArray.namedItem = function(name) {
                    return this.find(plugin => plugin.name === name);
                };
                return pluginArray;
            }
        });

        // Prevent Automation detection
        window.navigator.webdriver = false;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    })();
    """

    # Use safer JSON replacement method
    js_code = js_template.replace("JSON_DATA", fingerprint_json)

    return js_code


class FingerprintManager:
    """
    Class for managing browser fingerprints.

    Responsible for generating, storing, and applying browser fingerprint 
    configurations.
    """

    def __init__(self):
        """Initialize fingerprint manager"""
        self.generator = FingerprintGenerator()
        self.current_fingerprint = None

    def generate_new_fingerprint(
        self,
        browser_type: str = 'chrome',
        is_mobile: bool = False,
    ) -> Dict[str, any]:
        """
        Generate new browser fingerprint

        Args:
            browser_type (str): Browser type, 'chrome' or 'edge'
            is_mobile (bool): Whether to generate mobile device fingerprint

        Returns:
            Dict: Newly generated fingerprint data
        """
        self.current_fingerprint = self.generator.generate_fingerprint(
            browser_type, is_mobile
        )
        return self.current_fingerprint

    def get_fingerprint_arguments(
        self,
        browser_type: str = 'chrome',
    ) -> List[str]:
        """
        Get command line arguments for current fingerprint

        Args:
            browser_type (str): Browser type

        Returns:
            List[str]: List of command line arguments
        """
        if not self.current_fingerprint:
            self.generate_new_fingerprint(browser_type)

        return self.generator.get_fingerprint_arguments(
            self.current_fingerprint,
            browser_type,
        )

    def get_fingerprint_js(self) -> str:
        """
        Get JavaScript injection code for current fingerprint

        Returns:
            str: JavaScript code to inject
        """
        if not self.current_fingerprint:
            self.generate_new_fingerprint()

        return generate_fingerprint_js(self.current_fingerprint)


# Create global singleton instance
FINGERPRINT_MANAGER = FingerprintManager()
