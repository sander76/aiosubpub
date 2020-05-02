"""Async pubsub implementation."""

import asyncio
import logging
import random
from asyncio import CancelledError

__version__ = "1.0.4"

LOGGER = logging.getLogger(__name__)


class Channel:
    """A channel to which you can subscribe."""

    def __init__(self, name="a channel"):
        self.subscriptions = set()
        self.name = name

    def publish(self, message):
        """Publish a message on this channel."""
        for queue in self.subscriptions:
            queue.put_nowait(message)

    def get_subscription(self):
        """Return a subscription object.

        Used internally but also useful to create custom subscriber methods.
        """
        subscription = Subscription(self)
        self.subscriptions.add(subscription.queue)
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

    def __init__(self, hub):
        self.hub = hub
        self.queue = asyncio.Queue()
        self.task = None

    def cancel(self):
        """Cancel the subscription. The same as unsubscribe"""
        self.unsubscribe()

    def unsubscribe(self):
        """Unsubscribe the subscription."""
        self.task.cancel()
        self._remove_subscription()

    def _remove_subscription(self):
        if self.queue in self.hub.subscriptions:
            self.hub.subscriptions.remove(self.queue)

    def __enter__(self):
        self.hub.subscriptions.add(self.queue)
        LOGGER.debug(
            "Subscription: %s, total subscriptions %i",
            self.hub.name,
            len(self.hub.subscriptions),
        )
        return self.queue

    def __exit__(self, _type, value, traceback):
        LOGGER.debug("Un-subscribing from channel: %s", self.hub.name)
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
