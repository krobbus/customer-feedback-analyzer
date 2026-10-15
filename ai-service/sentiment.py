import sys
import json
import urllib.request
import urllib.error
import os

from scripts.env_loader import load_env_file

def analyze_sentiment_with_api(text: str) -> str:
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
            prompt_feedback = result.get("promptFeedback", {})
            block_reason = prompt_feedback.get("blockReason")
            if block_reason:
                return f"API_ERROR: Gemini blocked the prompt ({block_reason})"
            return "API_ERROR: Gemini returned no candidates"

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        response_text = "".join(
            part["text"] for part in parts if isinstance(part.get("text"), str)
        ).strip()
        if not response_text:
            finish_reason = candidate.get("finishReason", "unknown")
            return f"API_ERROR: Gemini returned no text (finish reason: {finish_reason})"

        try:
            response_data = json.loads(response_text)
            if isinstance(response_data, dict):
                sentiment = response_data.get("sentiment")
            elif isinstance(response_data, str):
                sentiment = response_data
            else:
                sentiment = None
        except json.JSONDecodeError:
            sentiment = response_text.upper()
        if isinstance(sentiment, str):
            sentiment = sentiment.strip().upper()
        if sentiment not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
            return "API_ERROR: Gemini returned an invalid sentiment"
        return sentiment
    except urllib.error.HTTPError as error:
        try:
            error_body = json.loads(error.read().decode("utf-8"))
            error_message = error_body.get("error", {}).get("message")
        except (AttributeError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
            error_message = None
        if error_message:
            return f"API_ERROR: Gemini returned HTTP {error.code}: {error_message}"
        return f"API_ERROR: Gemini returned HTTP {error.code}"
    except (urllib.error.URLError, TimeoutError) as error:
        return f"API_ERROR: Gemini request failed: {error}"
    except (AttributeError, TypeError, json.JSONDecodeError):
        return "API_ERROR: Gemini returned an invalid response"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_text = " ".join(sys.argv[1:])
        print(analyze_sentiment_with_api(input_text))
    else:
        print("ERROR: No text provided")