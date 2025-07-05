import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from urllib.parse import urlparse
import re
import time
from functools import lru_cache

@st.cache_resource
def get_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

@lru_cache(maxsize=32)
def fetch_and_extract_text(url):
    try:
        if not re.match(r'^https?://', url):
            url = 'http://' + url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text_blocks = soup.find_all(['p'])
        main_text = ' '.join([block.get_text(strip=True) for block in text_blocks])
        return main_text.strip()

    except Exception as e:
        print(f"[ERROR] URL fetch/extract failed: {e}")
        return None

def summarize_text(text, max_length=500, min_length=100):
    """
    Returns a longer summary by increasing max_length and summarizing more chunks.
    """
    if not text:
        return None

    summarizer = get_summarizer()

    try:
        chunk_size = 1000
        text_chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        summaries = []

        for chunk in text_chunks:
            summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)[0]['summary_text']
            summaries.append(summary)
            # Remove or increase this limit to include more detailed summary
            if len(summaries) >= 6:  # Increased from 3 to 6
                break

        return " ".join(summaries)

    except Exception as e:
        print(f"[ERROR] Summarization failed: {e}")
        return None

# Streamlit UI
st.set_page_config(page_title="Detailed Web Content Summarizer", layout="centered")
st.title("📰 Web Content Summarizer")
st.markdown("Paste any **website URL**, and get a **detailed summary** of its main content.")

url = st.text_input("🔗 Enter a website link (http:// or https://):", "")

if st.button("Summarize Now"):
    if url:
        with st.spinner("⏳ Fetching and summarizing content..."):
            start = time.time()
            text = fetch_and_extract_text(url)

            if text:
                summary = summarize_text(text)

                if summary:
                    st.success(f"✅ Detailed summary generated in {round(time.time() - start, 2)}s")
                    st.subheader("📝 Detailed Summary:")
                    st.write(summary)
                else:
                    st.error("⚠️ Could not generate a summary.")
            else:
                st.error("⚠️ Could not extract text from the provided URL.")
    else:
        st.warning("Please enter a valid URL starting with http:// or https://")
