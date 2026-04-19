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
]

BRIEFING_PROMPT = """\
Tu es un analyste géopolitique expert en Afrique de l'Ouest et au Sahel.

Voici les dernières actualités du {date} :

{articles}

---
Produis une synthèse structurée en français. Utilise le format Markdown compatible Telegram (gras avec *texte*, pas de #).

*🌍 MONDE*
Points clés pouvant impacter l'Afrique (3-5 bullets)

*🌍 AFRIQUE & SAHEL*
Développements régionaux importants (3-5 bullets)

*🇧🇫 BURKINA FASO & ALLIANCE AES*
Impact direct ou indirect sur le Burkina, relations avec Russie/Chine/partenaires (2-4 bullets)

*📊 ÉCONOMIE & HUMANITAIRE*
Matières premières, aide internationale, crise humanitaire (2-3 bullets)

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
