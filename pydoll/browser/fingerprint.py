import random
import string
import json
import uuid
import platform
from typing import Dict, List, Union, Optional


class FingerprintGenerator:
    """
    生成浏览器指纹伪装数据的类。
    
    该类负责生成唯一不重复的浏览器指纹，用于每次会话中伪装浏览器环境，
    避免跟踪和指纹识别。
    """
    
    # 常用的操作系统列表
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
    
    # 移动设备操作系统列表
    MOBILE_OS_LIST = [
        {'name': 'Android', 'version': '10', 'device': 'SM-G970F'},  # Samsung Galaxy S10e
        {'name': 'Android', 'version': '11', 'device': 'SM-G991B'},  # Samsung Galaxy S21
        {'name': 'Android', 'version': '12', 'device': 'Pixel 6'},   # Google Pixel 6
        {'name': 'Android', 'version': '13', 'device': 'Pixel 7'},   # Google Pixel 7
        {'name': 'iOS', 'version': '15.4', 'device': 'iPhone13,1'},  # iPhone 12 Mini
        {'name': 'iOS', 'version': '16.3', 'device': 'iPhone14,7'},  # iPhone 14
        {'name': 'iOS', 'version': '17.0', 'device': 'iPhone15,4'},  # iPhone 15
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
    
    # 常用的浏览器版本
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
    
    # Edge版本
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
    
    # 常用的语言
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
        'ar-SA,ar;q=0.9,en;q=0.8',  # 阿拉伯语（沙特阿拉伯）
        'he-IL,he;q=0.9,en;q=0.8',  # 希伯来语（以色列）
        'el-GR,el;q=0.9,en;q=0.8',  # 希腊语（希腊）
        'hu-HU,hu;q=0.9,en;q=0.8',  # 匈牙利语（匈牙利）
        'ro-RO,ro;q=0.9,en;q=0.8',  # 罗马尼亚语（罗马尼亚）
        'bg-BG,bg;q=0.9,en;q=0.8',  # 保加利亚语（保加利亚）
        'cs-CZ,cs;q=0.9,en;q=0.8',  # 捷克语（捷克）
        'sk-SK,sk;q=0.9,en;q=0.8',  # 斯洛伐克语（斯洛伐克）
        'th-TH,th;q=0.9,en;q=0.8',  # 泰语（泰国）
        'vi-VN,vi;q=0.9,en;q=0.8',  # 越南语（越南）
        'uk-UA,uk;q=0.9,en;q=0.8',  # 乌克兰语（乌克兰）
        'hr-HR,hr;q=0.9,en;q=0.8',  # 克罗地亚语（克罗地亚）
        'sr-RS,sr;q=0.9,en;q=0.8',  # 塞尔维亚语（塞尔维亚）
        'ms-MY,ms;q=0.9,en;q=0.8',  # 马来语（马来西亚）
        'id-ID,id;q=0.9,en;q=0.8',  # 印尼语（印尼）
        'fi-FI,fi;q=0.9,en;q=0.8',  # 芬兰语（芬兰）
        'sv-SE,sv;q=0.9,en;q=0.8',  # 瑞典语（瑞典）
        'da-DK,da;q=0.9,en;q=0.8',  # 丹麦语（丹麦）
        'no-NO,no;q=0.9,en;q=0.8',  # 挪威语（挪威）
        'nl-BE,nl;q=0.9,en;q=0.8',  # 荷兰语（比利时）
        'fr-BE,fr;q=0.9,en;q=0.8',  # 法语（比利时）
        'de-BE,de;q=0.9,en;q=0.8',  # 德语（比利时）
        'it-CH,it;q=0.9,en;q=0.8',  # 意大利语（瑞士）
        'fr-CH,fr;q=0.9,en;q=0.8',  # 法语（瑞士）
        'de-CH,de;q=0.9,en;q=0.8',  # 德语（瑞士）
        'pt-PT,pt;q=0.9,en;q=0.8',  # 葡萄牙语（葡萄牙）
        'zh-TW,zh;q=0.9,en;q=0.8',  # 中文（台湾）
        'zh-HK,zh;q=0.9,en;q=0.8',  # 中文（香港）
        'fa-IR,fa;q=0.9,en;q=0.8',  # 波斯语（伊朗）
        'tr-TR,tr;q=0.9,en;q=0.8',  # 土耳其语（土耳其）
        'pl-PL,pl;q=0.9,en;q=0.8',  # 波兰语（波兰）
        'cs-CZ,cs;q=0.9,en;q=0.8',  # 捷克语（捷克）
        'et-EE,et;q=0.9,en;q=0.8',  # 爱沙尼亚语（爱沙尼亚）
        'lv-LV.lv;q=0.9,en;q=0.8',  # 拉脱维亚语（拉脱维亚）
        'lt-LT,lt;q=0.9,en;q=0.8',  # 立陶宛语（立陶宛）
        'ka-GE,ka;q=0.9,en;q=0.8',  # 格鲁吉亚语（格鲁吉亚）
        'hy-AM,hy;q=0.9,en;q=0.8',  # 亚美尼亚语（亚美尼亚）
        'az-AZ,az;q=0.9,en;q=0.8',  # 阿塞拜疆语（阿塞拜疆）
        'mn-MN,mn;q=0.9,en;q=0.8',  # 蒙古语（蒙古）
        'ku-IQ,ku;q=0.9,en;q=0.8',  # 库尔德语（伊拉克）
        'mk-MK,mk;q=0.9,en;q=0.8',  # 马其顿语（北马其顿）
        'sq-AL,sq;q=0.9,en;q=0.8',  # 阿尔巴尼亚语（阿尔巴尼亚）
        'mt-MT,mt;q=0.9,en;q=0.8',  # 马耳他语（马耳他）
        'is-IS,is;q=0.9,en;q=0.8',  # 冰岛语（冰岛）
        'ga-IE,ga;q=0.9,en;q=0.8',  # 爱尔兰语（爱尔兰）
        'gd-GB,gd;q=0.9,en;q=0.8',  # 苏格兰盖尔语（英国）
        'cy-GB,cy;q=0.9,en;q=0.8',  # 威尔士语（英国）
        'br-FR,br;q=0.9,en;q=0.8',  # 布列塔尼语（法国）
        'eu-ES,eu;q=0.9,en;q=0.8',  # 巴斯克语（西班牙）
        'ca-ES,ca;q=0.9,en;q=0.8',  # 加泰罗尼亚语（西班牙）
        'gl-ES,gl;q=0.9,en;q=0.8',  # 加利西亚语（西班牙）
        'eo,en;q=0.9',  # 世界语
        'af-ZA,af;q=0.9,en;q=0.8',  # 南非荷兰语（南非）
        'xh-ZA,xh;q=0.9,en;q=0.8',  # 科萨语（南非）
        'zu-ZA,zu;q=0.9,en;q=0.8',  # 祖鲁语（南非）
        'st-ZA,st;q=0.9,en;q=0.8',  # 索托语（南非）
        'tn-ZA,tn;q=0.9,en;q=0.8',  # 托瓦纳语（南非）
        'ss-ZA,ss;q=0.9,en;q=0.8',  # 史瓦蒂语（南非）
        've-ZA,ve;q=0.9,en;q=0.8',  # 瓦纳语（南非）
        'nso-ZA,nso;q=0.9,en;q=0.8',  # 北索托语（南非）
        'tg-TJ,tg;q=0.9,en;q=0.8',  # 塔吉克语（塔吉克斯坦）
        'ps-AF,ps;q=0.9,en;q=0.8',  # 普什图语（阿富汗）
        'dv-MV,dv;q=0.9,en;q=0.8',  # 马尔代夫语（马尔代夫）
        'mi-NZ,mi;q=0.9,en;q=0.8',  # 毛利语（新西兰）
        'tk-TM,tk;q=0.9,en;q=0.8',  # 土库曼语（土库曼斯坦）
        'km-KH,km;q=0.9,en;q=0.8',  # 柬埔寨语（柬埔寨）
        'lo-LA,lo;q=0.9,en;q=0.8',  # 老挝语（老挝）
        'my-MM,my;q=0.9,en;q=0.8',  # 缅甸语（缅甸）
        'ne-NP,ne;q=0.9,en;q=0.8',  # 尼泊尔语（尼泊尔）
        'si-LK,si;q=0.9,en;q=0.8',  # 锡兰语（斯里兰卡）
        'mn-CN,mn;q=0.9,en;q=0.8',  # 蒙古语（中国）
        'bo-CN,bo;q=0.9,en;q=0.8',  # 藏语（中国）
        'ug-CN,ug;q=0.9,en;q=0.8',  # 维吾尔语（中国）
        'kk-KZ,kk;q=0.9,en;q=0.8',  # 哈萨克语（哈萨克斯坦）
        'uz-UZ,uz;q=0.9,en;q=0.8',  # 乌兹别克语（乌兹别克斯坦）
        'tt-RU,tt;q=0.9,en;q=0.8',  # 鞑靼语（俄罗斯）
        'ba-RU,ba;q=0.9,en;q=0.8',  # 巴什基尔语（俄罗斯）
        'cv-RU,cv;q=0.9,en;q=0.8',  # 钦察语（俄罗斯）
        'os-RU,os;q=0.9,en;q=0.8',  # 奥塞梯语（俄罗斯）
        'av-RU,av;q=0.9,en;q=0.8',  # 阿瓦尔语（俄罗斯）
        'ce-RU,ce;q=0.9,en;q=0.8',  # 切尔克斯语（俄罗斯）
        'kaa-KZ,kaa;q=0.9,en;q=0.8',  # 卡拉卡尔帕克语（哈萨克斯坦）
        'tr-CY,tr;q=0.9,en;q=0.8',  # 土耳其语（塞浦路斯）
        'el-CY,el;q=0.9,en;q=0.8',  # 希腊语（塞浦路斯）
        'hy-AM,hy;q=0.9,en;q=0.8',  # 亚美尼亚语（亚美尼亚）
        'ru-MD,ru;q=0.9,en;q=0.8',  # 俄语（摩尔多瓦）
        'uk-MD,uk;q=0.9,en;q=0.8',  # 乌克兰语（摩尔多瓦）
        'ro-MD,ro;q=0.9,en;q=0.8',  # 罗马尼亚语（摩尔多瓦）
        'tr-DE,tr;q=0.9,en;q=0.8',  # 土耳其语（德国）
        'ar-DE,ar;q=0.9,en;q=0.8',  # 阿拉伯语（德国）
        'ru-DE,ru;q=0.9,en;q=0.8',  # 俄语（德国）
        'es-DE,es;q=0.9,en;q=0.8',  # 西班牙语（德国）
        'it-DE,it;q=0.9,en;q=0.8',  # 意大利语（德国）
        'pl-DE,pl;q=0.9,en;q=0.8',  # 波兰语（德国）
        'tr-FR,tr;q=0.9,en;q=0.8',  # 土耳其语（法国）
        'ar-FR,ar;q=0.9,en;q=0.8',  # 阿拉伯语（法国）
        'ru-FR,ru;q=0.9,en;q=0.8',  # 俄语（法国）
        'es-FR,es;q=0.9,en;q=0.8',  # 西班牙语（法国）
        'it-FR,it;q=0.9,en;q=0.8',  # 意大利语（法国）
        'pl-FR,pl;q=0.9,en;q=0.8',  # 波兰语（法国）
        'tr-GB,tr;q=0.9,en;q=0.8',  # 土耳其语（英国）
        'ar-GB,ar;q=0.9,en;q=0.8',  # 阿拉伯语（英国）
        'ru-GB,ru;q=0.9,en;q=0.8',  # 俄语（英国）
        'es-GB,es;q=0.9,en;q=0.8',  # 西班牙语（英国）
        'it-GB,it;q=0.9,en;q=0.8',  # 意大利语（英国）
        'pl-GB,pl;q=0.9,en;q=0.8',  # 波兰语（英国）
        'tr-US,tr;q=0.9,en;q=0.8',  # 土耳其语（美国）
        'ar-US,ar;q=0.9,en;q=0.8',  # 阿拉伯语（美国）
        'ru-US,ru;q=0.9,en;q=0.8',  # 俄语（美国）
        'es-US,es;q=0.9,en;q=0.8',  # 西班牙语（美国）
        'it-US,it;q=0.9,en;q=0.8',  # 意大利语（美国）
        'pl-US,pl;q=0.9,en;q=0.8',  # 波兰语（美国）
        'tr-CA,tr;q=0.9,en;q=0.8',  # 土耳其语（加拿大）
        'ar-CA,ar;q=0.9,en;q=0.8',  # 阿拉伯语（加拿大）
        'ru-CA,ru;q=0.9,en;q=0.8',  # 俄语（加拿大）
        'es-CA,es;q=0.9,en;q=0.8',  # 西班牙语（加拿大）
        'it-CA,it;q=0.9,en;q=0.8',  # 意大利语（加拿大）
        'pl-CA,pl;q=0.9,en;q=0.8',  # 波兰语（加拿大）
        'tr-AU,tr;q=0.9,en;q=0.8',  # 土耳其语（澳大利亚）
        'ar-AU,ar;q=0.9,en;q=0.8',  # 阿拉伯语（澳大利亚）
        'ru-AU,ru;q=0.9,en;q=0.8',  # 俄语（澳大利亚）
        'es-AU,es;q=0.9,en;q=0.8',  # 西班牙语（澳大利亚）
        'it-AU,it;q=0.9,en;q=0.8',  # 意大利语（澳大利亚）
        'pl-AU,pl;q=0.9,en;q=0.8',  # 波兰语（澳大利亚）
        'tr-NZ,tr;q=0.9,en;q=0.8',  # 土耳其语（新西兰）
        'ar-NZ,ar;q=0.9,en;q=0.8',  # 阿拉伯语（新西兰）
    ]
    
    # 常见的WebGL厂商与渲染器
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
        """生成随机的唯一标识符"""
        return str(uuid.uuid4())
    
    @staticmethod
    def _random_viewport_size() -> Dict[str, int]:
        """生成随机的视口大小"""
        common_widths = [1366, 1440, 1536, 1600, 1920, 2560]
        common_heights = [768, 900, 864, 1024, 1080, 1440]
        
        width = random.choice(common_widths)
        height = random.choice(common_heights)
        
        return {"width": width, "height": height}
    
    @staticmethod
    def _generate_user_agent(os_info: Dict[str, str], browser_type: str, browser_version: str, is_mobile: bool = False) -> str:
        """根据操作系统信息和浏览器版本生成User-Agent"""
        # 移动设备User-Agent
        if is_mobile:
            if os_info['name'] == 'Android':
                return f"Mozilla/5.0 (Linux; Android {os_info['version']}; {os_info['device']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Mobile Safari/537.36"
            elif os_info['name'] == 'iOS':
                # iOS版本需要将点替换为下划线
                ios_version = os_info['version'].replace('.', '_')
                return f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        
        # 桌面设备User-Agent
        if browser_type.lower() == 'chrome':
            if os_info['name'] == 'Windows':
                return f"Mozilla/5.0 (Windows NT {os_info['version']}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
            elif os_info['name'] == 'Macintosh':
                return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {os_info['version'].replace('.', '_')}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
            else:  # Linux
                return f"Mozilla/5.0 (X11; Linux {os_info['version']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
        elif browser_type.lower() == 'edge':
            if os_info['name'] == 'Windows':
                return f"Mozilla/5.0 (Windows NT {os_info['version']}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36 Edg/{browser_version}"
            elif os_info['name'] == 'Macintosh':
                return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {os_info['version'].replace('.', '_')}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36 Edg/{browser_version}"
            else:  # Linux
                return f"Mozilla/5.0 (X11; Linux {os_info['version']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36 Edg/{browser_version}"
        else:
            # 默认返回Chrome
            return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
    
    def generate_fingerprint(self, browser_type: str = 'chrome', is_mobile: bool = False) -> Dict[str, Union[str, Dict, List]]:
        """
        生成一个完整的浏览器指纹配置
        
        Args:
            browser_type (str): 浏览器类型，'chrome' 或 'edge'
            is_mobile (bool): 是否生成移动设备指纹
            
        Returns:
            Dict: 包含完整指纹信息的字典
        """
        # 随机选择操作系统
        if is_mobile:
            os_info = random.choice(self.MOBILE_OS_LIST)
        else:
            os_info = random.choice(self.OS_LIST)
        
        # 根据浏览器类型选择版本
        if browser_type.lower() == 'edge':
            browser_version = random.choice(self.EDGE_VERSIONS)
        else:
            browser_version = random.choice(self.CHROME_VERSIONS)
        
        # 生成用户代理字符串
        user_agent = self._generate_user_agent(os_info, browser_type, browser_version, is_mobile)
        
        # 生成随机视口大小
        if is_mobile:
            viewport = {"width": random.choice([360, 375, 390, 414, 428]), 
                        "height": random.choice([640, 720, 780, 844, 926])}
        else:
            viewport = self._random_viewport_size()
        
        # 生成指纹数据
        fingerprint = {
            "id": self._generate_random_id(),
            "user_agent": user_agent,
            "language": random.choice(self.LANGUAGES),
            "color_depth": random.choice([24, 30, 32]),
            "device_memory": random.choice([2, 4, 8]) if is_mobile else random.choice([2, 4, 8, 16]),
            "hardware_concurrency": random.choice([2, 4, 6, 8]) if is_mobile else random.choice([2, 4, 6, 8, 12, 16]),
            "viewport": viewport,
            "platform": "Android" if os_info.get('name') == 'Android' else 
                       ("iPhone" if os_info.get('name') == 'iOS' else os_info['name']),
            "plugins": [],  # 默认为空数组
            "timezone": random.choice([-480, -420, -360, -300, -240, -180, 0, 60, 120, 180, 240, 300, 360, 480, 540]),
            "webgl": {
                "vendor": random.choice(self.WEBGL_VENDORS),
                "renderer": random.choice(self.WEBGL_RENDERERS)
            },
            "do_not_track": random.choice(["1", "0", None]),
            "canvas_fingerprint": ''.join(random.choices(string.ascii_letters + string.digits, k=64)),
            "audio_fingerprint": ''.join(random.choices(string.ascii_letters + string.digits, k=64)),
            "fonts": [],  # 默认为空数组
            "is_mobile": is_mobile,
            "mobile_info": os_info if is_mobile else None
        }
        
        return fingerprint
    
    def get_fingerprint_arguments(self, fingerprint: Dict[str, any], browser_type: str = 'chrome') -> List[str]:
        """
        将指纹转换为命令行参数列表
        
        Args:
            fingerprint (Dict): 指纹数据
            browser_type (str): 浏览器类型
            
        Returns:
            List[str]: 命令行参数列表
        """
        args = []
        
        # 设置用户代理
        args.append(f"--user-agent={fingerprint['user_agent']}")
        
        # 设置语言
        args.append(f"--lang={fingerprint['language'].split(',')[0]}")
        
        # 设置硬件并发
        args.append(f"--js-flags=--cpu-count={fingerprint['hardware_concurrency']}")
        
        # 设置视口大小
        args.append(f"--window-size={fingerprint['viewport']['width']},{fingerprint['viewport']['height']}")
        
        # 设置平台
        args.append(f"--platform={fingerprint['platform']}")
        
        # 设置WebGL参数（通过JavaScript注入方式，不直接作为启动参数）
        
        # 根据浏览器类型添加特定参数
        if browser_type.lower() == 'chrome':
            args.append("--disable-blink-features=AutomationControlled")
        elif browser_type.lower() == 'edge':
            args.append("--disable-blink-features=AutomationControlled")
            args.append("--edge-compat")
        
        return args


def generate_fingerprint_js(fingerprint: Dict[str, any]) -> str:
    """
    生成注入到浏览器的JavaScript代码，用于覆盖指纹属性
    
    Args:
        fingerprint (Dict): 指纹数据
        
    Returns:
        str: JavaScript注入代码
    """
    fingerprint_json = json.dumps(fingerprint)
    js_template = """
    (function() {
        const fingerprint = JSON_DATA;
        
        // 覆盖navigator属性
        Object.defineProperty(navigator, 'userAgent', {value: fingerprint.user_agent});
        Object.defineProperty(navigator, 'languages', {value: [fingerprint.language.split(',')[0]]});
        Object.defineProperty(navigator, 'platform', {value: fingerprint.platform});
        Object.defineProperty(navigator, 'hardwareConcurrency', {value: fingerprint.hardware_concurrency});
        Object.defineProperty(navigator, 'deviceMemory', {value: fingerprint.device_memory});
        
        if (fingerprint.do_not_track !== null) {
            Object.defineProperty(navigator, 'doNotTrack', {value: fingerprint.do_not_track});
        }
        
        // 覆盖屏幕属性
        Object.defineProperty(screen, 'width', {value: fingerprint.viewport.width});
        Object.defineProperty(screen, 'height', {value: fingerprint.viewport.height});
        Object.defineProperty(screen, 'colorDepth', {value: fingerprint.color_depth});
        
        // 增强WebGL伪装
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
        
        // 同样增强WebGL2伪装
        if (typeof WebGL2RenderingContext !== 'undefined') {
            const getParameterWebGL2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                // 复用相同的参数处理逻辑
                if (parameter === 37445 || parameter === 37446 || 
                    parameter === 3379 || parameter === 3386 || 
                    parameter === 33902 || parameter === 33901) {
                    return WebGLRenderingContext.prototype.getParameter.call(this, parameter);
                }
                return getParameterWebGL2.call(this, parameter);
            };
        }
        
        // 覆盖Canvas指纹
        const oldToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            if (this.width > 5 && this.height > 5) {
                // 只修改可能用于指纹识别的canvas
                const modifiedDataURL = oldToDataURL.call(this, type);
                // 添加微小变化，使每次都不同但视觉上相似
                return modifiedDataURL.slice(0, modifiedDataURL.length - 8) + fingerprint.canvas_fingerprint.slice(0, 8);
            }
            return oldToDataURL.call(this, type);
        };
        
        // 覆盖AudioContext指纹
        const oldGetChannelData = AudioBuffer.prototype.getChannelData;
        AudioBuffer.prototype.getChannelData = function() {
            const array = oldGetChannelData.apply(this, arguments);
            // 只修改用于音频指纹的数据
            if (array.length > 100) {
                // 添加微小变化
                const fingerprint_seed = parseInt(fingerprint.audio_fingerprint.slice(0, 8), 16);
                for (let i = 0; i < 8; i++) {
                    const index = Math.floor(array.length / 8 * i);
                    array[index] = array[index] + (fingerprint_seed % 100) / 1000000;
                }
            }
            return array;
        };
        
        // 修改插件信息
        Object.defineProperty(navigator, 'plugins', {
            get: function() {
                const plugins = fingerprint.plugins.length > 0 ? fingerprint.plugins : [];
                const pluginArray = Array.from(plugins);
                pluginArray.item = function(index) { return this[index]; };
                pluginArray.namedItem = function(name) { 
                    return this.find(plugin => plugin.name === name);
                };
                return pluginArray;
            }
        });
        
        // 防止Automation检测
        window.navigator.webdriver = false;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    })();
    """
    
    # 使用更安全的JSON替换方式
    js_code = js_template.replace("JSON_DATA", fingerprint_json)
    
    return js_code


class FingerprintManager:
    """
    管理浏览器指纹的类。
    
    负责生成、存储和应用浏览器指纹配置。
    """
    
    def __init__(self):
        """初始化指纹管理器"""
        self.generator = FingerprintGenerator()
        self.current_fingerprint = None
    
    def generate_new_fingerprint(self, browser_type: str = 'chrome', is_mobile: bool = False) -> Dict[str, any]:
        """
        生成新的浏览器指纹
        
        Args:
            browser_type (str): 浏览器类型，'chrome' 或 'edge'
            is_mobile (bool): 是否生成移动设备指纹
            
        Returns:
            Dict: 新生成的指纹数据
        """
        self.current_fingerprint = self.generator.generate_fingerprint(browser_type, is_mobile)
        return self.current_fingerprint
    
    def get_fingerprint_arguments(self, browser_type: str = 'chrome') -> List[str]:
        """
        获取当前指纹的命令行参数
        
        Args:
            browser_type (str): 浏览器类型
            
        Returns:
            List[str]: 命令行参数列表
        """
        if not self.current_fingerprint:
            self.generate_new_fingerprint(browser_type)
            
        return self.generator.get_fingerprint_arguments(self.current_fingerprint, browser_type)
    
    def get_fingerprint_js(self) -> str:
        """
        获取当前指纹的JavaScript注入代码
        
        Returns:
            str: 用于注入的JavaScript代码
        """
        if not self.current_fingerprint:
            self.generate_new_fingerprint()
            
        return generate_fingerprint_js(self.current_fingerprint)


# 创建全局单例实例
FINGERPRINT_MANAGER = FingerprintManager() 