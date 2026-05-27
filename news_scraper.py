import requests
import feedparser
import yfinance as yf

from deep_translator import GoogleTranslator


def get_stock_news(ticker):

    # -----------------------------
    # 1. 주가 정보 가져오기
    # -----------------------------

    stock = yf.Ticker(ticker)

    hist = stock.history(period="2d")

    if len(hist) < 2:
        change_text = "변동률 계산 실패"

    else:
        close_yesterday = hist["Close"].iloc[-2]
        close_today = hist["Close"].iloc[-1]

        change_percent = (
            (close_today - close_yesterday)
            / close_yesterday
        ) * 100

        change_text = f"{change_percent:+.2f}%"

    # -----------------------------
    # 2. 최근 1일 뉴스만 수집
    # -----------------------------

    query = (
        f"{ticker} stock "
        f"(site:cnbc.com OR "
        f"site:reuters.com OR "
        f"site:finance.yahoo.com OR "
        f"site:marketwatch.com) "
        f"when:1d"
    )

    url = (
            "https://news.google.com/rss/search?q="
            + query
    )

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {
            "change": change_text,
            "news": [f"{ticker} 뉴스 요청 실패"]
        }

    feed = feedparser.parse(response.text)

    news_list = []

    # 최근 뉴스 3개만
    for entry in feed.entries[:3]:

        title = entry.title
        link = entry.link
        try:
            translated = GoogleTranslator(
                source='auto',
                target='ko'
            ).translate(title)

        except:
            translated = title

        news_list.append(
            f"{translated}\n{link}"
        )

    if not news_list:
        news_list = [f"{ticker} 최신 뉴스 없음"]

    return {
        "change": change_text,
        "news": news_list
    }