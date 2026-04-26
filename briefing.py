import os
import feedparser
import anthropic
from datetime import datetime
from social_media import fetch_all_social

# ── Médias internationaux ──────────────────────────────────────────────────
INTERNATIONAL_FEEDS = [
    ("RFI Afrique",       "https://www.rfi.fr/fr/rss-afrique.xml"),
    ("RFI Monde",         "https://www.rfi.fr/fr/rss-monde.xml"),
    ("BBC Afrique",       "https://feeds.bbci.co.uk/afrique/rss.xml"),
    ("Jeune Afrique",     "https://www.jeuneafrique.com/feed/"),
    ("Le Monde Afrique",  "https://www.lemonde.fr/afrique/rss_full.xml"),
    ("Al Jazeera",        "https://www.aljazeera.com/xml/rss/all.xml"),
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

# ── Médias burkinabè (ce que les gens lisent et partagent) ─────────────────
BURKINA_FEEDS = [
    ("Burkina24",         "https://burkina24.com/feed/"),
    ("Lefaso.net",        "https://lefaso.net/spip.php?page=backend"),
    ("FasoZine",          "https://fasozine.com/feed/"),
    ("Wakat Sera",        "https://www.wakatsera.com/feed/"),
    ("L'Evénement",       "https://levenementbf.com/feed/"),
]

BRIEFING_PROMPT = """\
Tu es un analyste géopolitique expert en Afrique de l'Ouest, au Sahel et spécialiste des dynamiques sociales et politiques burkinabè. Ajoute un lien vérifiable à toutes tes informations. Cite uniquement les sources vérifiables. N'hallucine jamais.

Voici les dernières actualités du {date} :

== MÉDIAS INTERNATIONAUX ==
{articles_intl}

== MÉDIAS BURKINABÈ (presse locale) ==
{articles_bf}

== RÉSEAUX SOCIAUX BURKINA (posts réels Facebook/TikTok/Instagram) ==
{social_posts}

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

*📱 RÉSEAUX SOCIAUX BURKINA (Facebook · TikTok · Instagram)*
Sur la base des posts réels scannés sur ces plateformes :
• Sujets qui font le buzz / la polémique (2-3 bullets)
• Contenus les plus viraux ou partagés (1-2 bullets)
• Ton général : optimiste / tendu / critique / neutre ?
• 1 citation ou extrait marquant si disponible

*⚡ POINT CLÉ DU MOMENT*
En 2-3 phrases : le fait le plus important à surveiller pour le Burkina Faso.

Règles : factuel, neutre, concis. Chaque bullet = max 2 lignes.\
"""


def _parse_feed(feeds: list[tuple], max_per_feed: int) -> list[dict]:
    articles = []
    for source, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                summary = summary.replace("<p>", "").replace("</p>", " ")
                summary = summary[:250]
                if title:
                    articles.append({"source": source, "title": title, "summary": summary})
        except Exception as e:
            print(f"[WARN] Erreur flux {source}: {e}")
    return articles


def fetch_news(max_per_feed: int = 5) -> tuple[list[dict], list[dict]]:
    intl = _parse_feed(INTERNATIONAL_FEEDS, max_per_feed)
    bf   = _parse_feed(BURKINA_FEEDS, max_per_feed)
    return intl, bf


def _format(articles: list[dict]) -> str:
    if not articles:
        return "(aucune donnée disponible)"
    return "\n\n".join(
        f"[{a['source']}] {a['title']}\n{a['summary']}"
        for a in articles
    )


def _format_social(posts: list[dict]) -> str:
    if not posts:
        return "(aucune donnée disponible)"
    lines = []
    for p in posts:
        engagement = p.get("likes", 0) + p.get("shares", 0) * 2 + p.get("comments", 0)
        vues = f" · {p['vues']:,} vues" if p.get("vues") else ""
        lines.append(
            f"[{p['reseau']}] {p['source']} (❤️{p['likes']} 🔁{p['shares']} 💬{p['comments']}{vues})\n{p['texte']}"
        )
    return "\n\n".join(lines)


def generate_briefing() -> str:
    intl, bf = fetch_news()
    social = fetch_all_social()

    if not intl and not bf and not social:
        return "❌ Impossible de récupérer les actualités pour le moment. Réessayez dans quelques minutes."

    date_str = datetime.now().strftime("%d/%m/%Y à %Hh%M")
    prompt = BRIEFING_PROMPT.format(
        date=date_str,
        articles_intl=_format(intl),
        articles_bf=_format(bf),
        social_posts=_format_social(social),
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text
