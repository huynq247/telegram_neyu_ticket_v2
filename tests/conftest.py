"""
Pytest configuration and fixtures for testing.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database_connection():
    """Create mock database connection for testing"""
    mock_conn = Mock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock()
    mock_conn.fetchrow = AsyncMock()
    mock_conn.fetchval = AsyncMock()
    mock_conn.close = AsyncMock()
    return mock_conn


@pytest.fixture
def mock_telegram_bot():
    """Create mock Telegram bot for testing"""
    bot = Mock()
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    return bot


@pytest.fixture
def mock_telegram_update():
    """Create mock Telegram update for testing"""
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 12345
    update.effective_chat = Mock()
    update.effective_chat.id = 12345
    update.message = Mock()
    update.message.text = "test message"
    return update


@pytest.fixture
def mock_telegram_context():
    """Create mock Telegram context for testing"""
    context = Mock()
    context.bot = Mock()
    context.bot.send_message = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    return context


@pytest.fixture(autouse=True)
async def cleanup_async_resources():
    """Cleanup async resources after each test"""
    yield
    # Close any remaining async resources
    tasks = [task for task in asyncio.all_tasks() if not task.done()]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)