"""Async pubsub implementation."""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Callable, Generic, TypeVar

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

__all__ = ["Channel"]


class Channel(Generic[T]):
    """A channel to which you can subscribe."""

    _last: T

    def __init__(self, name: str = "a channel"):
        self.subscriptions: set[Subscription] = set()
        self.name = name

    def publish(self, message: T):
        """Publish a message on this channel."""
        self._last = message
        for subscription in self.subscriptions:
            subscription.queue.put_nowait(message)

    def get_latest(self) -> T:
        """Return the last message that was put in the queue."""
        return self._last

    def get_subscription(self) -> Subscription[T]:
        """Return a subscription object."""
        subscription = Subscription[T](self)
        LOGGER.debug(
            "Subscribing to %s. Total subscribers: %s",
            self.name,
            len(self.subscriptions),
        )
        return subscription

    def subscribe(self, callback: Callable[[T], None]) -> Subscription:
        """Subscribe to this channel"""
        subscription = Subscription[T](self, callback)
        return subscription


class Subscription(Generic[T]):
    """Subscription class.
    Used to subscribe to a Channel."""

    def __init__(self, channel: Channel, callback: None | Callable[[T], None] = None):
        """Create a subscription object belonging to a channel.

        If a callback is provided it will automatically be added as a task to be run when a message
        is received.
        """
        self._channel = channel
        self._channel.subscriptions.add(self)
        self.queue: asyncio.Queue = asyncio.Queue()
        self._callback = callback
        LOGGER.debug(
            "Subscription: %s, total subscriptions %i",
            self._channel.name,
            len(self._channel.subscriptions),
        )
        self.callback_task: asyncio.Task | None = None
        if callback:
            self.callback_task = asyncio.create_task(self._subscribe(callback))

    def unsubscribe(self):
        """Unsubscribe the subscription."""
        if self.callback_task is not None:
            self.callback_task.cancel()
        self._remove_subscription()

    async def _get_message(self) -> T:
        msg = await self.queue.get()
        self.queue.task_done()
        return msg

    async def _subscribe(self, callback: Callable[[T], None]):
        try:
            while True:
                callback(await self._get_message())
        except asyncio.CancelledError:
            LOGGER.debug("Shutting down callback listener.")
        except Exception as err:
            LOGGER.exception(err)

    def _remove_subscription(self):
        if self in self._channel.subscriptions:
            self._channel.subscriptions.remove(self)
        LOGGER.debug(
            "Un-subscribing from channel: %s, subscriber count: %s",
            self._channel.name,
            len(self._channel.subscriptions),
        )

    def __enter__(self):
        return self.queue

    def __exit__(self, _type, value, traceback):
        self._remove_subscription()


async def reader(name, hub):
    """An example reader"""
    msg = ""
    with Subscription(hub) as queue:
        while msg != "SHUTDOWN":
            msg = await queue.get()
            print(f"Reader {name} got message: {msg}")

            if random.random() < 0.1:
                print(f"Reader {name} has read enough")
                break

    print(f"Reader {name} is shutting down")
