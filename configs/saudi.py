import os
from .common_prompts import summarization_prompt_with_category

summarization_prompt = summarization_prompt_with_category('Arabic')

def translation_prompt(lang):
    # Check if source and target languages are the same
    source_lang = 'ar'  # Saudi Arabia's base language

    # Simple logic: only skip parentheses if source and target are the same
    if lang == source_lang:
        return f"""
You are a professional news translator. Translate the following Arabic news title and summary into {lang}.

IMPORTANT: Since the source language (Arabic) and target language ({lang}) are the same, DO NOT add parentheses with original text for proper nouns.

- For the title, translate naturally in {lang} but keep it short and concise.
- Maintain a neutral, objective tone suitable for news articles.
- Use formal language and avoid conversational tone.
- Do not add any extra comments or labels.

Return your response in this format:
Title: <translated title>
Content: <translated summary>
"""

    # Language-specific examples
    examples = {
        "ur": """- Person names: سعودی ولی عہد محمد بن سلمان(محمد بن سلمان), بادشاہ سلمان(الملك سلمان)
- Company/Organization names: سعودی آرامکو(أرامكو السعودية), سعودی ائیرلائنز(الخطوط السعودية)
- City/Country names: ریاض(الرياض), جدہ(جدة), مکہ مکرمہ(مكة المكرمة), مدینہ منورہ(المدينة المنورة)""",

        "hi": """- Person names: सऊदी क्राउन प्रिंस मोहम्मद बिन सलमान(محمد بن سلمان), राजा सलमान(الملك سلمان)
- Company/Organization names: सऊदी अरामको(أرامكو السعودية), सऊदी एयरलाइंस(الخطوط السعودية)
- City/Country names: रियाद(الرياض), जेद्दाह(جدة), मक्का(مكة المكرمة), मदीना(المدينة المنورة)""",

        "bn": """- Person names: সৌদি ক্রাউন প্রিন্স মোহাম্মদ বিন সালমান(محمد بن سلمان), রাজা সালমান(الملك سلمان)
- Company/Organization names: সৌদি আরামকো(أرامكو السعودية), সৌদি এয়ারলাইন্স(الخطوط السعودية)
- City/Country names: রিয়াদ(الرياض), জেদ্দা(جدة), মক্কা(مكة المكرمة), মদিনা(المدينة المنورة)""",

        "en": """- Person names: Saudi Crown Prince Mohammed bin Salman(محمد بن سلمان), King Salman(الملك سلمان)
- Company/Organization names: Saudi Aramco(أرامكو السعودية), Saudi Airlines(الخطوط السعودية)
- City/Country names: Riyadh(الرياض), Jeddah(جدة), Mecca(مكة المكرمة), Medina(المدينة المنورة)"""
    }

    lang_examples = examples.get(lang, examples["en"])  # Default to English if lang not found

    return f"""
You are a professional news translator. Translate the following Arabic news title and summary into {lang}.

STRICT REQUIREMENTS:
1. ALL proper nouns (names, locations, organizations, brands) MUST include the original Arabic text in parentheses
2. Format: Translation(Original)
3. This rule is MANDATORY - apply to every proper noun in the content

DETAILED EXAMPLES for {lang}:
{lang_examples}

IMPORTANT NOTES:
- For the title, translate naturally in {lang} but keep it short and concise. Avoid using parentheses in the title.
- Maintain a neutral, objective tone suitable for news articles.
- Use formal language and avoid conversational tone.
- Do not add any extra comments or labels.
- CRITICAL: Use ONLY {lang} script/characters in your translation. Do NOT mix characters from other languages.

Return your response in this format:
Title: <translated title>
Content: <translated summary with ALL proper nouns followed by (Original Arabic)>
"""

def top_prompt(top_n):
    return f"""
You are an expert news editor working for a Saudi news app targeted at newcomers to Saudi.
Select the top {top_n} most important and engaging news articles from the list below.

Selection criteria:
- Prefer articles related to Saudi Arabia or Middle East when available
- If no Saudi/Middle East articles are available, select the most globally important news
- Overall importance and public impact
- Reader engagement potential
- Avoid selecting multiple articles with very similar or identical titles

IMPORTANT: You must respond with EXACTLY the Article ID as shown in the list below.
Return ONLY the article IDs of the selected articles, one per line, nothing else.
You MUST select {top_n} articles even if none are specifically about Saudi/Middle East.
"""

config = {
    "country": "Saudi",
    "api_url": os.getenv("NEWS_API_URL"),
    "firestore_collection": "saudi_articles",
    "info_doc": "saudi_info",
    "base_lang": "ar",
    "lang_list": ["ur", "hi", "bn", "en"],
    "select_all": False,
    "top_article_ratio": 0.12,
    "timezone": "Asia/Riyadh",
    "daily_popular_days": 2,
    "daily_popular_limit": 10,
    "summarization_prompt": summarization_prompt,
    "translation_prompt": translation_prompt,
    "top_prompt": top_prompt
}