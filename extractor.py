import feedparser
from newspaper import Article
import requests
from bs4 import BeautifulSoup

def extract_article(url):
    # Try Newspaper3k first
    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text.strip()

        if len(text) >= 1000:
            return text[:5000]

    except Exception:
        pass

    # Fallback: BeautifulSoup
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        paragraphs = []

        for p in soup.find_all("p"):
            t = p.get_text(" ", strip=True)

            if len(t) > 40:
                paragraphs.append(t)

        text = "\n".join(paragraphs)

        if len(text) >= 300:
            return text[:5000]

    except Exception as e:
        print("BeautifulSoup Error:", e)

    return ""

def fetch_news(sources):

    items = []

    for source in sources:

        try:
            rss = source["rss"]

            if not rss:
             continue

            feed = feedparser.parse(
            requests.get(
             rss,
             headers={"User-Agent": "Mozilla/5.0"},
             timeout=20
             ).content
            )

            source_name = source["name"]
            category = source["category"]
            priority = source["priority"]

            for e in feed.entries[:6]:

                title = e.get("title", "").strip()

                if not title:
                    continue

                
                summary = e.get("summary", "")

                if not summary:
                    summary = e.get("description", "")

                if not summary:
                    summary = title


                link = e.get("link", "")

                image = ""

                if hasattr(e, "media_content") and e.media_content:
                 image = e.media_content[0].get("url", "")

                elif hasattr(e, "media_thumbnail") and e.media_thumbnail:
                 image = e.media_thumbnail[0].get("url", "")

                elif hasattr(e, "links"):
                 for l in e.links:
                    if l.get("type", "").startswith("image"):
                     image = l.get("href")
                     break

                content = extract_article(link)

                print("=" * 60)
                print("SOURCE:", source_name)
                print("TITLE:", title)
                print("Summary length:", len(summary))
                print("Content length:", len(content))

                items.append({
                    "title": title,
                    "summary": summary,
                    "content": content,
                    "link": link,
                    "image": image,
                    "source": source_name,
                    "category": category,
                    "priority": priority
                })

        except Exception as ex:
            print("Feed Error:", ex)

    return items
