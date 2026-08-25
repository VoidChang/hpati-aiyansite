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
        '<p>艾研信息专注于高校电子工程教育的教学实验平台研发。'
        '我们以模块化、可扩展为设计原则，覆盖单片机、物联网、模拟电源、'
        '信号链与智能小车等方向，配套完整的代码例程与应用视频。</p>'
        '<p>从课程教学到学科竞赛，一套套件贯穿始终。</p>'
        '<p>艾研信息支持教育部产学合作协同育人项目，是杭州市高新技术企业、'
        '杭州市“雏鹰计划”企业，长期与德州仪器（TI）生态深度合作。</p>'
    ),
    'contact_address': '浙江省杭州市',
    'contact_icp': '浙ICP备XXXXXXX号',
}

PRODUCT_CATEGORIES = [
    {'name': '智能控制', 'slug': 'smart-control', 'summary': '智能小车、遥控器等控制类套件', 'order': 1},
    {'name': '物联网', 'slug': 'iot', 'summary': '物联网实验与系统套件', 'order': 2},
    {'name': '核心板', 'slug': 'core-board', 'summary': '处理器核心板与开发板', 'order': 3},
    {'name': '模拟与电源', 'slug': 'analog-power', 'summary': '模拟电源与信号链实验', 'order': 4},
    {'name': '单片机', 'slug': 'mcu', 'summary': '单片机教学实验平台', 'order': 5},
    {'name': '计算机体系', 'slug': 'computer-system', 'summary': '软硬件课程贯通教学系统', 'order': 6},
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
