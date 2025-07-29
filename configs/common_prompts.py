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
- Write a concise summary in plain {language} that captures the key points and important facts
- Adjust the length based on the article's content (1-4 lines maximum)
- Include essential details like who, what, when, where if relevant
- Determine the category of the article. Choose ONLY ONE from: {', '.join(categories)}
- Use a neutral, formal tone suitable for news articles
- Avoid casual or conversational phrases
- Respond in the exact format below:
Category: <one of above>
Content: <your summary>

If the content is not suitable for summarization (e.g., too short, incomplete, or lacks meaning), just return: SKIP

Article:
{{content}}"""