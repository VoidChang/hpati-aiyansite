"""
Seed the site with content scraped from http://www.hpati.com/

Idempotent — safe to run repeatedly; existing rows are updated in place and
their slugs / relationships preserved. The user forum from the original site
is intentionally not migrated (per the rebuild brief).

Usage:
    python manage.py seed
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from website.models import (
    News, NewsCategory, Product, ProductCategory, ProductExperiment,
    SiteSetting,
)


# --------------------------------------------------------------------------- #
# Source data — taken verbatim from the public pages of hpati.com (Apr 2026).
# Images / binary docs are left for the editor to upload via the admin, since
# the originals live on a third-party CDN. FileField slots stay empty until
# then; the templates render graceful placeholders.
# --------------------------------------------------------------------------- #
SITE = {
    'company_name': '艾研信息',
    'company_name_en': 'AiYan Information',
    'tagline': '为高校电子工程教育提供创新实验平台',
    'hero_title': '让工程教育，回归动手实践',
    'hero_subtitle': '从单片机到物联网，从电源拓扑到智能小车——为高校实验室打造的模块化教学套件。',
    'about_title': '让工程教育，回归动手实践',
    'about_body': (
        '<p>杭州艾研信息技术有限公司（Hangzhou Aiyan Information Technology Co., ltd）'
        '位于杭州高新技术开发区内，是集研发、生产、销售、服务于一体的科技型技术企业。'
        '公司依托园区区位优势，与国内多所院校开展技术合作，'
        '致力于为高校、科研院所、企业提供综合性解决方案。'
        '主要产品包括高校教育实验平台、面向高校研究所应用开发方案等。</p>'
        '<p>艾研信息定位于搭建半导体厂商与国内大专院校的合作桥梁，'
        '凭借专业的服务、创新的理念、热忱的态度，'
        '携手各方推动嵌入式及模拟技术在国内稳步发展。'
        '公司研发团队在嵌入式技术以及相关模拟技术领域积累了充足的技术与产品设计开发经验。'
        '依托和半导体厂商及大专院校的项目合作基础，'
        '我们可提供硬件、软件、案例、课程、教材、培训一体化配套方案，'
        '合力推进嵌入式及模拟技术走进国内高校，助力学生综合能力稳步提升。</p>'
        '<p>艾研信息支持教育部产学合作协同育人项目，'
        '是杭州市高新技术企业、杭州市“雏鹰计划”企业，'
        '长期与德州仪器（TI）生态深度合作，'
        '产品覆盖智能控制、物联网、核心板、模拟与电源、单片机、'
        '计算机体系、教学套件、无线通信等方向。</p>'
    ),
    'contact_address': '杭州市滨江区滨安路1197号4幢207室',
    'contact_phone': '0571-86134572',
    'contact_fax': '0571-86134572',
    'contact_email': 'support@hpati.com',
    'contact_zip': '310013',
    'work_hours': '9:00-17:00',
    'map_lng': 120.181077,
    'map_lat': 30.18991,
    'contact_icp': '浙ICP备13028346号-1',
}

PRODUCT_CATEGORIES = [
    {'name': '智能控制', 'slug': 'smart-control', 'summary': '智能小车、遥控器等控制类套件', 'order': 1},
    {'name': '物联网', 'slug': 'iot', 'summary': '物联网实验与系统套件', 'order': 2},
    {'name': '核心板', 'slug': 'core-board', 'summary': '处理器核心板与开发板', 'order': 3},
    {'name': '模拟与电源', 'slug': 'analog-power', 'summary': '模拟电源与信号链实验', 'order': 4},
    {'name': '单片机', 'slug': 'mcu', 'summary': '单片机教学实验平台', 'order': 5},
    {'name': '计算机体系', 'slug': 'computer-system', 'summary': '软硬件课程贯通教学系统', 'order': 6},
    {'name': '教学套件', 'slug': 'teaching-kit', 'summary': 'MOOC 与课程配套实验套件', 'order': 7},
    {'name': '无线通信', 'slug': 'wireless', 'summary': '蓝牙、WIFI 等无线通信评估板', 'order': 8},
]

PRODUCTS = [
    {
        'name': '智能小车 AY-Smart Car', 'code': 'AY-Smart Car',
        'slug': 'ay-smart-car', 'category_slug': 'smart-control',
        'tagline': '巡线 · 迷宫避障 · 直立平衡，三种状态自由切换。',
        'summary': '基于MSPM0系列处理器的智能小车套件，具备巡线、迷宫避障、直立平衡等功能，传感器、电机、车体构架高度可扩展，搭配全能遥控器。',
        'description': (
            '<p>智能小车套件基于易于开发使用的MSPM0系列处理器控制，'
            '同时具备巡线、迷宫避障、直立平衡等功能，并且在传感器、电机、车体构架方面具备高度扩展性。'
            '搭配同款处理器的全能遥控器，不仅能对小车进行常规控制，还能快速的配置调整小车的参数。</p>'
            '<h3>巡线功能</h3>'
            '<p>依靠车底部的巡线传感器和编码电机，实现小车指定速度的巡线、转弯和掉头。'
            '巡线传感器可识别任意颜色线，以适应不同赛道。（默认黑色巡线，彩色巡线需选配白光传感器）</p>'
            '<h3>迷宫避障功能</h3>'
            '<p>依靠车头及两侧的红外测距传感器和编码电机，实现小车在迷宫中以指定速度避障行进、转弯和掉头。'
            '车头可加装超声波传感器以实现距离精确测量和控制。</p>'
            '<h3>直立平衡功能</h3>'
            '<p>依靠角度传感器和编码电机，实现小车直立平衡。'
            '小车在巡线/避障/直立平衡三种状态切换时，无需改变小车硬件结构。</p>'
            '<h3>全能遥控器</h3>'
            '<p>基于M0L1306同型号处理器的全能遥控器，与小车通过无线串口通信。'
            '不仅可以对小车进行常规运动方向控制，还具备体感控制功能。'
            '不仅有蜂鸣器还有振动电机作为输入反馈。'
            '两个机械旋转编码器可以实现参数的快速精确设定，方便调试小车的各项参数。</p>'
        ),
        'specifications': '主控芯片 | MSPM0系列\n通信方式 | 无线串口\n功能模式 | 巡线 / 迷宫避障 / 直立平衡\n遥控器主控 | M0L1306\n扩展性 | 传感器、电机、车体高度可扩展',
        'featured': True, 'order': 1,
        'experiments': [
            'MSPM0开发软件与SDK例程调用', '定时节拍实现GPIO输入和输出控制',
            'UART串口通信与人机交互', 'SPI与OLED显示', 'ADC与寻线传感器',
            '正交编码器与直流电机测速', 'PWM与直流电机调速', '速度闭环控制',
            '速度位置双闭环控制', '基于双闭环的位移控制', '转向环与寻迹小车',
            '使用遥控器配置小车参数',
        ],
    },
    {
        'name': '物联网实验套件 AY-IOT KIT', 'code': 'AY-IOT KIT',
        'slug': 'ay-iot-kit', 'category_slug': 'iot',
        'tagline': '同时兼容 TI CC3200 Launchpad 与树莓派。',
        'summary': '物联网实验套件同时兼容TI CC3200Launchpad和树莓派，提供完整全套代码和应用视频指导，标准接口便于扩展。',
        'description': (
            '<p>物联网实验套件同时兼容TI CC3200Launchpad和树莓派，方便不同应用背景的用户学习使用；'
            '实验套件提供完整的全套代码和应用视频指导，回避繁琐的指导书；'
            '套件的模块设计了标准的接口，方便套件的扩展，同时也便于用户自行扩展。</p>'
            '<p>物联网实验需要涉及的环节很多，一般至少包含前端传感器电路、传感器的采集数据、'
            '系统的电池供电、采集数据上发到网络（或者云服务）、网络平台对数据处理、'
            '从网络平台下发到控制前端的反向数据通路、整个系统的移动设备应用呈现（通常是手机端APP）。'
            '作为物联网应用的创新设计，如果在众多环节中出现一个环节的问题，'
            '都将导致最终创新想法不能实现。本实验套件的目标就是为学习物联网开发的学生，'
            '提供各种工具并了解其基本原理，掌握各个环节的快速设计工具的综合应用方式。</p>'
            '<p>因为手机品种过多，实验套件手机端不提供专门APP的程序，但提供了手机网页版的程序，'
            '用户可采用套壳的方式快速实现可以个人手机上呈现的APP。</p>'
        ),
        'specifications': '兼容平台 | TI CC3200 Launchpad / 树莓派\n接口标准 | 模块化标准接口\n配套资料 | 全套代码 + 应用视频\n移动端 | 网页版APP（可套壳）',
        'featured': True, 'order': 2,
        'experiments': [
            '传感器采集与前端电路', '系统电池供电设计', '数据上发到云服务',
            '网络平台数据处理', '反向数据通路控制', '移动设备应用呈现',
        ],
    },
    {
        'name': '3507核心板 AY-MSPM0G3507 C', 'code': 'AY-MSPM0G3507 C',
        'slug': 'ay-mspm0g3507-c', 'category_slug': 'core-board',
        'tagline': '面包板友好的 MSPM0G3507 核心板。',
        'summary': '主控芯片MSPM0G3507，64引脚，40mm×60mm，可插入面包板，Typec USB 5V 供电。',
        'description': (
            '<p>主控芯片MSPM0G3507，64引脚。尺寸：40mm × 60mm。'
            '用2个2.54mm间距 2×15 双排孔引出绝大部分引脚。'
            '两个排针间距设置成可以插入到面包板的间隔，方便在面包板上实验。</p>'
            '<p>提供两排排针和一头排母一头排针的配件，不焊死，可自行选择焊接。</p>'
            '<p>供电：Typec USB 5V / 排针引线3.3V / 排针引线5.5V。</p>'
        ),
        'specifications': '主控芯片 | MSPM0G3507\n引脚数 | 64\n尺寸 | 40mm × 60mm\n引出 | 2×15 双排孔 2.54mm\n供电 | Typec USB 5V / 3.3V / 5.5V',
        'featured': True, 'order': 3,
    },
    {
        'name': 'AY-MSE KIT 创新实验套件', 'code': 'AY-MSE KIT',
        'slug': 'ay-mse-kit', 'category_slug': 'analog-power',
        'tagline': '信号链与电源知识点，面向本科教学。',
        'summary': '以Tiva Cortex M4 LaunchPad为核心，包含信号链与电源多个模拟应用模块，面向电子电气、电信通信专业本科教学。',
        'description': (
            '<p>本套件以Tiva Cortex M4 LaunchPad为核心模块，'
            '包含针对信号链与电源知识点在内的多个模拟应用模块，'
            '面向电子电气、电信通信等专业的本科教学、课外实践，'
            '兼顾MCU的开发学习和模拟知识的理解与应用。</p>'
            '<p>套件提供配套的实验指导书，相应的代码例程，便于用户学习与操作。</p>'
        ),
        'specifications': '核心模块 | Tiva Cortex M4 LaunchPad\n覆盖知识 | 信号链 / 电源\n适用专业 | 电子电气、电信通信\n配套 | 实验指导书 + 代码例程',
        'featured': False, 'order': 4,
    },
    {
        'name': '模拟电源创新实验套件 AY-APower KIT', 'code': 'AY-APower KIT',
        'slug': 'ay-apower-kit', 'category_slug': 'analog-power',
        'tagline': '掌握电源拓扑结构与工作原理。',
        'summary': '以模拟电源基础知识教育为目标，帮助学生掌握电源的拓扑结构和工作原理、理解外围器件对电源的性能影响。',
        'description': (
            '<p>以模拟电源基础知识教育为目标，帮助学生掌握电源的拓扑结构和工作原理、'
            '理解外围器件对电源的性能影响、学习电源参数的计算、理解电源反馈和暂态响应。</p>'
        ),
        'specifications': '教学目标 | 模拟电源基础\n核心知识 | 拓扑结构 / 参数计算 / 反馈与暂态响应\n适用 | 本科教学与课外实践',
        'featured': False, 'order': 5,
    },
    {
        'name': '单片机实验套件 AY-SCMP KIT', 'code': 'AY-SCMP KIT',
        'slug': 'ay-scmp-kit', 'category_slug': 'mcu',
        'tagline': '发挥单片机在人机交互方面的优势。',
        'summary': '创新实验平台将所需信息生动有趣地传递给用户，学习单片机及外围电路设计方法。',
        'description': (
            '<p>创新实验平台充分发挥单片机在人机交互方面的优势，'
            '将所需的信息传递给用户，生动有趣的学习单片机、以及外围电路的设计方法。</p>'
        ),
        'specifications': '定位 | 单片机人机交互实验\n学习内容 | 单片机 + 外围电路设计\n配套 | 实验指导与例程',
        'featured': False, 'order': 6,
    },
    {
        'name': 'Sword4.0 计算机软硬件课程贯通教学实验系统', 'code': 'Sword4.0',
        'slug': 'sword4-0', 'category_slug': 'computer-system',
        'tagline': '软硬件课程贯通教学实验系统。',
        'summary': '贯通计算机软硬件课程的实验教学系统，支撑从数字逻辑到体系结构的完整教学链路。',
        'description': (
            '<p>Sword4.0 计算机软硬件课程贯通教学实验系统，'
            '支撑从数字逻辑、计算机组成原理到体系结构的完整教学链路，'
            '帮助学生在统一的平台上贯通理解计算机软硬件协同工作原理。</p>'
        ),
        'specifications': '定位 | 计算机软硬件贯通\n课程覆盖 | 数字逻辑 / 计算机组成 / 体系结构\n形态 | 统一实验平台',
        'featured': False, 'order': 7,
    },
    {
        'name': 'MOOC-《电子工程综合实践》配套实验开发套件',
        'code': 'MOOC-EE Practice Kit',
        'slug': 'mooc-ee-practice-kit', 'category_slug': 'teaching-kit',
        'tagline': 'MOOC 课程配套,硬件与软件综合实践入门。',
        'summary': '配套《电子工程综合实践》MOOC 课程的实验开发套件，'
                   '带领学习者设计兼有硬件与软件的电子电路系统，并亲手制作工程原型。',
        'description': (
            '<p>本课程是针对电子工程相关专业的实践课程，将带领大家设计有一定实用功能、'
            '兼有硬件和软件的电子电路系统，并亲手制作其工程原型实物，'
            '为学习者提供电子工程方面的入门级基础性综合技能实践训练。</p>'
            '<p>课程具体信息请参见 '
            '<a href="http://www.cnmooc.org/portal/course/73/144.mooc" '
            'target="_blank" rel="noopener">中国大学 MOOC</a>。</p>'
            '<p>套件内容：</p>'
            '<ul>'
            '<li>电子工程综合实践（MOOC板） × 1 块</li>'
            '<li>MSP-EXP430G2 LaunchPad × 1 块</li>'
            '<li>电子工程综合实践基础包材料 × 1 份</li>'
            '<li>电子工程综合实践拓展包材料 × 1 份</li>'
            '</ul>'
            '<p>备注：配件包材料不包含 TI 物料，所需 TI 物料可通过注册 myTI 账号申请获得。</p>'
        ),
        'specifications': '配套课程 | 电子工程综合实践\n套件内容 | MOOC板 + MSP-EXP430G2 LaunchPad + 基础包 + 拓展包\nTI 物料 | 需 myTI 账号申请',
        'featured': False, 'order': 8,
    },
    {
        'name': '口袋电子系统实验模块 AY-SEB Module',
        'code': 'AY-SEB Module',
        'slug': 'ay-seb-module', 'category_slug': 'core-board',
        'tagline': '可独立工作的核心模块，搭配 LaunchPad 扩展实验。',
        'summary': '口袋电子系统实验核心模块，与 TI MSP430F5529 LaunchPad 或 Tiva Cortex M4 LaunchPad '
                   '搭配，可实现 COG 显示、机械/触摸按键、BUCK、BOOST、DAC 输出等功能。',
        'description': (
            '<p>口袋电子系统实验核心模块（AY-SEB Module）是口袋电子系统实验套件'
            '（AY-SEB Kit）的核心模块，与套件的外围模块配合，'
            '可以组建功能更完整、覆盖更多知识点的实验套件。</p>'
            '<p>核心模块可独立于外围模块工作，它与 TI MSP430F5529 LaunchPad '
            '或 TI Tiva Cortex M4 LaunchPad 搭配，可以实现 COG 显示、'
            '机械/触摸按键、BUCK、BOOST、DAC 输出等功能。</p>'
        ),
        'specifications': '兼容 LaunchPad | MSP430F5529LP / Tiva Cortex M4\n功能 | COG 显示 / 机械·触摸按键 / BUCK / BOOST / DAC 输出\n形态 | 可独立工作的核心模块',
        'featured': False, 'order': 9,
    },
    {
        'name': '口袋电子系统实验套件 AY-SEB KIT',
        'code': 'AY-SEB KIT',
        'slug': 'ay-seb-kit', 'category_slug': 'mcu',
        'tagline': '信号链、电源到电机控制，单片机人机交互综合实验平台。',
        'summary': '创新实验平台涵盖从信号链、电源到电机控制的诸多方面，'
                   '同时发挥单片机在人机交互方面的优势，生动有趣地学习模拟技术与单片机知识。',
        'description': (
            '<p>创新实验平台涵盖从信号链、电源到电机控制的诸多方面，'
            '同时发挥单片机在人机交互方面的优势，'
            '生动有趣地学习模拟技术和单片机知识。</p>'
            '<h3>信号链方面</h3>'
            '<p>针对超声波、麦克风、压力应变三种传感器的微弱信号，'
            '分别采用通用运放电路、三极管放大电路和仪表放大器电路进行处理，'
            '全面学习模拟信号调理的知识。对于常见的数字类传感器信号、'
            '红外类传感器信号的处理也专门设计了实验。</p>'
            '<h3>电源管理方面</h3>'
            '<p>设计了最常用的两种斩波电路：BUCK 斩波电路和 BOOST 斩波电路。'
            '两个斩波电路分别使用集成芯片和分立 MOSFET 元件来构造，'
            '在功能上分别为电流输出与电压输出，尽可能罗列电源管理方面的知识点。</p>'
        ),
        'specifications': '信号链 | 超声波 / 麦克风 / 压力应变 传感器调理\n电源 | BUCK + BOOST 斩波电路\n主控 | MSP430F5529 LaunchPad',
        'featured': False, 'order': 10,
    },
    {
        'name': 'MSP430 口袋实验套件 AY-G2PL KIT',
        'code': 'AY-G2PL KIT',
        'slug': 'ay-g2pl-kit', 'category_slug': 'mcu',
        'tagline': '围绕 MSP430G2 的多功能口袋实验板。',
        'summary': '围绕 MSP430G2 系列的口袋实验套件，涵盖供电单元、触摸板、I2C 扩展 IO、'
                   '机械按键与 LED 灯柱、LCD 显示、PWM 与滤波器等实验单元。',
        'description': (
            '<p>围绕 MSP430G2 系列的口袋实验套件，涵盖多个功能单元：</p>'
            '<ul>'
            '<li><strong>供电单元</strong>：涉及运放电源供电的理解，'
            '双极性信号的处理，电荷泵型反压芯片的应用。</li>'
            '<li><strong>触摸板单元</strong>：涉及电容触摸按键的测量及原理，'
            'G2 系列单片机 IO 内部集成 RC 振荡电路的振荡频率的测量，'
            '施密特反相器构成的多谐振荡器的原理与应用。</li>'
            '<li><strong>I2C 扩展 IO 单元</strong>：涉及 I2C 原理的学习及应用，'
            '串行转并行的原理及应用，IO 扩展芯片的原理及应用。</li>'
            '<li><strong>机械按键及 LED 灯柱</strong>：涉及扩展 IO 口的应用，'
            '按键及 LED 的控制实验。</li>'
            '<li><strong>LCD 显示单元</strong>：涉及 128 段液晶显示的原理及应用，'
            '液晶驱动控制器的原理及应用。可配合其他单元实现显示、控制、存储等功能。</li>'
            '<li><strong>PWM 及滤波器单元</strong>：涉及 SPWM 的原理及应用，'
            '滤波器的设计与调试。</li>'
            '</ul>'
        ),
        'specifications': '主控 | MSP430G2 系列\n实验单元 | 供电 / 触摸 / I2C 扩展 / LCD 显示 / PWM 滤波\n形态 | 口袋实验板',
        'featured': False, 'order': 11,
    },
    {
        'name': '双模蓝牙 4.0 评估板 AY-CC2564EVM',
        'code': 'AY-CC2564EVM',
        'slug': 'ay-cc2564-evm', 'category_slug': 'wireless',
        'tagline': 'TI CC256x 双模蓝牙 4.0 评估板,板载 PCB 天线。',
        'summary': '基于 TI CC256x 的双模式蓝牙 4.0 评估板，板载 PCB 天线无障碍通信距离不小于 10 米，'
                   '提供标准 BoosterPack 接口与非标扩展接口。',
        'description': (
            '<p>AY-CC2564EVM 是基于 TI CC256x 的双模式蓝牙 4.0 的评估板。'
            'TI 的电源技术和软件算法使得 CC256X 在蓝牙 BR/EDR/LE 多种模式'
            '都比同类产品更节能。</p>'
            '<p>评估板采用板载 PCB 天线，无障碍通信距离不小于 10 米；'
            '评估板提供标准的 BoosterPack 接口，可以与 TI 的 MSP430 LaunchPad '
            '或 TIVA LaunchPad 直接互联；评估板同时提供非 BoosterPack 标准的连接接口，'
            '方便用户将评估板连接到自制的 MCU 系统上。</p>'
            '<p>板上有关蓝牙芯片的应用设计可以直接拷贝到用户自己的电路板上，'
            '以减少产品的开发时间。可应用于无线音频传输、无线数据采集等场景。</p>'
        ),
        'specifications': '蓝牙芯片 | TI CC256x\n支持模式 | BR / EDR / LE 双模\n通信距离 | ≥10 米（无障碍）\n接口 | BoosterPack 标准接口 + 非标扩展接口\n天线 | 板载 PCB 天线',
        'featured': False, 'order': 12,
    },
    {
        'name': 'AY-TPA3112 EVM 音频功放评估板',
        'code': 'AY-TPA3112 EVM',
        'slug': 'ay-tpa3112-evm', 'category_slug': 'analog-power',
        'tagline': 'TPA3112D1 评估模块,用户 DIY 装配外围电路。',
        'summary': 'TPA3112D1 评估模块，外围电路器件由用户 DIY 装配，'
                   '可构成 25W D 类功放的单声道音频放大器，支持带/不带 LC 滤波器两种输出方式。',
        'description': (
            '<p>AY-TPA3112D1 EVM 是一块只焊装了核心芯片 TPA3112D1 的评估模块（EVM），'
            '外围电路器件由用户 DIY 装配。EVM 的外围电路装配完成后可构成 25W、'
            'D 类功放的单声道音频放大器。</p>'
            '<p>EVM 输入模拟音频信号并将板上的输出端口外接 speaker，'
            '就可以呈现 EVM 的音频功放的效果。EVM 的输出可通过板上的跳线选择'
            '带 LC 滤波器或不带 LC 滤波器的两种方式，用户可以体验其不同效果。</p>'
            '<p>用户应用 EVM 能迅速评测 TPA3112D1 的音频放大品质并与数据手册中的'
            '技术指标进行比对。EVM 提供了完整的《用户指南》，'
            '包含 EVM 的电路原理图、器件列表（BOM）以及详尽的快速入门指导。</p>'
        ),
        'specifications': '核心芯片 | TPA3112D1\n输出功率 | 25W D 类功放\n输出方式 | 带 LC 滤波器 / 直通 可选\n配套资料 | 用户指南（原理图 + BOM + 快速入门）',
        'featured': False, 'order': 13,
    },
    {
        'name': 'AY-LDC1000 电感数字转换器评估板',
        'code': 'AY-LDC1000',
        'slug': 'ay-ldc1000', 'category_slug': 'analog-power',
        'tagline': '板载 PCB 线圈可分离,支持外接电感传感器。',
        'summary': 'LDC1000 电感数字转换器评估模块，板载 PCB 传感器线圈与 LDC1000 IC 转换电路可分离，'
                   '支持外接电感传感器，提供原型系统设计的最大灵活性。',
        'description': (
            '<p>该模块为用户提供原型系统设计的最大灵活性。'
            '体现在板载的 PCB 传感器线圈和 LDC1000 IC 转换电路可以分离。</p>'
            '<p>当要使用板载的 PCB 传感器线圈时，只需将模块与 MCU 系统的 SPI 数据线'
            '和相应的供电线连接即可。若要使用外接的电感传感器，'
            '可以沿板上邮票孔掰断电路板。外接的传感器通过模块配套的接线柱'
            '连接到转换电路上。</p>'
        ),
        'specifications': '核心芯片 | LDC1000\n传感器 | 板载 PCB 线圈（可分离）\n通信接口 | SPI\n扩展 | 支持外接电感传感器',
        'featured': False, 'order': 14,
    },
]

NEWS_CATEGORIES = [
    {'name': '企业动态', 'slug': 'company-news', 'order': 1},
    {'name': '行业新闻', 'slug': 'industry-news', 'order': 2},
]

INDUSTRY_NEWS = [
    ('2026-04-01', '人工智能赋能高校 重塑高等教育新生态', '人工智能'),
    ('2025-12-05', 'AI入课堂既要“缰绳”也要“导航”', '人工智能'),
    ('2025-03-04', '把握人工智能机遇 加快推动教育创新', '教育创新'),
    ('2024-12-24', '人工智能引领高等教育数字化转型', '数字化转型'),
    ('2024-04-24', '加快数字人才培养 服务发展新质生产力', '人才培养'),
    ('2024-01-09', '高校网络安全态势感知体系建设', '网络安全'),
    ('2023-09-27', '虚拟教研室在虚实间激发深度学习', '教学创新'),
    ('2023-06-27', '经典互联网是否仍然重要？', '互联网'),
    ('2023-03-27', '乔姆斯基谈ChatGPT与后者的回应', '人工智能'),
    ('2023-01-06', '互联网简史：从阿帕网到元宇宙', '互联网'),
    ('2022-11-02', '聚焦：信息技术的“应为”与“能为”', '信息技术'),
    ('2022-08-22', '人工智能助推数字化时代教师转型', '人工智能'),
]

COMPANY_NEWS = [
    ('2019-12-18', '艾研信息支持教育部2018年第二批产学合作协同育人项目',
     '艾研信息持续支持教育部产学合作协同育人项目，与高校共建实践条件与课程体系。'),
    ('2016-10-18', '艾研信息被评为杭州市高新技术企业',
     '艾研信息凭借在高校电子工程教学实验领域的持续研发投入，被评为杭州市高新技术企业。'),
    ('2016-03-16', '艾研信息成为杭州市“雏鹰计划”企业',
     '作为杭州市“雏鹰计划”入选企业，艾研信息获得政策支持，加速教学实验平台研发。'),
    ('2015-11-10', '艾研模拟电源套件正式发布',
     '面向模拟电源基础教育的 AY-APower KIT 正式发布，帮助学生掌握电源拓扑结构与工作原理。'),
    ('2014-11-25', '艾研官方站全新改版公测',
     '艾研信息官方网站全新改版，进入公测阶段。'),
]


class Command(BaseCommand):
    help = 'Seed the site with content scraped from hpati.com (forum excluded).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding site content…'))

        # ── Site settings (singleton). ──────────────────────────────────────
        site, _ = SiteSetting.objects.update_or_create(pk=1, defaults=SITE)
        self.stdout.write(f'  · site settings  → {site.company_name}')

        # ── Product categories. ─────────────────────────────────────────────
        cat_map = {}
        for c in PRODUCT_CATEGORIES:
            obj, _ = ProductCategory.objects.update_or_create(
                slug=c['slug'],
                defaults={'name': c['name'], 'summary': c.get('summary', ''),
                          'order': c['order'], 'is_visible': True},
            )
            cat_map[c['slug']] = obj
        self.stdout.write(f'  · product categories  → {len(cat_map)}')

        # ── Products + experiments. ─────────────────────────────────────────
        for p in PRODUCTS:
            cat = cat_map.get(p.get('category_slug'))
            defaults = {
                'name': p['name'], 'code': p['code'],
                'tagline': p.get('tagline', ''),
                'summary': p.get('summary', ''),
                'description': p.get('description', ''),
                'specifications': p.get('specifications', ''),
                'category': cat,
                'featured': p.get('featured', False),
                'order': p.get('order', 0),
                'is_published': True,
            }
            prod, created = Product.objects.update_or_create(
                slug=p['slug'], defaults=defaults,
            )
            # Experiments (rebuild list each run).
            prod.experiments.all().delete()
            for i, title in enumerate(p.get('experiments', [])):
                ProductExperiment.objects.create(
                    product=prod, title=title, order=i,
                )
            self.stdout.write(f"  · product  {'+ new' if created else '~ upd'}  {prod.name}")

        # ── News categories. ─────────────────────────────────────────────────
        news_cat_map = {}
        for c in NEWS_CATEGORIES:
            obj, _ = NewsCategory.objects.update_or_create(
                slug=c['slug'],
                defaults={'name': c['name'], 'order': c['order']},
            )
            news_cat_map[c['slug']] = obj

        # ── Industry news. ───────────────────────────────────────────────────
        industry_cat = news_cat_map['industry-news']
        for d, title, tag in INDUSTRY_NEWS:
            slug = slugify(title) or slugify(d)
            News.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title, 'category': industry_cat,
                    'excerpt': f'行业资讯 · {tag}',
                    'body': f'<p>{title}</p><p>本文转载自行业公开资讯，详细内容请见原文。</p>',
                    'published_at': date.fromisoformat(d),
                    'is_published': True,
                },
            )
        self.stdout.write(f'  · industry news  → {len(INDUSTRY_NEWS)}')

        # ── Company news. ────────────────────────────────────────────────────
        company_cat = news_cat_map['company-news']
        for d, title, excerpt in COMPANY_NEWS:
            slug = slugify(title) or slugify(d)
            News.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title, 'category': company_cat,
                    'excerpt': excerpt,
                    'body': f'<p>{excerpt}</p>',
                    'published_at': date.fromisoformat(d),
                    'is_published': True,
                },
            )
        self.stdout.write(f'  · company news  → {len(COMPANY_NEWS)}')

        self.stdout.write(self.style.SUCCESS('Seed complete.'))
