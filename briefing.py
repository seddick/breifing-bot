import os
import feedparser
import anthropic
from datetime import datetime

# Flux RSS - Sources d'actualités africaines et mondiales
RSS_FEEDS = [
    ("RFI Afrique",        "https://www.rfi.fr/fr/rss-afrique.xml"),
    ("RFI Monde",          "https://www.rfi.fr/fr/rss-monde.xml"),
    ("BBC Afrique",        "https://feeds.bbci.co.uk/afrique/rss.xml"),
    ("Jeune Afrique",      "https://www.jeuneafrique.com/feed/"),
    ("Le Monde Afrique",   "https://www.lemonde.fr/afrique/rss_full.xml"),
    ("Al Jazeera",         "https://www.aljazeera.com/xml/rss/all.xml"),
    ("Reuters",        "https://feeds.reuters.com/Reuters/worldNews"),
    ("AP News",        "https://apnews.com/rss/apf-topnews"),
    ("BBC News",        "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera English",        "https://www.aljazeera.com/xml/rss/all.xml"),
    ("Deutsche Welle",        "https://rss.dw.com/xml/rss-en-all"),
    ("France 24",        "https://www.france24.com/en/rss"),
    ("The Guardian",        "https://www.theguardian.com/world/rss"),
    ("Financial Times",        "https://ft.com/?format=rss"),
    ("The New York Times",        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("The Hindu",        "https://thehindu.com/feeder/default.rss"),
    ("The Indian Express",        "https://indianexpress.com/feed/"),
    ("CNA",        "https://www.channelnewsasia.com/api/v1/rss-outbound-feed"),
    ("South China Morning Post",        "https://www.scmp.com/rss/feed"),
    ("China Daily",        "https://www.chinadaily.com.cn/rss/world_rss.xml"),
    ("The Moscow Times",        "https://www.themoscowtimes.com/rss"),
    ("The Rio Times",        "https://riotimesonline.com/feed/"),
    ("Mail & Guardian",        "https://mg.co.za/feed/"),
    ("Gulf News",        "https://gulfnews.com/arc/outboundfeeds/rss/?outputType=xml"),
    ("Ahram Online",        "https://english.ahram.org.eg/RSS.aspx"),
    ("Tehran Times",        "https://www.tehrantimes.com/rss"),
    ("InfoBrics",        "https://infobrics.org/feed/"),
    ("Foreign Affairs",        "https://www.foreignaffairs.com/rss.xml"),
    ("World Politics Review",        "https://www.worldpoliticsreview.com/feed/"),
    ("The Diplomat",        "https://thediplomat.com/feed/"),
    ("Chatham House",        "https://www.chathamhouse.org/feed/")
]

BRIEFING_PROMPT = """\
Tu es un analyste géopolitique expert en Afrique de l'Ouest et au Sahel.

Voici les dernières actualités du {date} :

{articles}

---
Produis une synthèse structurée en français. Utilise le format Markdown compatible Telegram (gras avec *texte*, pas de #).

*🌍 MONDE*
Points clés pouvant impacter l'Afrique (5-10 bullets)

*🌍 AFRIQUE & SAHEL*
Développements régionaux importants (5-10 bullets)

*🇧🇫 BURKINA FASO & ALLIANCE AES*
Impact direct ou indirect sur le Burkina, relations avec Russie/Chine/partenaires (4-8 bullets)

*📊 ÉCONOMIE & HUMANITAIRE*
Matières premières, aide internationale, crise humanitaire (5-10 bullets)

*⚡ POINT CLÉ DU MOMENT*
En 2-3 phrases : le fait le plus important à surveiller pour le Burkina Faso.

Règles : factuel, neutre, concis. Chaque bullet = max 2 lignes.\
"""


def fetch_news(max_per_feed: int = 5) -> list[dict]:
    articles = []
    for source, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                # Nettoyer le résumé HTML basique
                summary = summary.replace("<p>", "").replace("</p>", " ")
                summary = summary[:250]
                if title:
                    articles.append({
                        "source": source,
                        "title": title,
                        "summary": summary,
                    })
        except Exception as e:
            print(f"[WARN] Erreur flux {source}: {e}")
    return articles


def generate_briefing() -> str:
    articles = fetch_news()
    if not articles:
        return "❌ Impossible de récupérer les actualités pour le moment. Réessayez dans quelques minutes."

    news_text = "\n\n".join(
        f"[{a['source']}] {a['title']}\n{a['summary']}"
        for a in articles
    )

    date_str = datetime.now().strftime("%d/%m/%Y à %Hh%M")
    prompt = BRIEFING_PROMPT.format(date=date_str, articles=news_text)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text
