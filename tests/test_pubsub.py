import asyncio
import logging
from unittest.mock import Mock

import pytest

from aiosubpub import Channel

_LOGGER = logging.getLogger(__name__)


@pytest.fixture
def dummy_message():
    return "a dummy message"


class MockedCallback:
    def __init__(self):
        self.mock = Mock()

    def __call__(self, *args, **kwargs):
        self.mock(*args, **kwargs)


@pytest.fixture
def mock_callback():
    return MockedCallback()


@pytest.mark.asyncio
async def test_pubsub_callback_success(dummy_message):
    dummy_channel = Channel("dummy channel")
    mock_callback = Mock()
    subscription = dummy_channel.subscribe(mock_callback)

    dummy_channel.publish(dummy_message)
    await asyncio.sleep(0.1)
    mock_callback.assert_called_once_with(dummy_message)
    subscription.unsubscribe()


@pytest.mark.asyncio
async def test_channel_list(mock_callback: MockedCallback):
    """Assert the subscription list is empty when starting a channel"""
    dummy_channel: Channel = Channel("dummy channel")
    assert len(dummy_channel.subscriptions) == 0


@pytest.mark.asyncio
async def test_channel_subscriptions(mock_callback):
    dummy_channel = Channel("dummy channel")

    sub1 = dummy_channel.subscribe(mock_callback)
    sub2 = dummy_channel.subscribe(mock_callback)

    assert len(dummy_channel.subscriptions) == 2

    sub1.unsubscribe()
    sub2.unsubscribe()


@pytest.mark.asyncio
async def test_channel_unsubscribe_no_watch(mock_callback):
    """Test subscription after unsubscribe.

    This test cancels the subscription before the watching starts.
    """
    dummy_channel = Channel("dummy channel")
    subscription = dummy_channel.subscribe(mock_callback)
    assert len(dummy_channel.subscriptions) == 1

    subscription.unsubscribe()
    await asyncio.sleep(0.1)
    assert len(dummy_channel.subscriptions) == 0


@pytest.mark.asyncio
async def test_channel_unsubscribe_watch(mock_callback):
    """Test subscription after unsubscribe."""

    dummy_channel = Channel("dummy channel")
    subscription_task = dummy_channel.subscribe(mock_callback)
    assert len(dummy_channel.subscriptions) == 1

    await asyncio.sleep(0.1)
    subscription_task.unsubscribe()
    await asyncio.sleep(0.1)
    assert len(dummy_channel.subscriptions) == 0


@pytest.mark.asyncio
async def test_custom_subscription(dummy_message):
    """Test a custom subscription"""

    channel = Channel("dummy channel")

    subscription = channel.get_subscription()

    async def _custom_subscriber():
        with subscription as sub:
            result = await sub.get()
            return result

    channel.publish(dummy_message)

    result = await _custom_subscriber()
    assert result == dummy_message


@pytest.mark.asyncio
async def test_get_latest(dummy_message):
    channel = Channel("dummy channel")
    channel.publish(dummy_message)

    latest = channel.get_latest()

    assert latest == dummy_message
