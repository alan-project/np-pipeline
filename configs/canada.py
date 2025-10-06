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

    return f"""
You are a professional news translator. Translate the following English news title and summary into {lang}.

STRICT REQUIREMENTS:
1. ALL proper nouns (names, locations, organizations, brands) MUST include the original English text in parentheses
2. Format: Translation(Original)
3. EXCEPTION: If translation equals original text, omit parentheses (e.g., UN not UN(UN), Apple not Apple(Apple))
4. For repeated proper nouns: Include parentheses ONLY on first occurrence, omit on subsequent mentions
5. This rule is MANDATORY - apply to every proper noun in the content

DETAILED EXAMPLES for {lang}:
- Person names (first occurrence with parentheses, subsequent without):
  * Korean: 저스틴 트뤼도(Justin Trudeau) 총리가 발표했다... 이후 트뤼도는...
  * Hindi: प्रधानमंत्री जस्टिन ट्रूडो(Justin Trudeau) ने घोषणा की... बाद में ट्रूडो ने...
  * Chinese: 总理贾斯汀·特鲁多(Justin Trudeau)宣布... 后来特鲁多...
  * Arabic: رئيس الوزراء جاستن ترودو(Justin Trudeau) أعلن... لاحقاً، قال ترودو...

- Company/Organization names:
  * Korean: 유엔(UN), 애플(Apple), 구글(Google)
  * Hindi: संयुक्त राष्ट्र(UN), एप्पल(Apple), गूगल(Google)
  * Chinese: 联合国(UN), 苹果(Apple), 谷歌(Google)
  * Arabic: الأمم المتحدة(UN), أبل(Apple), جوجل(Google)

- City/Country names:
  * Korean: 토론토(Toronto), 오타와(Ottawa), 밴쿠버(Vancouver)
  * Hindi: टोरंटो(Toronto), ओटावा(Ottawa), वैंकूवर(Vancouver)
  * Chinese: 多伦多(Toronto), 渥太华(Ottawa), 温哥华(Vancouver)
  * Arabic: تورونتو(Toronto), أوتاوا(Ottawa), فانكوفر(Vancouver)

IMPORTANT NOTES:
- For the title, translate naturally in {lang} but keep it short and concise. Avoid using parentheses in the title.
- Maintain a neutral, objective tone suitable for news articles.
- Use formal language and avoid conversational tone.
- Do not add any extra comments or labels.

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
