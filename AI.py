import os
import json
import requests
from groq import Groq
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)

groq_client = Groq(
    api_key=GROQ_API_KEY
)

PROMPT = """
আপনি বাংলাদেশের একজন পেশাদার সংবাদ সম্পাদক।

নিচের তথ্যের ভিত্তিতে ১৮০-২৫০ শব্দের একটি প্রমিত বাংলা সংবাদ লিখুন।

নিয়ম:

- শুধুমাত্র প্রদত্ত তথ্য ব্যবহার করুন।
- কোনো তথ্য, সংখ্যা বা উদ্ধৃতি তৈরি করবেন না।
- ৩-৪টি স্বাভাবিক অনুচ্ছেদ লিখুন।
- প্রথম অনুচ্ছেদে মূল ঘটনা লিখুন।
- শেষ অনুচ্ছেদে ঘটনার গুরুত্ব লিখুন।
- ভাষা হবে স্বাভাবিক, সাবলীল ও সংবাদপত্র উপযোগী বাংলা।
- কোনো ইংরেজি অনুচ্ছেদ লিখবেন না।
- শুধুমাত্র সংবাদ লিখুন।

বিভাগ:
{category}

শিরোনাম:
{title}

তথ্য:
{article}
"""

def gemini_rewrite(title, category, article):

    prompt = PROMPT.format(
        title=title,
        category=category,
        article=article
    )

    try:
        interaction = gemini_client.interactions.create(
            model="models/gemini-3.6-flash",
            input=prompt,
            generation_config={
                "thinking_level": "medium",
                "max_output_tokens": 2048,
            },
        )

        return interaction.steps[-1].text.strip()

    except Exception as e:
        print("Gemini Error:", e)
        return None
