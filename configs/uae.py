import os
from .common_prompts import summarization_prompt_with_category

summarization_prompt = summarization_prompt_with_category('Arabic')

def translation_prompt(lang):
    # Check if source and target languages are the same
    source_lang = 'ar'  # UAE's base language

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
        "ur": """- Person names: متحدہ عرب امارات کے صدر شیخ محمد بن زاید(محمد بن زايد), شیخ محمد بن راشد(محمد بن راشد)
- Company/Organization names: امارات ایئرلائنز(طيران الإمارات), اتصالات(اتصالات), آدنوک(أدنوك)
- City/Country names: ابوظبی(أبوظبي), دبئی(دبي), شارجہ(الشارقة), عجمان(عجمان)""",

        "hi": """- Person names: यूएई के राष्ट्रपति शेख मोहम्मद बिन जायद(محمد بن زايد), शेख मोहम्मद बिन राशिद(محمد بن راشد)
- Company/Organization names: एमिरेट्स एयरलाइंस(طيران الإمارات), एतिसलात(اتصالات), अडनॉक(أدنوك)
- City/Country names: अबू धाबी(أبوظبي), दुबई(دبي), शारजाह(الشارقة), अजमान(عجمان)""",

        "ml": """- Person names: യുഎഇ പ്രസിഡന്റ് ഷെയ്ഖ് മുഹമ്മദ് ബിൻ സായിദ്(محمد بن زايد), ഷെയ്ഖ് മുഹമ്മദ് ബിൻ റാഷിദ്(محمد بن راشد)
- Company/Organization names: എമിറേറ്റ്സ് എയർലൈൻസ്(طيران الإمارات), എത്തിസലാത്ത്(اتصالات), അഡ്നോക്ക്(أدنوك)
- City/Country names: അബുദാബി(أبوظبي), ദുബായ്(دبي), ഷാർജ(الشارقة), അജ്മാൻ(عجمان)""",

        "en": """- Person names: UAE President Sheikh Mohammed bin Zayed(محمد بن زايد), Sheikh Mohammed bin Rashid(محمد بن راشد)
- Company/Organization names: Emirates Airlines(طيران الإمارات), Etisalat(اتصالات), ADNOC(أدنوك)
- City/Country names: Abu Dhabi(أبوظبي), Dubai(دبي), Sharjah(الشارقة), Ajman(عجمان)"""
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
You are an expert news editor working for a UAE news app targeted at newcomers to UAE.
Select the top {top_n} most important and engaging news articles from the list below.

Selection criteria:
- Prefer articles related to UAE or Middle East when available
- If no UAE/Middle East articles are available, select the most globally important news
- Overall importance and public impact
- Reader engagement potential
- Avoid selecting multiple articles with very similar or identical titles

IMPORTANT: You must respond with EXACTLY the Article ID as shown in the list below.
Return ONLY the article IDs of the selected articles, one per line, nothing else.
You MUST select {top_n} articles even if none are specifically about UAE/Middle East.
"""

config = {
    "country": "UAE",
    "api_url": os.getenv("NEWS_API_URL"),
    "firestore_collection": "uae_articles",
    "info_doc": "uae_info",
    "base_lang": "ar",
    "lang_list": ["ur", "hi", "ml", "en"],
    "select_all": False,
    "top_article_ratio": 0.15,
    "timezone": "Asia/Dubai",
    "daily_popular_days": 2,
    "daily_popular_limit": 10,
    "summarization_prompt": summarization_prompt,
    "translation_prompt": translation_prompt,
    "top_prompt": top_prompt
}