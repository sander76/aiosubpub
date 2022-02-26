[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![CI](https://github.com/sander76/mspyteams/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/sander76/pypubsub/branch/master/graph/badge.svg)](https://codecov.io/gh/sander76/pypubsub)


# AioSubPub

Async pub sub implementation.

Inspired by someone else whose name I cannot find anymore. If you see your code (I did some improvements on it I think) please let me know and I am happy to give you credit.

## Installation

`pip install aiosubpub`

## Usage

```python
import aiosubpub
import asyncio
loop=asyncio.get_event_loop()

# create a channel
a_channel = aiosubpub.Channel()

# subscribe to the channel using a callback.
def call_back(data):
    print(data)

subscription = loop.create_task(a_channel.subscribe(call_back))

# Publish a message.
a_channel.publish("a message")

subscription.un_subscribe()


# Without callback:

subscription = a_channel.get_subscription()

async def _custom_subscriber():
    with subscription as sub:
        result = await sub.get()
        print(result)

a_channel.publish("a message")

result = await _custom_subscriber()
```

## changelog

### 1.0.10
- Add `get_latest` to the channel.
