"""The itemised notice required before consent (DPDP Rule 3).

India's Digital Personal Data Protection Act does not accept a link to a
privacy policy as notice. Rule 3 requires a notice that stands on its own,
is written in clear and plain language, and itemises the personal data and
the specific purpose it is collected for - presented independently of any
other information.

Rule 3 also requires the notice to be available in English **or any language
in the Eighth Schedule to the Constitution** (22 languages). That is a
product requirement, not a legal footnote: a patient who cannot read the
notice cannot give informed consent. English, Hindi, Tamil, Mandarin and Dutch ship today; further languages are
a data change in translations.py, not a code change.

Note that only English and Eighth Schedule languages (Hindi and Tamil here)
satisfy the Indian requirement. Mandarin and Dutch serve other markets.

The notice must also state how to withdraw consent, how to complain, and how
to reach the Data Protection Board - all reachable from the notice itself.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List

# Bump when the notice text changes materially. A consent token carrying an
# older version is rejected, which forces the user to see the new notice.
NOTICE_VERSION = "2026-08-28"

# Contact details are deployment configuration, not code. DPDP requires a
# published grievance contact; the notice refuses to render without one so a
# placeholder cannot reach a user.
GRIEVANCE_EMAIL = os.environ.get("PLAINMED_GRIEVANCE_EMAIL", "")
GRIEVANCE_NAME = os.environ.get("PLAINMED_GRIEVANCE_NAME", "")


@dataclass(frozen=True)
class NoticeItem:
    """One itemised (data, purpose) pair, as Rule 3 requires."""

    data: str
    purpose: str


@dataclass(frozen=True)
class Notice:
    language: str
    version: str
    title: str
    intro: str
    items: List[NoticeItem]
    retention: str
    sharing: str
    rights: List[str]
    withdraw: str
    grievance: str
    board: str
    age: str
    not_medical_advice: str
    contact: Dict[str, str] = field(default_factory=dict)


_BOARD_EN = (
    "If we do not resolve your complaint, you may complain to the Data "
    "Protection Board of India."
)
_BOARD_HI = (
    "यदि हम आपकी शिकायत का समाधान नहीं करते हैं, तो आप भारतीय डेटा संरक्षण "
    "बोर्ड से शिकायत कर सकते हैं।"
)


def _english() -> Notice:
    return Notice(
        language="en",
        version=NOTICE_VERSION,
        title="Before you continue",
        intro=(
            "PlainMed reads the laboratory report you provide and explains, in "
            "plain language, what it says. Please read this notice before you "
            "give your consent."
        ),
        items=[
            NoticeItem(
                data="The photo, PDF, or text of your report",
                purpose=(
                    "To read the test names, values, units and reference ranges "
                    "so we can explain them to you"
                ),
            ),
            NoticeItem(
                data="Corrections you make on the review screen",
                purpose="To correct anything we read incorrectly",
            ),
            NoticeItem(
                data="A random session identifier and your IP address",
                purpose=(
                    "To prevent misuse and keep the service available. This does "
                    "not identify you"
                ),
            ),
        ],
        retention=(
            "Your report is used only while your request is being processed, "
            "usually a few seconds. It is not written to disk, not written to "
            "any log, and not stored. We keep no copy and cannot retrieve it "
            "afterwards."
        ),
        sharing=(
            "Your report is not shared with anyone. Before the AI model reads "
            "it, we remove identifying details such as your name, date of "
            "birth, and hospital or record numbers - the model receives only "
            "the test results themselves."
        ),
        rights=[
            "Ask what personal data we hold about you",
            "Ask us to correct or erase it",
            "Nominate someone to exercise your rights if you are unable to",
            "Withdraw your consent at any time",
            "Complain to us, and then to the Data Protection Board of India",
        ],
        withdraw=(
            "You can withdraw your consent at any time by tapping Clear, or by "
            "closing this page. Withdrawing is as easy as giving consent, and "
            "stops all processing immediately. Because we store nothing, there "
            "is nothing left to delete afterwards."
        ),
        grievance=(
            "If you have a question or complaint about how your data is "
            "handled, contact our Grievance Officer. We will respond within "
            "the time the law requires."
        ),
        board=_BOARD_EN,
        age=(
            "PlainMed is only for people aged 18 or over. If you are under 18, "
            "please ask a parent or guardian to help you instead."
        ),
        not_medical_advice=(
            "PlainMed explains what your report says. It does not diagnose, "
            "does not recommend treatment, and is not a substitute for a "
            "doctor. Always confirm with a qualified clinician."
        ),
        contact={"name": GRIEVANCE_NAME, "email": GRIEVANCE_EMAIL},
    )


def _hindi() -> Notice:
    return Notice(
        language="hi",
        version=NOTICE_VERSION,
        title="आगे बढ़ने से पहले",
        intro=(
            "PlainMed आपकी दी हुई प्रयोगशाला रिपोर्ट को पढ़ता है और सरल भाषा में "
            "बताता है कि उसमें क्या लिखा है। सहमति देने से पहले कृपया यह सूचना पढ़ें।"
        ),
        items=[
            NoticeItem(
                data="आपकी रिपोर्ट की फ़ोटो, PDF या टेक्स्ट",
                purpose=(
                    "जाँच के नाम, मान, इकाइयाँ और संदर्भ सीमाएँ पढ़ने के लिए, "
                    "ताकि हम उन्हें आपको समझा सकें"
                ),
            ),
            NoticeItem(
                data="समीक्षा स्क्रीन पर आपके द्वारा किए गए सुधार",
                purpose="हमने जो ग़लत पढ़ा हो उसे ठीक करने के लिए",
            ),
            NoticeItem(
                data="एक यादृच्छिक सत्र पहचानकर्ता और आपका IP पता",
                purpose=(
                    "दुरुपयोग रोकने और सेवा उपलब्ध रखने के लिए। इससे आपकी पहचान "
                    "नहीं होती"
                ),
            ),
        ],
        retention=(
            "आपकी रिपोर्ट केवल आपके अनुरोध के दौरान उपयोग होती है, आमतौर पर कुछ "
            "सेकंड। इसे डिस्क पर नहीं लिखा जाता, किसी लॉग में नहीं रखा जाता, और "
            "संग्रहीत नहीं किया जाता। हमारे पास कोई प्रति नहीं रहती।"
        ),
        sharing=(
            "आपकी रिपोर्ट किसी के साथ साझा नहीं की जाती। AI मॉडल के पढ़ने से पहले "
            "हम आपका नाम, जन्म तिथि और अस्पताल या रिकॉर्ड संख्या जैसी पहचान संबंधी "
            "जानकारी हटा देते हैं - मॉडल को केवल जाँच के परिणाम मिलते हैं।"
        ),
        rights=[
            "पूछें कि हमारे पास आपका कौन सा व्यक्तिगत डेटा है",
            "उसे सुधारने या मिटाने के लिए कहें",
            "यदि आप असमर्थ हों तो अपने अधिकारों के लिए किसी को नामित करें",
            "किसी भी समय अपनी सहमति वापस लें",
            "हमसे, और फिर भारतीय डेटा संरक्षण बोर्ड से शिकायत करें",
        ],
        withdraw=(
            "आप किसी भी समय Clear दबाकर या यह पृष्ठ बंद करके अपनी सहमति वापस ले "
            "सकते हैं। सहमति वापस लेना उतना ही आसान है जितना देना, और यह तुरंत सभी "
            "प्रसंस्करण रोक देता है।"
        ),
        grievance=(
            "आपके डेटा के प्रबंधन के बारे में किसी प्रश्न या शिकायत के लिए हमारे "
            "शिकायत अधिकारी से संपर्क करें। हम कानून द्वारा निर्धारित समय में उत्तर देंगे।"
        ),
        board=_BOARD_HI,
        age=(
            "PlainMed केवल 18 वर्ष या उससे अधिक आयु के लोगों के लिए है। यदि आप 18 "
            "वर्ष से कम आयु के हैं, तो कृपया माता-पिता या अभिभावक की सहायता लें।"
        ),
        not_medical_advice=(
            "PlainMed बताता है कि आपकी रिपोर्ट में क्या लिखा है। यह रोग का निदान "
            "नहीं करता, उपचार की सलाह नहीं देता, और डॉक्टर का विकल्प नहीं है। हमेशा "
            "किसी योग्य चिकित्सक से पुष्टि करें।"
        ),
        contact={"name": GRIEVANCE_NAME, "email": GRIEVANCE_EMAIL},
    )


def _from_table(language: str) -> Notice:
    """Build a notice from the translation table.

    English and Hindi are written out in full above because they were the
    first two and carry the canonical wording. Everything else is data, so
    adding a language does not touch this module.
    """
    from plainmed.compliance.translations import ITEMS, TEXT

    text = TEXT[language]
    return Notice(
        language=language,
        version=NOTICE_VERSION,
        title=str(text["title"]),
        intro=str(text["intro"]),
        items=[NoticeItem(data=d, purpose=p) for d, p in ITEMS[language]],
        retention=str(text["retention"]),
        sharing=str(text["sharing"]),
        rights=list(text["rights"]),
        withdraw=str(text["withdraw"]),
        grievance=str(text["grievance"]),
        board=str(text["board"]),
        age=str(text["age"]),
        not_medical_advice=str(text["not_medical_advice"]),
        contact={"name": GRIEVANCE_NAME, "email": GRIEVANCE_EMAIL},
    )


_BUILDERS = {
    "en": _english,
    "hi": _hindi,
    "ta": lambda: _from_table("ta"),
    "zh": lambda: _from_table("zh"),
    "nl": lambda: _from_table("nl"),
}

SUPPORTED_LANGUAGES = tuple(_BUILDERS)


class GrievanceContactMissingError(RuntimeError):
    """No published grievance contact, which DPDP requires."""


def get_notice(language: str = "en", require_contact: bool = False) -> Notice:
    """Build the notice, falling back to English for unsupported languages.

    ``require_contact`` is set in production: a notice without a reachable
    grievance contact does not meet the requirement, and shipping a
    placeholder to a patient is worse than failing loudly at startup.
    """
    builder = _BUILDERS.get(language.lower().split("-")[0], _english)
    notice = builder()
    if require_contact and not (GRIEVANCE_EMAIL and GRIEVANCE_NAME):
        raise GrievanceContactMissingError(
            "PLAINMED_GRIEVANCE_NAME and PLAINMED_GRIEVANCE_EMAIL must be set. "
            "DPDP requires a published grievance contact in the consent notice."
        )
    return notice
