import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from briefing import generate_briefing

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

MAX_TELEGRAM_LENGTH = 4000


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 *Bonjour ! Je suis votre assistant actualités Burkina & Monde.*\n\n"
        "📰 *Commandes disponibles :*\n"
        "• /briefing — Synthèse des dernières actualités\n"
        "• /aide — Aide\n\n"
        "_Données en temps réel · Focus Burkina Faso & Sahel_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⏳ Analyse des dernières actualités en cours...")
    try:
        synthesis = generate_briefing()
        # Découper si le message dépasse la limite Telegram
        for i in range(0, len(synthesis), MAX_TELEGRAM_LENGTH):
            chunk = synthesis[i : i + MAX_TELEGRAM_LENGTH]
            await update.message.reply_text(chunk, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Erreur briefing: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Une erreur est survenue. Réessayez dans quelques minutes."
        )


async def aide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "ℹ️ *AIDE*\n\n"
        "Ce bot analyse en temps réel les actualités mondiales\n"
        "et produit une synthèse avec focus *Burkina Faso*.\n\n"
        "*Sources :* RFI, BBC Afrique, Jeune Afrique, Le Monde, Al Jazeera\n\n"
        "• /briefing — Obtenir la synthèse maintenant\n"
        "• /start — Message de bienvenue"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


def main() -> None:
    token = os.environ["TELEGRAM_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("briefing", briefing_command))
    app.add_handler(CommandHandler("aide", aide))
    print("✅ Bot démarré. En attente de messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
