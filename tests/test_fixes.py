"""
두 버그 수정 검증 테스트:
1. news() — try 블록 밖 data 참조 버그
2. watchlist_manager — 절대경로 변환
"""
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── watchlist_manager 경로 테스트 ─────────────────────────────────────────────

def test_watchlist_file_is_absolute():
    from watchlist_manager import WATCHLIST_FILE
    assert Path(WATCHLIST_FILE).is_absolute()


def test_watchlist_file_points_to_project_dir():
    from watchlist_manager import WATCHLIST_FILE
    assert Path(WATCHLIST_FILE).parent == Path(__file__).parent.parent


def test_get_tickers_returns_empty_for_unknown_user(tmp_path):
    from watchlist_manager import get_tickers
    wf = tmp_path / "user_watchlist.json"
    wf.write_text(json.dumps({"9999": ["AAPL"]}))
    with patch("watchlist_manager.WATCHLIST_FILE", wf):
        assert get_tickers(1234) == []


def test_get_tickers_returns_list_for_known_user(tmp_path):
    from watchlist_manager import get_tickers
    wf = tmp_path / "user_watchlist.json"
    wf.write_text(json.dumps({"7952029488": ["SOXL", "TQQQ"]}))
    with patch("watchlist_manager.WATCHLIST_FILE", wf):
        assert get_tickers(7952029488) == ["SOXL", "TQQQ"]


# ── news() 버그 수정 테스트 ───────────────────────────────────────────────────

def _make_update(user_id: int = 7952029488):
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.reply_text = AsyncMock()
    return update


def _make_context():
    return MagicMock()


@pytest.mark.asyncio
async def test_news_first_ticker_exception_still_sends_response():
    """첫 번째 ticker(SOXL)가 예외 발생해도 나머지 종목 포함해 응답이 와야 함."""
    from bot import news

    update = _make_update()
    context = _make_context()

    with patch("bot.get_tickers", return_value=["SOXL", "TQQQ"]):
        with patch("bot.get_stock_news", side_effect=[
            RuntimeError("network error"),          # SOXL 실패
            {"change": "+1.00%", "news": ["TQQQ 뉴스"]},  # TQQQ 성공
        ]):
            await news(update, context)

    update.message.reply_text.assert_called_once()
    sent = update.message.reply_text.call_args[0][0]
    assert "SOXL" in sent
    assert "정보 없음" in sent
    assert "뉴스 수집 실패" in sent
    assert "TQQQ" in sent
    assert "TQQQ 뉴스" in sent


@pytest.mark.asyncio
async def test_news_all_succeed():
    """모든 종목 정상 응답."""
    from bot import news

    update = _make_update()
    context = _make_context()

    with patch("bot.get_tickers", return_value=["SOXL", "SPY"]):
        with patch("bot.get_stock_news", side_effect=[
            {"change": "+7.56%", "news": ["SOXL 뉴스"]},
            {"change": "+0.12%", "news": ["SPY 뉴스"]},
        ]):
            await news(update, context)

    sent = update.message.reply_text.call_args[0][0]
    assert "SOXL (+7.56%)" in sent
    assert "SPY (+0.12%)" in sent


@pytest.mark.asyncio
async def test_news_all_tickers_fail_still_responds():
    """모든 종목 예외가 나도 응답은 와야 함."""
    from bot import news

    update = _make_update()
    context = _make_context()

    with patch("bot.get_tickers", return_value=["SOXL"]):
        with patch("bot.get_stock_news", side_effect=RuntimeError("timeout")):
            await news(update, context)

    update.message.reply_text.assert_called_once()
    sent = update.message.reply_text.call_args[0][0]
    assert "SOXL" in sent
    assert "정보 없음" in sent


@pytest.mark.asyncio
async def test_news_no_tickers():
    """관심종목 없으면 안내 메시지."""
    from bot import news

    update = _make_update()
    context = _make_context()

    with patch("bot.get_tickers", return_value=[]):
        await news(update, context)

    update.message.reply_text.assert_called_once_with("관심종목이 없습니다.")
