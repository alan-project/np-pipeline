import os
from .common_prompts import summarization_prompt_with_category

summarization_prompt = summarization_prompt_with_category('English')

def translation_prompt(lang):
    # Check if source and target languages are the same
    source_lang = 'en'  # Canada's base language

    # Simple logic: only skip parentheses if source and target are the same
    if lang == source_lang:
        return f"""
You are a professional news translator. Translate the following English news title and summary into {lang}.

IMPORTANT: Since the source language (English) and target language ({lang}) are the same, DO NOT add parentheses with original text for proper nouns.

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
        "ko": """- Person names: 저스틴 트뤼도(Justin Trudeau), 조 바이든(Joe Biden)
- Company/Organization names: 유엔(UN), 애플(Apple), 구글(Google)
- City/Country names: 토론토(Toronto), 오타와(Ottawa), 밴쿠버(Vancouver)""",

        "hi": """- Person names: जस्टिन ट्रूडो(Justin Trudeau), जो बाइडन(Joe Biden)
- Company/Organization names: संयुक्त राष्ट्र(UN), एप्पल(Apple), गूगल(Google)
- City/Country names: टोरंटो(Toronto), ओटावा(Ottawa), वैंकूवर(Vancouver)""",

        "zh": """- Person names: 贾斯汀·特鲁多(Justin Trudeau), 乔·拜登(Joe Biden)
- Company/Organization names: 联合国(UN), 苹果(Apple), 谷歌(Google)
- City/Country names: 多伦多(Toronto), 渥太华(Ottawa), 温哥华(Vancouver)""",

        "ar": """- Person names: جاستن ترودو(Justin Trudeau), جو بايدن(Joe Biden)
- Company/Organization names: الأمم المتحدة(UN), أبل(Apple), جوجل(Google)
- City/Country names: تورونتو(Toronto), أوتاوا(Ottawa), فانكوفر(Vancouver)"""
    }

    lang_examples = examples.get(lang, examples["ko"])  # Default to Korean if lang not found

    return f"""
You are a professional news translator. Translate the following English news title and summary into {lang}.

STRICT REQUIREMENTS:
1. ONLY these proper nouns need parentheses with original English text:
   - Person names (politicians, celebrities, public figures)
   - Geographic locations (countries, cities, regions)
   - Organizations and companies
   - Brand names
2. Format: Translation(Original)
3. DO NOT add parentheses for:
   - Common nouns (war, prisoner, video, shock, death, etc.)
   - Verbs or adjectives
   - General concepts or abstract nouns
4. This rule is MANDATORY - be precise about what qualifies as a proper noun

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
Content: <translated summary with ALL proper nouns followed by (Original English)>
"""

def top_prompt(top_n):
    return f"""
You are an expert news editor working for a Canadian news app targeted at newcomers to Canada.
Select the top {top_n} most important and engaging news articles from the list below.

Selection criteria:
- Prefer articles related to Canada or North America when available
- If no Canada/North America articles are available, select the most globally important news
- Overall importance and public impact
- Reader engagement potential
- Avoid selecting multiple articles with very similar or identical titles

CRITICAL: You must copy EXACTLY the Article ID as shown below. Do NOT modify, shorten, or change any characters.
- Copy the entire ID string character by character
- Double-check each ID before including it in your response
- Return ONLY the article IDs, one per line, no additional text
- You MUST select exactly {top_n} articles

Example format:
eaf5dbb6c306b8ab5f539ed210b18958
a153b83d4640740c93766d23dbafcd67
"""

config = {
    "country": "Canada",
    "api_url": os.getenv("NEWS_API_URL"),
    "firestore_collection": "canada_articles",
    "info_doc": "canada_info",
    "base_lang": "en",
    "lang_list": ["ko", "hi", "zh", "ar"],
    "select_all": False,
    "top_article_ratio": 0.12,
    "timezone": "America/Toronto",
    "daily_popular_days": 2,
    "daily_popular_limit": 10,
    "summarization_prompt": summarization_prompt,
    "translation_prompt": translation_prompt,
    "top_prompt": top_prompt
}
