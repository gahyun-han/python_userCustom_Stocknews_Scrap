from watchlist_manager import load_watchlists
from news_scraper import get_stock_news
from telegram_sender import send_message


def send_daily_news():
    watchlists = load_watchlists()

    for user_id, tickers in watchlists.items():

        if not tickers:
            continue

        message = "📈 오늘의 관심종목 뉴스\n\n"

        for ticker in tickers:

            news_list = get_stock_news(ticker)

            message += f"🔥 {ticker}\n"

            for news in news_list:
                message += f"- {news}\n"

            message += "\n"

        send_message(user_id, message)