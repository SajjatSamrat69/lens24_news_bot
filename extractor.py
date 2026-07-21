import feedparser
from newspaper import Article

def extract_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text.strip()

        if len(text) < 100:
            return ""

        return text[:2500]

    except Exception as e:
        print("Newspaper Error:", e)
        return ""


def fetch_news(feeds):

    items = []

    for url in feeds:

        try:
            feed = feedparser.parse(url)

            source = feed.feed.get("title", "Unknown Source")

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

                content = extract_article(link)

                print("=" * 60)
                print("SOURCE:", source)
                print("TITLE:", title)
                print("Summary length:", len(summary))
                print("Content length:", len(content))

                items.append({
                    "title": title,
                    "summary": summary,
                    "content": content,
                    "link": link,
                    "image": image,
                    "source": source
                })

        except Exception as ex:
            print("Feed Error:", ex)

    return items
