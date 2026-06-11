from news_scraper import get_stock_news
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from watchlist_manager import (
    add_ticker,
    remove_ticker,
    get_tickers,
    reset_watchlist,
)

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "주식 뉴스 봇 시작!\n\n"
        "/add TSLA\n"
        "/remove TSLA\n"
        "/list\n"
        "/news\n"
        "/reset"
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("예시: /add TSLA")
        return

    ticker = context.args[0].upper()

    add_ticker(user_id, ticker)

    await update.message.reply_text(f"{ticker} 추가 완료")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        return

    ticker = context.args[0].upper()

    remove_ticker(user_id, ticker)

    await update.message.reply_text(f"{ticker} 삭제 완료")


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    tickers = get_tickers(user_id)

    if not tickers:
        await update.message.reply_text("등록된 종목 없음")
        return

    msg = "\n".join(tickers)

    await update.message.reply_text(f"관심종목:\n{msg}")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    reset_watchlist(user_id)

    await update.message.reply_text("관심종목 초기화 완료")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    tickers = get_tickers(user_id)

    if not tickers:
        await update.message.reply_text("관심종목이 없습니다.")
        return

    message = "📈 오늘의 뉴스\n\n"

    for ticker in tickers:

        try:
            data = get_stock_news(ticker)
            change = data["change"]
            news_list = data["news"]
        except Exception as e:
            change = "정보 없음"
            news_list = [f"뉴스 수집 실패: {e}"]

        message += f"🔥 {ticker} ({change})\n"

        for news in news_list:
            message += f"- {news}\n"

        message += "\n"

    await update.message.reply_text(message)

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("news", news))

    print("Bot Running...")
    app.run_polling()

