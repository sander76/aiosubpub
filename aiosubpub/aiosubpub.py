"""Async pubsub implementation."""

import asyncio
import logging
import random
from asyncio import CancelledError
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)


class Channel:
    """A channel to which you can subscribe."""

    def __init__(self, name: str = "a channel"):
        self.subscriptions: set = set()
        self.name = name
        self._last = None

    def publish(self, message: Any):
        """Publish a message on this channel."""
        self._last = message
        for queue in self.subscriptions:
            queue.put_nowait(message)

    def get_latest(self):
        """Return the last message that was put in the queue."""
        return self._last

    def get_subscription(self) -> "Subscription":
        """Return a subscription object.

        Used internally but also useful to create custom subscriber methods.
        """
        subscription = Subscription(self)
        self.subscriptions.add(subscription.queue)
        LOGGER.debug(
            "Subscribing to %s. Total subscribers: %s",
            self.name,
            len(self.subscriptions),
        )
        return subscription

    def subscribe(self, callback) -> "Subscription":
        """Subscribe to this channel"""
        _loop = asyncio.get_running_loop()
        subscription = self.get_subscription()
        subscription.task = _loop.create_task(self._subscribe(subscription, callback))
        return subscription

    async def _subscribe(self, subscription: "Subscription", callback):
        try:
            with subscription as queue:
                while True:
                    msg = await queue.get()
                    callback(msg)
                    queue.task_done()
        except CancelledError:
            LOGGER.debug("Shutting down subscriber")


class Subscription:
    """Subscription class.
    Used to subscribe to a Channel."""

    def __init__(self, hub: "Channel"):
        self.hub = hub
        self.queue = asyncio.Queue()
        self.task: Optional[asyncio.Task] = None

    def cancel(self):
        """Cancel the subscription. The same as unsubscribe"""
        self.unsubscribe()

    def unsubscribe(self):
        """Unsubscribe the subscription."""
        if self.task is not None:
            self.task.cancel()
        self._remove_subscription()

    def _remove_subscription(self):
        if self.queue in self.hub.subscriptions:
            self.hub.subscriptions.remove(self.queue)
        LOGGER.debug(
            "Un-subscribing from channel: %s, subscriber count: %s",
            self.hub.name,
            len(self.hub.subscriptions),
        )

    def __enter__(self):
        self.hub.subscriptions.add(self.queue)
        LOGGER.debug(
            "Subscription: %s, total subscriptions %i",
            self.hub.name,
            len(self.hub.subscriptions),
        )
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
