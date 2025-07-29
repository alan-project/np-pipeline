"""
Common prompts shared across all country configurations
"""

def summarization_prompt_with_category(language):
    """
    Generate summarization prompt with category classification
    Args:
        language: Target language for the summary (e.g., 'English', 'German', 'Arabic')
    """
    categories = [
        "crime",
        "politics", 
        "business",
        "culture",
        "technology",
        "sports",
        "health",
        "other"
    ]
    
    return f"""You're a news editor and categorization assistant. Summarize and categorize the following article.
- Write a brief summary in 2~3 lines in plain {language}
- Determine the category of the article. Choose ONLY ONE from: {', '.join(categories)}
- Use a neutral, formal tone suitable for news articles
- Avoid casual or conversational phrases
- Respond in the exact format below:
Category: <one of above>
Content: <your summary>

If the content is not suitable for summarization (e.g., too short, incomplete, or lacks meaning), just return: SKIP

Article:
{{content}}"""