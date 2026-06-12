"""
버그 수정 검증 테스트:
1. news() — try 블록 밖 data 참조 버그
2. watchlist_manager — 절대경로 변환
3. scheduler — dict 반환값을 list로 쓰던 버그 + 예외 처리 누락
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


# ── bot.py news() 테스트 ──────────────────────────────────────────────────────

def _make_update(user_id: int = 7952029488):
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.reply_text = AsyncMock()
    return update


@pytest.mark.asyncio
async def test_news_first_ticker_exception_still_sends_response():
    """첫 번째 ticker(SOXL)가 예외 발생해도 나머지 종목 포함해 응답이 와야 함."""
    from bot import news
    update = _make_update()
    with patch("bot.get_tickers", return_value=["SOXL", "TQQQ"]):
        with patch("bot.get_stock_news", side_effect=[
            RuntimeError("network error"),
            {"change": "+1.00%", "news": ["TQQQ 뉴스"]},
        ]):
            await news(update, MagicMock())
    sent = update.message.reply_text.call_args[0][0]
    assert "SOXL" in sent
    assert "정보 없음" in sent
    assert "TQQQ" in sent
    assert "TQQQ 뉴스" in sent


@pytest.mark.asyncio
async def test_news_all_succeed():
    from bot import news
    update = _make_update()
    with patch("bot.get_tickers", return_value=["SOXL", "SPY"]):
        with patch("bot.get_stock_news", side_effect=[
            {"change": "+7.56%", "news": ["SOXL 뉴스"]},
            {"change": "+0.12%", "news": ["SPY 뉴스"]},
        ]):
            await news(update, MagicMock())
    sent = update.message.reply_text.call_args[0][0]
    assert "SOXL (+7.56%)" in sent
    assert "SPY (+0.12%)" in sent


@pytest.mark.asyncio
async def test_news_no_tickers():
    from bot import news
    update = _make_update()
    with patch("bot.get_tickers", return_value=[]):
        await news(update, MagicMock())
    update.message.reply_text.assert_called_once_with("관심종목이 없습니다.")


# ── scheduler.py send_daily_news() 테스트 ─────────────────────────────────────

def test_scheduler_uses_dict_change_and_news(tmp_path):
    """scheduler가 get_stock_news 반환 dict에서 change, news를 올바르게 꺼내야 함."""
    from scheduler import send_daily_news
    wf = tmp_path / "user_watchlist.json"
    wf.write_text(json.dumps({"111": ["SOXL", "TQQQ"]}))
    sent_messages = []

    with patch("watchlist_manager.WATCHLIST_FILE", wf):
        with patch("scheduler.get_stock_news", side_effect=[
            {"change": "+5.00%", "news": ["SOXL 뉴스A"]},
            {"change": "+1.00%", "news": ["TQQQ 뉴스B"]},
        ]):
            with patch("scheduler.send_message", side_effect=lambda uid, msg: sent_messages.append(msg)):
                send_daily_news()

    assert len(sent_messages) == 1
    msg = sent_messages[0]
    assert "SOXL (+5.00%)" in msg
    assert "SOXL 뉴스A" in msg
    assert "TQQQ (+1.00%)" in msg
    assert "TQQQ 뉴스B" in msg
    # 예전 버그: dict key("change","news")가 그대로 출력되지 않아야 함
    assert "- change\n" not in msg
    assert "- news\n" not in msg


def test_scheduler_first_ticker_exception_continues(tmp_path):
    """SOXL 예외 발생해도 TQQQ 포함해 메시지 전송."""
    from scheduler import send_daily_news
    wf = tmp_path / "user_watchlist.json"
    wf.write_text(json.dumps({"111": ["SOXL", "TQQQ"]}))
    sent_messages = []

    with patch("watchlist_manager.WATCHLIST_FILE", wf):
        with patch("scheduler.get_stock_news", side_effect=[
            RuntimeError("timeout"),
            {"change": "+1.00%", "news": ["TQQQ 뉴스"]},
        ]):
            with patch("scheduler.send_message", side_effect=lambda uid, msg: sent_messages.append(msg)):
                send_daily_news()

    assert len(sent_messages) == 1
    msg = sent_messages[0]
    assert "SOXL" in msg
    assert "정보 없음" in msg
    assert "TQQQ" in msg


def test_scheduler_empty_watchlist_sends_nothing(tmp_path):
    from scheduler import send_daily_news
    wf = tmp_path / "user_watchlist.json"
    wf.write_text(json.dumps({"111": []}))
    with patch("watchlist_manager.WATCHLIST_FILE", wf):
        with patch("scheduler.send_message") as mock_send:
            send_daily_news()
    mock_send.assert_not_called()
