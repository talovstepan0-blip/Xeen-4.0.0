# Файл: plugins/news.py
"""
Плагин новостей - RSS ленты (Habr, 3DNews, BBC)
"""

import feedparser

RSS_FEEDS = {
    "habr": "https://habr.com/ru/rss/",
    "3dnews": "http://www.3dnews.ru/news/feed",
    "bbc": "http://feeds.bbci.co.uk/news/rss.xml"
}


def execute(params: dict) -> dict:
    """Получить новости из указанного источника"""
    source = params.get("source", "habr")
    limit = params.get("limit", 5)
    
    feed_url = RSS_FEEDS.get(source, RSS_FEEDS["habr"])
    
    try:
        feed = feedparser.parse(feed_url)
        entries = feed.entries[:limit]
        
        news = [
            {
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", "")
            }
            for entry in entries
        ]
        
        return {"status": "success", "source": source, "news": news}
    except Exception as e:
        return {"status": "error", "message": str(e)}
