import os
import time
import feedparser
from groq import Groq
from googleapiclient.discovery import build

# --- CORE CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "gsk_Rqi7My09C786WQVCf8BYWgdyb3FYmpwebe8aTyIYcyE2gOZzbzD")
BLOGGER_API_KEY = os.environ.get("BLOGGER_API_KEY", "AIzaSyCcdlaxhi3mNjF-pfTBsWOVezl9mmRcUm4")
BLOG_ID = os.environ.get("BLOG_ID", "1222511286621075933")

FEEDS = {
    'World News': 'https://nytimes.com',
    'Technology': 'https://feedburner.com',
    'Business': 'https://cnbc.com',
    'Science': 'https://sciencedaily.com'
}

NICHE_TAGS = {
    'World News': 'আন্তর্জাতিক',
    'Technology': 'প্রযুক্তি',
    'Business': 'ব্যবসায়',
    'Science': 'বিজ্ঞান'
}

THUMBNAILS = {
    'World News': 'https://unsplash.com',
    'Technology': 'https://unsplash.com',
    'Business': 'https://unsplash.com',
    'Science': 'https://unsplash.com'
}

print("⚙️ Initializing Core API Engines...")
groq_client = Groq(api_key=GROQ_API_KEY)
blogger = build('blogger', 'v3', developerKey=BLOGGER_API_KEY)

def run_portal():
    print("🤖 [Lens24 Engine] actively scanning global news networks...")

    for niche, feed_url in FEEDS.items():
        print(f"\n🔍 Checking channel: {niche}")
        parsed_feed = feedparser.parse(feed_url)
        bangla_label = NICHE_TAGS.get(niche, 'লাইভ আপডেট')
        img_url = THUMBNAILS.get(niche, 'https://unsplash.com')
        
        if not parsed_feed.entries:
            print(f"⚠️ Warning: No entries found for channel {niche}")
            continue
            
        entry = parsed_feed.entries[0]
        print(f"🔥 Found Raw Story Headline: {entry.title}")
        
        # Fallback safety validation to prevent blank text payloads
        raw_context = getattr(entry, 'summary', getattr(entry, 'description', entry.title))
        
        title_prompt = f"Translate this news headline into professional journalism style Bangla. Return ONLY the translated text, nothing else: {entry.title}"
        body_prompt = (
            f"You are a professional Bangladeshi news reporter. Translate and rewrite the following news article text "
            f"into a high-quality, engaging news post in the Bangla language. Use clean HTML paragraphs (<p>) "
            f"to structure the text formatting cleanly. Do not write a headline. Do not include any English characters.\n\n"
            f"Text to rewrite: {raw_context}"
        )
        
        try:
            print("🧠 Requesting lightning translation from Groq Llama 3...")
            t_comp = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": title_prompt}],
                temperature=0.1
            )
            final_title = t_comp.choices.message.content.strip().replace('"', '')
            print(f"📝 Translated Headline: {final_title}")

            b_comp = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": body_prompt}],
                temperature=0.5
            )
            final_content = b_comp.choices.message.content.strip()

            html_content = f'<div class="separator" style="clear: both; text-align: center;"><img src="{img_url}" style="max-width: 100%; height: auto; margin-bottom: 15px;"/></div><p>{final_content}</p>'

            post_payload = {
                "kind": "blogger#post",
                "title": final_title,
                "content": html_content,
                "labels": [str(bangla_label), "ব্রেকিং নিউজ"]
            }
            
            print(f"🚀 Pushing payload data to Blogger Blog ID: {BLOG_ID}...")
            response = blogger.posts().insert(blogId=BLOG_ID, body=post_payload).execute()
            print(f"✅ Successfully published! Post URL: {response.get('url')}")
            
        except Exception as post_err:
            print(f"❌ Critical pipeline stall on item: {post_err}")

if __name__ == '__main__':
    run_portal()
    print("\n🏁 Master cloud sequence task completed.")
