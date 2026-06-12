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

            try:
                data = get_stock_news(ticker)
                change = data["change"]
                news_list = data["news"]
            except Exception as e:
                change = "정보 없음"
                news_list = [f"뉴스 수집 실패: {e}"]

            message += f"🔥 {ticker} ({change})\n"

            for item in news_list:
                message += f"- {item}\n"

            message += "\n"

        send_message(user_id, message)