import sys
import os
import csv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sentiment_checker import analyze_sentiment_with_api

def process_csv_feedback(file_path: str):
    if not os.path.exists(file_path):
        print(f"[Error]: File not found at '{file_path}'")
        return

    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            if not fieldnames:
                print("[Error]: The CSV file is empty or missing headers.")
                return
            
            target_col = None
            for col in fieldnames:
                col_lower = col.strip().lower()
                if col_lower in ["feedback", "comment", "review", "reviews", "comments"]:
                    target_col = col
                    break

            if not target_col:
                for col in fieldnames:
                    col_lower = col.strip().lower()
                    if ("feedback" in col_lower or "comment" in col_lower) and "id" not in col_lower:
                        target_col = col
                        break
            
            if not target_col:
                print(f"[Error]: Could not find a valid feedback column.")
                print(f"Available columns are: {fieldnames}")
                return

            print(f"[System]: Found target column -> '{target_col}'\n")
            print("-" * 65)
            print(f"{'Row':<5} | {'Feedback Snippet':<40} | {'Sentiment':<10}")
            print("-" * 65)

            counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
            row_count = 0

            for index, row in enumerate(reader):
                text = row.get(target_col, "").strip()
                if not text:
                    continue

                row_count += 1
                sentiment = analyze_sentiment_with_api(text)

                if sentiment in counts:
                    counts[sentiment] += 1

                snippet = (text[:37] + "...") if len(text) > 40 else text
                print(f"{index + 2:<5} | {snippet:<40} | {sentiment:<10}")

            print("-" * 65)
            print("Batch Processing Complete!")
            print(f"Summary -> Positive: {counts['POSITIVE']} | Negative: {counts['NEGATIVE']} | Neutral: {counts['NEUTRAL']}")

    except Exception as e:
        print(f"[Error]: Failed to process CSV file: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = input("Enter path to your CSV file (e.g., reviews.csv): ").strip().strip('"')
    process_csv_feedback(path)