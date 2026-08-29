"""Notice translations beyond English and Hindi.

Kept separate from notice.py so adding a language is a data change, not a
change to the module that decides what a notice must contain.

**These are working translations, not certified ones.** A consent notice is
the document a patient relies on to understand what happens to their data;
a mistranslation is an invalid consent, not a cosmetic bug. Every language
here must be reviewed by a qualified translator - ideally one with health or
legal experience - before it is shown to a real patient. See
legal/india/phase1-production.md.

Language choice also carries a legal wrinkle worth naming: India's DPDP Act
requires the notice in English or an Eighth Schedule language. Tamil
qualifies. Mandarin and Dutch do not - they serve other markets, and using
them does not satisfy the Indian requirement on its own.
"""

from __future__ import annotations

from typing import Dict

# (data, purpose) pairs, in the same order as the English notice.
ITEMS: Dict[str, list] = {
    "ta": [
        ("உங்கள் அறிக்கையின் புகைப்படம், PDF அல்லது உரை",
         "பரிசோதனைப் பெயர்கள், மதிப்புகள், அலகுகள் மற்றும் குறிப்பு வரம்புகளைப் "
         "படித்து உங்களுக்கு விளக்குவதற்கு"),
        ("மதிப்பாய்வுத் திரையில் நீங்கள் செய்யும் திருத்தங்கள்",
         "நாங்கள் தவறாகப் படித்ததைச் சரிசெய்வதற்கு"),
        ("சீரற்ற அமர்வு அடையாளம் மற்றும் உங்கள் IP முகவரி",
         "தவறான பயன்பாட்டைத் தடுத்து சேவையைக் கிடைக்கச் செய்வதற்கு. இது உங்களை "
         "அடையாளம் காட்டாது"),
    ],
    "zh": [
        ("您报告的照片、PDF 或文本",
         "读取检验项目名称、数值、单位和参考范围，以便向您解释"),
        ("您在核对页面上所做的更正",
         "更正我们读错的内容"),
        ("随机会话标识符和您的 IP 地址",
         "防止滥用并保持服务可用。这不会识别您的身份"),
    ],
    "nl": [
        ("De foto, PDF of tekst van uw rapport",
         "Om de testnamen, waarden, eenheden en referentiewaarden te lezen "
         "zodat we ze aan u kunnen uitleggen"),
        ("Correcties die u op het controlescherm maakt",
         "Om te corrigeren wat wij verkeerd hebben gelezen"),
        ("Een willekeurige sessie-identificatie en uw IP-adres",
         "Om misbruik te voorkomen en de dienst beschikbaar te houden. Dit "
         "identificeert u niet"),
    ],
}

TEXT: Dict[str, Dict[str, object]] = {
    # ------------------------------------------------------------- Tamil
    "ta": {
        "title": "தொடர்வதற்கு முன்",
        "intro": (
            "PlainMed நீங்கள் வழங்கும் ஆய்வக அறிக்கையைப் படித்து, அதில் என்ன "
            "இருக்கிறது என்பதை எளிய மொழியில் விளக்குகிறது. உங்கள் ஒப்புதலை "
            "வழங்குவதற்கு முன் இந்த அறிவிப்பைப் படிக்கவும்."
        ),
        "retention": (
            "உங்கள் அறிக்கை உங்கள் கோரிக்கை செயலாக்கப்படும் போது மட்டுமே "
            "பயன்படுத்தப்படுகிறது, பொதுவாக சில வினாடிகள். அது வட்டில் "
            "எழுதப்படுவதில்லை, எந்தப் பதிவேட்டிலும் சேமிக்கப்படுவதில்லை. "
            "எங்களிடம் நகல் எதுவும் இல்லை."
        ),
        "sharing": (
            "உங்கள் அறிக்கை யாருடனும் பகிரப்படுவதில்லை. AI மாதிரி அதைப் "
            "படிப்பதற்கு முன், உங்கள் பெயர், பிறந்த தேதி மற்றும் மருத்துவமனை "
            "அல்லது பதிவு எண் போன்ற அடையாள விவரங்களை நாங்கள் நீக்குகிறோம் - "
            "மாதிரிக்குப் பரிசோதனை முடிவுகள் மட்டுமே கிடைக்கும்."
        ),
        "rights": [
            "உங்களைப் பற்றி எங்களிடம் என்ன தனிப்பட்ட தரவு உள்ளது எனக் கேளுங்கள்",
            "அதைத் திருத்தவோ அழிக்கவோ கோருங்கள்",
            "நீங்கள் இயலாதபோது உங்கள் உரிமைகளுக்கு ஒருவரை நியமியுங்கள்",
            "எந்த நேரத்திலும் உங்கள் ஒப்புதலைத் திரும்பப் பெறுங்கள்",
            "எங்களிடமும், பின்னர் இந்திய தரவுப் பாதுகாப்பு வாரியத்திடமும் புகார் அளியுங்கள்",
        ],
        "withdraw": (
            "நீங்கள் எந்த நேரத்திலும் Clear ஐ அழுத்தி அல்லது இந்தப் பக்கத்தை "
            "மூடி உங்கள் ஒப்புதலைத் திரும்பப் பெறலாம். ஒப்புதலைத் திரும்பப் "
            "பெறுவது அதை வழங்குவது போலவே எளிதானது, மேலும் அது அனைத்து "
            "செயலாக்கத்தையும் உடனடியாக நிறுத்துகிறது."
        ),
        "grievance": (
            "உங்கள் தரவு எவ்வாறு கையாளப்படுகிறது என்பது குறித்த கேள்வி அல்லது "
            "புகாருக்கு எங்கள் புகார் அதிகாரியைத் தொடர்பு கொள்ளுங்கள். சட்டம் "
            "நிர்ணயித்த காலத்திற்குள் நாங்கள் பதிலளிப்போம்."
        ),
        "board": (
            "நாங்கள் உங்கள் புகாரைத் தீர்க்கவில்லை என்றால், நீங்கள் இந்திய "
            "தரவுப் பாதுகாப்பு வாரியத்திடம் புகார் அளிக்கலாம்."
        ),
        "age": (
            "PlainMed 18 வயது அல்லது அதற்கு மேற்பட்டவர்களுக்கு மட்டுமே. நீங்கள் "
            "18 வயதுக்குக் குறைவானவர் என்றால், பெற்றோர் அல்லது பாதுகாவலரின் "
            "உதவியைக் கேளுங்கள்."
        ),
        "not_medical_advice": (
            "உங்கள் அறிக்கையில் என்ன இருக்கிறது என்பதை PlainMed விளக்குகிறது. "
            "இது நோயைக் கண்டறிவதில்லை, சிகிச்சையைப் பரிந்துரைப்பதில்லை, "
            "மருத்துவருக்கு மாற்றாகவும் இல்லை. எப்போதும் தகுதிவாய்ந்த "
            "மருத்துவரிடம் உறுதிப்படுத்திக் கொள்ளுங்கள்."
        ),
    },
    # ---------------------------------------------------------- Mandarin
    "zh": {
        "title": "继续之前",
        "intro": (
            "PlainMed 读取您提供的化验报告，并用通俗易懂的语言解释其中的内容。"
            "在您同意之前，请阅读本告知说明。"
        ),
        "retention": (
            "您的报告仅在处理您的请求期间使用，通常为几秒钟。它不会写入磁盘，"
            "不会记录到任何日志中，也不会被存储。我们不保留任何副本。"
        ),
        "sharing": (
            "您的报告不会与任何人共享。在 AI 模型读取之前，我们会移除您的姓名、"
            "出生日期以及医院或病历号等身份信息——模型只会收到检验结果本身。"
        ),
        "rights": [
            "询问我们持有您的哪些个人数据",
            "要求我们更正或删除这些数据",
            "在您无法行使权利时指定他人代为行使",
            "随时撤回您的同意",
            "向我们投诉，之后可向印度数据保护委员会投诉",
        ],
        "withdraw": (
            "您可以随时点击“清除”或关闭本页面来撤回同意。撤回同意与给予同意"
            "一样简单，并会立即停止所有处理。"
        ),
        "grievance": (
            "如果您对我们如何处理您的数据有疑问或投诉，请联系我们的申诉专员。"
            "我们将在法律规定的时间内答复。"
        ),
        "board": "如果我们未能解决您的投诉，您可以向印度数据保护委员会投诉。",
        "age": (
            "PlainMed 仅供 18 岁及以上人士使用。如果您未满 18 岁，"
            "请让家长或监护人协助您。"
        ),
        "not_medical_advice": (
            "PlainMed 解释您的报告写了什么。它不做诊断，不推荐治疗方案，"
            "也不能替代医生。请务必向合格的临床医生确认。"
        ),
    },
    # ------------------------------------------------------------- Dutch
    "nl": {
        "title": "Voordat u verdergaat",
        "intro": (
            "PlainMed leest het laboratoriumrapport dat u aanlevert en legt in "
            "gewone taal uit wat erin staat. Lees deze kennisgeving voordat u "
            "toestemming geeft."
        ),
        "retention": (
            "Uw rapport wordt alleen gebruikt terwijl uw verzoek wordt "
            "verwerkt, doorgaans enkele seconden. Het wordt niet naar schijf "
            "geschreven, niet in een logbestand vastgelegd en niet opgeslagen. "
            "Wij bewaren geen kopie."
        ),
        "sharing": (
            "Uw rapport wordt met niemand gedeeld. Voordat het AI-model het "
            "leest, verwijderen wij identificerende gegevens zoals uw naam, "
            "geboortedatum en ziekenhuis- of dossiernummer — het model "
            "ontvangt alleen de testresultaten zelf."
        ),
        "rights": [
            "Vraag welke persoonsgegevens wij over u hebben",
            "Vraag ons deze te corrigeren of te wissen",
            "Wijs iemand aan om uw rechten uit te oefenen als u dat niet kunt",
            "Trek uw toestemming op elk moment in",
            "Dien een klacht in bij ons en daarna bij de toezichthouder",
        ],
        "withdraw": (
            "U kunt uw toestemming op elk moment intrekken door op Wissen te "
            "tikken of deze pagina te sluiten. Intrekken is net zo eenvoudig "
            "als geven, en stopt alle verwerking onmiddellijk."
        ),
        "grievance": (
            "Hebt u een vraag of klacht over hoe uw gegevens worden verwerkt, "
            "neem dan contact op met onze klachtenfunctionaris. Wij reageren "
            "binnen de wettelijke termijn."
        ),
        "board": (
            "Als wij uw klacht niet oplossen, kunt u een klacht indienen bij "
            "de bevoegde toezichthoudende autoriteit."
        ),
        "age": (
            "PlainMed is alleen bedoeld voor personen van 18 jaar en ouder. "
            "Bent u jonger dan 18, vraag dan een ouder of voogd om hulp."
        ),
        "not_medical_advice": (
            "PlainMed legt uit wat er in uw rapport staat. Het stelt geen "
            "diagnose, adviseert geen behandeling en vervangt geen arts. "
            "Bevestig de interpretatie altijd met een bevoegde zorgverlener."
        ),
    },
}

# Shown in the language picker, in the language itself.
ENDONYMS = {
    "en": "English",
    "hi": "हिन्दी",
    "ta": "தமிழ்",
    "zh": "中文",
    "nl": "Nederlands",
}
