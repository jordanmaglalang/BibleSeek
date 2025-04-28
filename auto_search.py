import re

def find_bible_verses(text):
    # Regex to find Bible references (e.g., John 3:16)
    pattern = r'\b([1-3]?\s?[A-Za-z]+)\s(\d+):(\d+)\b'
    verses = re.findall(pattern, text)
    return verses
def generate_google_search_link(book, chapter, verse):
    query = f"{book} {chapter}:{verse}"
    return f"https://www.google.com/search?q={query.replace(' ', '+')}"
