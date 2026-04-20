"""
Scraping des réseaux sociaux burkinabè via Apify.
Apify fournit des actors officiels pour Facebook, TikTok et Instagram.
Compte gratuit : https://apify.com (5$/mois de crédit offert)
"""
import os
from apify_client import ApifyClient

# ── Pages Facebook publiques burkinabè à surveiller ───────────────────────
FACEBOOK_PAGES = [
    "burkina24",
    "lefasonet",
    "wakatsera.bf",
    "Sidwaya.officiel",
    "LObservateurPaalga",
    "radiooméga.bf",
]

# ── Hashtags TikTok burkinabè ─────────────────────────────────────────────
TIKTOK_HASHTAGS = [
    "burkinafaso",
    "burkina",
    "ouagadougou",
    "fasonews",
    "actualiteburkina",
]

# ── Hashtags Instagram burkinabè ──────────────────────────────────────────
INSTAGRAM_HASHTAGS = [
    "burkinafaso",
    "burkina",
    "ouagadougou",
    "burkinabe",
]


def _get_client() -> ApifyClient:
    token = os.environ.get("APIFY_API_TOKEN", "")
    if not token:
        raise EnvironmentError("Variable APIFY_API_TOKEN manquante dans .env")
    return ApifyClient(token)


def fetch_facebook(max_posts: int = 10) -> list[dict]:
    """Récupère les derniers posts des pages Facebook burkinabè."""
    client = _get_client()
    posts = []
    try:
        run = client.actor("apify/facebook-posts-scraper").call(
            run_input={
                "startUrls": [
                    {"url": f"https://www.facebook.com/{page}"}
                    for page in FACEBOOK_PAGES
                ],
                "maxPosts": max_posts,
                "maxPostComments": 0,
                "maxReviewComments": 0,
                "scrapeAbout": False,
                "scrapeReviews": False,
            }
        )
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            text = (item.get("text") or "").strip()[:300]
            if text:
                posts.append({
                    "reseau": "Facebook",
                    "source": item.get("pageName", "Page BF"),
                    "texte": text,
                    "likes": item.get("likes", 0),
                    "shares": item.get("shares", 0),
                    "comments": item.get("comments", 0),
                })
    except Exception as e:
        print(f"[WARN] Facebook scraping: {e}")
    return posts


def fetch_tiktok(max_per_hashtag: int = 5) -> list[dict]:
    """Récupère les vidéos TikTok tendance sur les hashtags burkinabè."""
    client = _get_client()
    videos = []
    try:
        run = client.actor("clockworks/free-tiktok-scraper").call(
            run_input={
                "hashtags": TIKTOK_HASHTAGS,
                "resultsPerPage": max_per_hashtag,
                "shouldDownloadVideos": False,
                "shouldDownloadCovers": False,
            }
        )
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            desc = (item.get("text") or "").strip()[:250]
            if desc:
                videos.append({
                    "reseau": "TikTok",
                    "source": f"@{item.get('authorMeta', {}).get('name', 'inconnu')}",
                    "texte": desc,
                    "likes": item.get("diggCount", 0),
                    "shares": item.get("shareCount", 0),
                    "comments": item.get("commentCount", 0),
                    "vues": item.get("playCount", 0),
                })
    except Exception as e:
        print(f"[WARN] TikTok scraping: {e}")
    return videos


def fetch_instagram(max_per_hashtag: int = 5) -> list[dict]:
    """Récupère les posts Instagram sur les hashtags burkinabè."""
    client = _get_client()
    posts = []
    try:
        run = client.actor("apify/instagram-hashtag-scraper").call(
            run_input={
                "hashtags": INSTAGRAM_HASHTAGS,
                "resultsLimit": max_per_hashtag,
            }
        )
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            caption = (item.get("caption") or "").strip()[:250]
            if caption:
                posts.append({
                    "reseau": "Instagram",
                    "source": f"@{item.get('ownerUsername', 'inconnu')}",
                    "texte": caption,
                    "likes": item.get("likesCount", 0),
                    "shares": 0,
                    "comments": item.get("commentsCount", 0),
                })
    except Exception as e:
        print(f"[WARN] Instagram scraping: {e}")
    return posts


def fetch_all_social() -> list[dict]:
    """Agrège tous les réseaux et trie par engagement."""
    all_posts = []
    all_posts += fetch_facebook()
    all_posts += fetch_tiktok()
    all_posts += fetch_instagram()

    # Trier par engagement total (likes + shares + comments)
    all_posts.sort(
        key=lambda p: p.get("likes", 0) + p.get("shares", 0) * 2 + p.get("comments", 0),
        reverse=True,
    )
    return all_posts[:20]  # Top 20 posts les plus engagés
