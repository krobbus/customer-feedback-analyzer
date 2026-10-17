import json
import urllib.request
import os

from scripts.env_loader import load_env_file

def local_sentiment_check(text: str):
    text_lower = text.lower()
    
    positive_keywords = ["love", "loved", "great", "excellent", "fantastic", "amazing", "best", "wonderful", "happy", "fast", "smooth", "perfect"]
    negative_keywords = ["broken", "terrible", "horrible", "awful", "worst", "hate", "crashes", "poor", "disappointed", "lags", "useless", "garbage"]
    
    has_positive = any(word in text_lower for word in positive_keywords)
    has_negative = any(word in text_lower for word in negative_keywords)

    if has_positive and has_negative:
        return None 
    elif has_positive and not has_negative:
        return "POSITIVE"
    elif has_negative and not has_positive:
        return "NEGATIVE"
    
    return None

def analyze_sentiment_with_api(text: str) -> str:
    local_result = local_sentiment_check(text)
    if local_result is not None:
        return local_result

    load_env_file()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "ERROR: GEMINI_API_KEY not configured in environment file"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    payload = {
        "systemInstruction": {
            "parts": [{
                "text": (
                    "Classify the sentiment of the customer feedback. "
                    "Return exactly one sentiment value."
                )
            }]
        },
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 128,
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "sentiment": {
                        "type": "STRING",
                        "enum": ["POSITIVE", "NEGATIVE", "NEUTRAL"],
                    }
                },
                "required": ["sentiment"],
            },
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        candidates = result.get("candidates", [])
        if not candidates:
            return "API_ERROR: Gemini returned no candidates"

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        response_text = "".join(
            part["text"] for part in parts if isinstance(part.get("text"), str)
        ).strip()
        
        response_data = json.loads(response_text)
        sentiment = response_data.get("sentiment", "NEUTRAL").strip().upper()
        
        if sentiment not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
            return "NEUTRAL"
        return sentiment
    except Exception as error:
        return f"API_ERROR: {error}"