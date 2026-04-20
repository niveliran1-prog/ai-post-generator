import os
import json
import random
import re
import urllib.parse
import pandas as pd
import streamlit as st
from openai import OpenAI


# =========================
# Page setup
# =========================
st.set_page_config(
    page_title="מחולל פוסטים חכם ל-Canva",
    page_icon="🎨",
    layout="wide"
)


# =========================
# Styling (RTL + modern UI)
# =========================
st.markdown("""
<style>
html, body, [class*="css"]  {
    direction: rtl;
    text-align: right;
    font-family: "Segoe UI", sans-serif;
}

.block-container {
    padding-top: 1.6rem;
    padding-bottom: 2rem;
    max-width: 1320px;
}

.main-shell {
    background: linear-gradient(180deg, rgba(13,18,30,0.96) 0%, rgba(8,12,22,1) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 28px;
    padding: 28px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.25);
    margin-bottom: 22px;
}

.hero-title {
    font-size: 3rem;
    font-weight: 900;
    line-height: 1.1;
    margin-bottom: 0.4rem;
    background: linear-gradient(90deg, #ffffff 0%, #b8d5ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.02rem;
    color: #b8bfd3;
    margin-bottom: 1.2rem;
}

.section-title {
    font-size: 1.45rem;
    font-weight: 800;
    margin-top: 0.6rem;
    margin-bottom: 0.8rem;
    color: #ffffff;
}

.section-card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 18px;
    border-radius: 22px;
    margin-bottom: 16px;
    backdrop-filter: blur(8px);
}

.version-title {
    font-size: 1.2rem;
    font-weight: 800;
    margin-bottom: 0.9rem;
    color: #ffffff;
}

.small-label {
    font-size: 0.92rem;
    font-weight: 700;
    color: #d8dded;
    margin-top: 0.55rem;
    margin-bottom: 0.35rem;
}

.auto-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(117, 164, 255, 0.12);
    border: 1px solid rgba(117, 164, 255, 0.28);
    color: #dfe9ff;
    margin-bottom: 10px;
    font-size: 0.85rem;
    font-weight: 700;
}

.info-chip {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    color: #d8dded;
    font-size: 0.85rem;
    font-weight: 700;
    margin-left: 8px;
    margin-bottom: 8px;
}

.note-box {
    background: rgba(255,255,255,0.03);
    border: 1px dashed rgba(255,255,255,0.12);
    border-radius: 18px;
    padding: 14px;
    margin-top: 10px;
    margin-bottom: 10px;
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div {
    border-radius: 16px !important;
}

div[data-testid="stCodeBlock"] {
    border-radius: 18px !important;
}

.stButton > button,
.stDownloadButton > button {
    border-radius: 16px !important;
    font-weight: 700 !important;
    min-height: 48px !important;
}

hr {
    border: none;
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 1.1rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-shell">', unsafe_allow_html=True)
st.markdown('<div class="hero-title">🎨 מחולל פוסטים חכם ל-Canva</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">צור 3 גרסאות שונות לפוסט, סטורי או ריל — עם כיוון קריאייטיבי מלא, אלמנטים ויזואליים, המלצות אנימציה, CTA לוואטסאפ וייצוא ל-Canva Bulk Create.</div>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)


# =========================
# API setup
# =========================
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("לא נמצא OPENAI_API_KEY. צריך להגדיר מפתח API לפני שמריצים.")
    st.stop()

client = OpenAI(api_key=api_key)


# =========================
# Helpers
# =========================
def get_canva_create_url(platform: str, content_type: str) -> str:
    if platform == "אינסטגרם":
        if content_type == "סטורי":
            return "https://www.canva.com/create/instagram-stories/"
        if content_type == "ריל":
            return "https://www.canva.com/create/videos/"
        return "https://www.canva.com/create/instagram-posts/"

    if platform == "פייסבוק":
        return "https://www.canva.com/create/facebook-posts/"

    if platform == "לינקדאין":
        return "https://www.canva.com/create/linkedin-posts/"

    if platform == "טיקטוק":
        return "https://www.canva.com/create/tiktok-videos/"

    return "https://www.canva.com/create/"


def normalize_phone_for_whatsapp(phone: str) -> str:
    raw = re.sub(r"[^\d+]", "", phone.strip())

    if raw.startswith("+"):
        raw = raw[1:]

    if raw.startswith("972"):
        return raw

    if raw.startswith("0"):
        return "972" + raw[1:]

    return raw


def build_whatsapp_link(phone: str, business_name: str) -> str:
    clean_phone = normalize_phone_for_whatsapp(phone)
    if not clean_phone:
        return ""

    message = f"שלום, הגעתי דרך הפרסום של {business_name} ואשמח לקבל פרטים נוספים."
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_message}"


def get_images_by_topic(prompt: str, tone: str, content_type: str) -> list[str]:
    prompt_lower = prompt.lower()

    if any(word in prompt_lower for word in ["קוסמטיקה", "טיפול פנים", "פיגמנטציה", "עור", "אסתטיקה", "beauty", "facial", "skincare", "skin"]):
        if tone == "יוקרתי":
            return [
                "https://images.unsplash.com/photo-1515377905703-c4788e51af15",
                "https://images.unsplash.com/photo-1524504388940-b1c1722653e1",
                "https://images.unsplash.com/photo-1494790108377-be9c29b29330"
            ]
        return [
            "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881",
            "https://images.unsplash.com/photo-1556228720-195a672e8a03",
            "https://images.unsplash.com/photo-1596462502278-27bfdc403348"
        ]

    if any(word in prompt_lower for word in ["שיפוץ", "שיפוצים", "מטבח", "אמבטיה", "רימודל", "remodel", "renovation", "backyard", "landscaping"]):
        return [
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e",
            "https://images.unsplash.com/photo-1581578731548-c64695cc6952",
            "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2"
        ]

    if any(word in prompt_lower for word in ["נדל", "נדלן", "נכס", "דירה", "בית", "real estate", "property", "house", "listing"]):
        return [
            "https://images.unsplash.com/photo-1560518883-ce09059eeffa",
            "https://images.unsplash.com/photo-1570129477492-45c003edd2be",
            "https://images.unsplash.com/photo-1568605114967-8130f3a36994"
        ]

    if any(word in prompt_lower for word in ["תינוק", "תינוקות", "ילדים", "אמא", "baby", "newborn", "kids", "mom"]):
        return [
            "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4",
            "https://images.unsplash.com/photo-1516627145497-ae6968895b74",
            "https://images.unsplash.com/photo-1544126592-807ade215a0b"
        ]

    if any(word in prompt_lower for word in ["ai", "artificial intelligence", "automation", "software", "tech", "technology", "אוטומציה", "בינה מלאכותית", "טכנולוגיה"]):
        return [
            "https://images.unsplash.com/photo-1677442136019-21780ecad995",
            "https://images.unsplash.com/photo-1485827404703-89b55fcc595e",
            "https://images.unsplash.com/photo-1516321318423-f06f85e504b3"
        ]

    if content_type == "סטורי":
        return [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e",
            "https://images.unsplash.com/photo-1492724441997-5dc865305da7",
            "https://images.unsplash.com/photo-1470770841072-f978cf4d019e"
        ]

    return [
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9"
    ]


def auto_assign_templates(content_type: str) -> list[str]:
    if content_type == "פוסט":
        base = ["A", "B", "C"]
    elif content_type == "סטורי":
        base = ["B", "C", "A"]
    else:
        base = ["C", "A", "B"]

    random.shuffle(base)
    return base


def shorten_caption(caption: str, max_lines: int = 4) -> str:
    lines = caption.split("\n")
    lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(lines[:max_lines])


def enforce_business_details(caption: str, business_name: str, whatsapp_link: str) -> str:
    fixed = caption.strip()

    if business_name and business_name not in fixed:
        fixed += f"\n— {business_name}"

    if whatsapp_link and "wa.me" not in fixed and "וואטסאפ" not in fixed:
        fixed += f"\n💬 לפרטים בוואטסאפ"

    fixed = shorten_caption(fixed, max_lines=4)
    return fixed


def parse_canva_execution(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [line.strip("-• ").strip() for line in value.split("\n") if line.strip()]
    return []


def parse_storyboard(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [line.strip("-• ").strip() for line in value.split("\n") if line.strip()]
    return []


def build_bulk_csv(
    versions: list,
    templates: list,
    image_urls: list,
    business_name: str,
    whatsapp_link: str
) -> bytes:
    rows = []

    for i, version in enumerate(versions):
        hashtags_text = " ".join(version["hashtags"])
        caption_fixed = enforce_business_details(
            version["caption"],
            business_name,
            whatsapp_link
        )

        rows.append({
            "template": templates[i],
            "headline": version.get("headline", ""),
            "subheadline": version.get("subheadline", ""),
            "cta": version.get("cta_graphic", ""),
            "caption": caption_fixed,
            "hashtags": hashtags_text,
            "image_url": image_urls[i],
            "business_name": business_name,
            "whatsapp_link": whatsapp_link,
            "visual_concept": version.get("visual_concept", ""),
            "hero_asset_type": version.get("hero_asset_type", ""),
            "overlay_element": version.get("overlay_element", ""),
            "animation_style": version.get("animation_style", ""),
            "background_style": version.get("background_style", ""),
            "color_direction": version.get("color_direction", ""),
            "cta_style": version.get("cta_style", "")
        })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8-sig")


# =========================
# Prompt
# =========================
SYSTEM_PROMPT = """
You are a professional social media creative strategist and Canva content expert.

Your job is to create 3 high-converting social media versions in Hebrew.

Each version must include:
- headline
- subheadline
- cta_graphic
- short caption
- hashtags
- visual_concept
- hero_asset_type
- overlay_element
- animation_style
- background_style
- color_direction
- cta_style
- canva_execution

If content type is Story or Reel, also include:
- storyboard

IMPORTANT:
- Business name should appear naturally inside the caption
- Use WhatsApp as the main CTA if provided
- Do not overload the caption with contact details
- Do not include both phone number and WhatsApp in the caption
- Caption must be short, sharp, modern and conversion-focused
- Think like a creative director, not just a copywriter

CAPTION RULES:
- Max 3-5 short lines
- Hook + benefit + CTA
- Short, scannable, eye-catching
- Avoid long paragraphs

Each version should feel different:
1. Elegant / clean
2. Bold / marketing-oriented
3. Warm / emotional

Return valid JSON only in this structure:
{
  "versions": [
    {
      "version_name": "Version 1",
      "headline": "...",
      "subheadline": "...",
      "cta_graphic": "...",
      "caption": "...",
      "hashtags": ["...", "..."],
      "visual_concept": "...",
      "hero_asset_type": "...",
      "overlay_element": "...",
      "animation_style": "...",
      "background_style": "...",
      "color_direction": "...",
      "cta_style": "...",
      "canva_execution": ["...", "..."],
      "storyboard": ["...", "..."]
    }
  ]
}
""".strip()


def generate_posts(
    prompt: str,
    platform: str,
    tone: str,
    content_type: str,
    creative_mode: str,
    attention_trigger: str,
    business_name: str,
    business_address: str,
    contact_phone: str,
    whatsapp_link: str
) -> dict:
    user_message = f"""
Create 3 different ready-to-publish social media versions.

Platform: {platform}
Content type: {content_type}
Tone: {tone}
Creative mode: {creative_mode}
Attention trigger: {attention_trigger}
Language: Hebrew

Business details:
- Business name: {business_name}
- Business address: {business_address}
- Contact phone: {contact_phone}
- WhatsApp link: {whatsapp_link}

User request:
{prompt}

IMPORTANT:
- Always include the business name in the caption
- Use WhatsApp as the main CTA
- Keep captions short
- Make the output visually attractive and scroll-stopping
- Add creative direction for Canva execution
""".strip()

    response = client.responses.create(
        model="gpt-5",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    raw_text = response.output_text.strip()
    return json.loads(raw_text)


# =========================
# UI - Business info
# =========================
st.markdown('<div class="section-title">פרטי העסק</div>', unsafe_allow_html=True)

b1, b2, b3 = st.columns(3)

with b1:
    business_name = st.text_input(
        "שם העסק",
        placeholder="לדוגמה: Lily Beauty Clinic"
    )

with b2:
    business_address = st.text_input(
        "כתובת העסק",
        placeholder="לדוגמה: הרצל 5, תל אביב"
    )

with b3:
    contact_phone = st.text_input(
        "טלפון ליצירת קשר",
        placeholder="לדוגמה: 052-1234567"
    )

whatsapp_link = build_whatsapp_link(contact_phone, business_name) if contact_phone else ""

chip_cols = st.columns(4)
with chip_cols[0]:
    if business_name:
        st.markdown(f'<div class="info-chip">שם העסק: {business_name}</div>', unsafe_allow_html=True)
with chip_cols[1]:
    if contact_phone:
        st.markdown(f'<div class="info-chip">טלפון: {contact_phone}</div>', unsafe_allow_html=True)
with chip_cols[2]:
    if business_address:
        st.markdown(f'<div class="info-chip">כתובת: {business_address}</div>', unsafe_allow_html=True)
with chip_cols[3]:
    if whatsapp_link:
        st.markdown('<div class="info-chip">CTA לוואטסאפ מוכן</div>', unsafe_allow_html=True)


# =========================
# UI - Content settings
# =========================
st.markdown('<div class="section-title">הגדרות תוכן</div>', unsafe_allow_html=True)

top1, top2, top3 = st.columns(3)

with top1:
    platform = st.selectbox(
        "פלטפורמה",
        ["אינסטגרם", "פייסבוק", "טיקטוק", "לינקדאין"]
    )

with top2:
    content_type = st.selectbox(
        "סוג תוכן",
        ["פוסט", "סטורי", "ריל"]
    )

with top3:
    tone = st.selectbox(
        "סגנון כתיבה",
        ["מקצועי", "חם ואנושי", "יוקרתי", "שיווקי", "קליל"]
    )

mid1, mid2 = st.columns(2)
with mid1:
    creative_mode = st.selectbox(
        "מצב קריאייטיב",
        ["נקי", "יוקרתי", "בולט", "קליני", "ויראלי"]
    )

with mid2:
    attention_trigger = st.selectbox(
        "זווית משיכת תשומת לב",
        ["כאב", "תוצאה", "הוכחה חברתית", "מבצע", "יוקרה", "לפני-אחרי"]
    )

user_prompt = st.text_area(
    "מה אתה רוצה לפרסם?",
    placeholder="לדוגמה: תכתוב לי 3 גרסאות לפוסט לאינסטגרם על טיפול פנים לפני הקיץ, טון יוקרתי אבל אנושי, עם קריאה לפעולה לקביעת תור.",
    height=180,
)


# =========================
# UI - Canva automation
# =========================
st.markdown('<div class="section-title">אוטומציה ל-Canva</div>', unsafe_allow_html=True)

auto_mode = st.toggle("בחר תמונות ותבניות אוטומטית", value=True)

suggested_images = get_images_by_topic(user_prompt, tone, content_type) if user_prompt.strip() else ["", "", ""]
suggested_templates = auto_assign_templates(content_type)

c1, c2, c3 = st.columns(3)

with c1:
    if auto_mode:
        st.markdown('<div class="auto-badge">גרסה 1 - אוטומטי</div>', unsafe_allow_html=True)
        template_1 = suggested_templates[0]
        image_url_1 = suggested_images[0] if len(suggested_images) > 0 else ""
        st.text_input("תבנית לגרסה 1", value=template_1, disabled=True)
        st.text_input("Image URL לגרסה 1", value=image_url_1, disabled=True)
    else:
        template_1 = st.selectbox("תבנית לגרסה 1", ["A", "B", "C"], index=0)
        image_url_1 = st.text_input("Image URL לגרסה 1", placeholder="https://example.com/image1.jpg")

with c2:
    if auto_mode:
        st.markdown('<div class="auto-badge">גרסה 2 - אוטומטי</div>', unsafe_allow_html=True)
        template_2 = suggested_templates[1]
        image_url_2 = suggested_images[1] if len(suggested_images) > 1 else ""
        st.text_input("תבנית לגרסה 2", value=template_2, disabled=True)
        st.text_input("Image URL לגרסה 2", value=image_url_2, disabled=True)
    else:
        template_2 = st.selectbox("תבנית לגרסה 2", ["A", "B", "C"], index=1)
        image_url_2 = st.text_input("Image URL לגרסה 2", placeholder="https://example.com/image2.jpg")

with c3:
    if auto_mode:
        st.markdown('<div class="auto-badge">גרסה 3 - אוטומטי</div>', unsafe_allow_html=True)
        template_3 = suggested_templates[2]
        image_url_3 = suggested_images[2] if len(suggested_images) > 2 else ""
        st.text_input("תבנית לגרסה 3", value=template_3, disabled=True)
        st.text_input("Image URL לגרסה 3", value=image_url_3, disabled=True)
    else:
        template_3 = st.selectbox("תבנית לגרסה 3", ["A", "B", "C"], index=2)
        image_url_3 = st.text_input("Image URL לגרסה 3", placeholder="https://example.com/image3.jpg")


# =========================
# Session state
# =========================
if "generated_versions" not in st.session_state:
    st.session_state.generated_versions = None


# =========================
# Generate
# =========================
if st.button("צור 3 גרסאות", type="primary", use_container_width=True):
    if not user_prompt.strip():
        st.warning("צריך לכתוב בקשה לפני שיוצרים תוכן.")
    elif not business_name.strip():
        st.warning("צריך להזין את שם העסק.")
    elif not contact_phone.strip():
        st.warning("צריך להזין מספר טלפון ליצירת קשר.")
    else:
        with st.spinner("יוצר 3 גרסאות..."):
            try:
                result = generate_posts(
                    prompt=user_prompt,
                    platform=platform,
                    tone=tone,
                    content_type=content_type,
                    creative_mode=creative_mode,
                    attention_trigger=attention_trigger,
                    business_name=business_name,
                    business_address=business_address,
                    contact_phone=contact_phone,
                    whatsapp_link=whatsapp_link
                )
                versions = result.get("versions", [])

                if len(versions) != 3:
                    st.error("המודל לא החזיר 3 גרסאות תקינות. נסה שוב.")
                else:
                    st.session_state.generated_versions = versions
                    st.success("3 הגרסאות מוכנות.")

            except Exception as e:
                st.error(f"קרתה שגיאה: {e}")


# =========================
# Render results
# =========================
def render_version_card(version: dict, index: int, template_name: str, image_url: str) -> None:
    hashtags_text = " ".join(version.get("hashtags", []))
    canva_url = get_canva_create_url(platform, content_type)

    caption_fixed = enforce_business_details(
        caption=version.get("caption", ""),
        business_name=business_name,
        whatsapp_link=whatsapp_link
    )

    full_post = f"""{caption_fixed}

{hashtags_text}
"""

    canva_steps = parse_canva_execution(version.get("canva_execution", []))
    storyboard = parse_storyboard(version.get("storyboard", []))

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="version-title">גרסה {index}</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.markdown('<div class="small-label">תבנית</div>', unsafe_allow_html=True)
        st.code(template_name, language="markdown")

        st.markdown('<div class="small-label">כותרת ראשית</div>', unsafe_allow_html=True)
        st.code(version.get("headline", ""), language="markdown")

        st.markdown('<div class="small-label">כותרת משנה</div>', unsafe_allow_html=True)
        st.code(version.get("subheadline", ""), language="markdown")

        st.markdown('<div class="small-label">CTA לגרפיקה</div>', unsafe_allow_html=True)
        st.code(version.get("cta_graphic", ""), language="markdown")

        st.markdown('<div class="small-label">קונספט ויזואלי</div>', unsafe_allow_html=True)
        st.code(version.get("visual_concept", ""), language="markdown")

        st.markdown('<div class="small-label">נכס ויזואלי מרכזי</div>', unsafe_allow_html=True)
        st.code(version.get("hero_asset_type", ""), language="markdown")

    with col_b:
        st.markdown('<div class="small-label">אלמנט מושך עין</div>', unsafe_allow_html=True)
        st.code(version.get("overlay_element", ""), language="markdown")

        st.markdown('<div class="small-label">סגנון אנימציה</div>', unsafe_allow_html=True)
        st.code(version.get("animation_style", ""), language="markdown")

        st.markdown('<div class="small-label">סגנון רקע</div>', unsafe_allow_html=True)
        st.code(version.get("background_style", ""), language="markdown")

        st.markdown('<div class="small-label">כיוון צבעים</div>', unsafe_allow_html=True)
        st.code(version.get("color_direction", ""), language="markdown")

        st.markdown('<div class="small-label">סגנון CTA</div>', unsafe_allow_html=True)
        st.code(version.get("cta_style", ""), language="markdown")

        st.markdown('<div class="small-label">קישור לתמונה</div>', unsafe_allow_html=True)
        st.code(image_url if image_url else "לא הוזן", language="markdown")

    st.markdown('<div class="small-label">Caption לפוסט</div>', unsafe_allow_html=True)
    st.code(caption_fixed, language="markdown")

    st.markdown('<div class="small-label">Hashtags</div>', unsafe_allow_html=True)
    st.code(hashtags_text, language="markdown")

    st.markdown('<div class="small-label">Post מלא (מוכן להדבקה)</div>', unsafe_allow_html=True)
    st.code(full_post, language="markdown")

    if canva_steps:
        st.markdown('<div class="small-label">איך לבצע ב-Canva</div>', unsafe_allow_html=True)
        steps_md = "\n".join([f"- {step}" for step in canva_steps])
        st.markdown(f'<div class="note-box">{steps_md}</div>', unsafe_allow_html=True)

    if content_type in ["סטורי", "ריל"] and storyboard:
        st.markdown('<div class="small-label">Storyboard</div>', unsafe_allow_html=True)
        storyboard_md = "\n".join([f"- {item}" for item in storyboard])
        st.markdown(f'<div class="note-box">{storyboard_md}</div>', unsafe_allow_html=True)

    btn1, btn2 = st.columns(2)
    with btn1:
        st.link_button(
            "פתח פורמט מתאים ב-Canva 🚀",
            canva_url,
            use_container_width=True
        )
    with btn2:
        if whatsapp_link:
            st.link_button(
                "פתח שיחת וואטסאפ 💬",
                whatsapp_link,
                use_container_width=True
            )

    st.markdown('</div>', unsafe_allow_html=True)


versions = st.session_state.generated_versions

if versions:
    templates = [template_1, template_2, template_3]
    image_urls = [image_url_1, image_url_2, image_url_3]

    st.info("לכל גרסה יש עכשיו גם כיוון קריאייטיבי מלא: ויזואל, אנימציה, אלמנטים מושכי עין והוראות ביצוע ב-Canva.")

    tab1, tab2, tab3 = st.tabs(["גרסה 1", "גרסה 2", "גרסה 3"])

    with tab1:
        render_version_card(versions[0], 1, template_1, image_url_1)

    with tab2:
        render_version_card(versions[1], 2, template_2, image_url_2)

    with tab3:
        render_version_card(versions[2], 3, template_3, image_url_3)

    csv_data = build_bulk_csv(
        versions=versions,
        templates=templates,
        image_urls=image_urls,
        business_name=business_name,
        whatsapp_link=whatsapp_link
    )

    st.markdown('<div class="section-title">ייצוא ל-Canva Bulk Create</div>', unsafe_allow_html=True)
    st.download_button(
        label="⬇️ הורד CSV מוכן ל-Canva",
        data=csv_data,
        file_name="canva_bulk_create.csv",
        mime="text/csv",
        use_container_width=True
    )