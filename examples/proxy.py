import reactivestreams
import websockets
import asyncio
from asyncio.queues import Queue, QueueEmpty
from subscription import Subscription
import time
import re

class PublisherProxy(reactivestreams.Publisher):
    def __init__(self):
        print("PublisherProxy() [construct]")
        self.name = "PublisherProxy"
        self.peer_name = "SubscriberProxy"
        self.request_pattern = re.compile("request:([0-9]+)")
        self.queue = Queue(50)
        self.self_acknowledged = False
        self.peer_acknowledged = False

    def synchronized(self):
        return self.self_acknowledged and self.peer_acknowledged

    async def synchronize(self, delay=1.0):
        print("PublisherProxy.synchronize() [starting]")
        while not self.synchronized():
            print(f"PublisherProxy.synchronize() {time.strftime('%X')} synchronizing...")
            await self.send(f"{self.name}-SYN")
            await asyncio.sleep(delay)
        print(f"PublisherProxy.synchronize() {time.strftime('%X')} synchronized!")
        asyncio.create_task(self.processor())

    async def enqueue(self, item):
        await self.queue.put(item)

    async def dequeue(self):
        return await self.queue.get()

    async def processor(self):
        print("PublisherProxy.processor() [starting]")
        while True:
            item = await self.dequeue()
            self.process(item)

    async def connect(self, endpoint):
        print(f"PublisherProxy.connect() endpoint: {endpoint}")
        self.websocket = await websockets.connect(endpoint)
        self.recv_task = asyncio.create_task(self.recv())
        asyncio.create_task(self.synchronize())

    def attach(self, websocket):
        print(f"PublisherProxy.attach() websocket: {websocket}")
        self.websocket = websocket
        self.recv_task = asyncio.create_task(self.recv())
        asyncio.create_task(self.synchronize())

    async def send(self, message):
        print(f"PublisherProxy.send() message: {message}")
        await self.websocket.send(message)

    async def recv(self):
        print("PublisherProxy.recv() [starting]")
        async for message in self.websocket:
            print(f"PublisherProxy.recv() message: {message}")
            self.process(message)

    def process(self, message):
        print(f"PublisherProxy.process() message: {message}")
        if (type(message) == bytes):
            self.subscriber.onNext(message)
        elif len(message) >= 7 and message[0:7] == "onNext:":
            self.subscriber.onNext(message[7:])
        elif message == "onSubscribe":
            self.subscription = Subscription(self, self.subscriber)
            self.subscriber.onSubscribe(self.subscription)
        elif message == "onComplete":
            self.subscriber.onComplete()
        elif message == "onError":
            self.subscriber.onError()
        elif message == "subscribe":
            asyncio.create_task(self.send(message))
        elif len(message) >= 8 and message[0:8] == "request:":
            asyncio.create_task(self.send(message))
        elif message == f"{self.name}-OK":
            self.peer_acknowledged = True
            asyncio.create_task(self.send(f"{self.name}-ACK"))
        elif message == f"{self.peer_name}-SYN":
            asyncio.create_task(self.send(f"{self.peer_name}-OK"))
        elif message == f"{self.peer_name}-ACK":
            self.self_acknowledged = True
        else:
            print(f"PublisherProxy.process() UNHANDLED message: {message}")

    def subscribe(self, subscriber: reactivestreams.Subscriber):
        print(f"PublisherProxy.subscribe() subscriber: {subscriber}")
        self.subscriber = subscriber
        asyncio.create_task(self.enqueue("subscribe"))

    def request(self, N):
        print(f"PublisherProxy.request() N: {N}")
        asyncio.create_task(self.enqueue(f"request:{N}"))

class SubscriberProxy(reactivestreams.Subscriber):
    def __init__(self, publisher: reactivestreams.Publisher):
        print("SubscriberProxy() [construct]")
        self.name = "SubscriberProxy"
        self.peer_name = "PublisherProxy"
        self.queue = Queue(50)
        self.publisher = publisher
        self.websocket = None
        self.recv_task = None
        self.self_acknowledged = False
        self.peer_acknowledged = False

    def synchronized(self):
        return self.self_acknowledged and self.peer_acknowledged

    async def synchronize(self, delay=1.0):
        print("SubscriberProxy.synchronize() [starting]")
        while not self.synchronized():
            print(f"SubscriberProxy.synchronize() {time.strftime('%X')} synchronizing...")
            await self.send(f"{self.name}-SYN")
            await asyncio.sleep(delay)
        print(f"SubscriberProxy.synchronize() {time.strftime('%X')} synchronized!")
        asyncio.create_task(self.processor())

    async def enqueue(self, item):
        await self.queue.put(item)

    async def dequeue(self):
        return await self.queue.get()

    async def processor(self):
        while True:
            item = await self.dequeue()
            self.process(item)

    async def connect(self, endpoint):
        print(f"SubscriberProxy.connect() endpoint: {endpoint}")
        self.websocket = await websockets.connect(endpoint)
        self.recv_task = asyncio.create_task(self.recv())
        asyncio.create_task(self.synchronize())

    async def send(self, message):
        print(f"SubscriberProxy.send() message: {message}")
        await self.websocket.send(message)

    async def recv(self):
        print("SubscriberProxy.recv() [starting]")
        while True:
            message = await self.websocket.recv()
            print(f"SubscriberProxy.recv() message: {message}")
            self.process(message)

    def process(self, message):
        print(f"SubscriberProxy.process() message: {message}")
        if (type(message) == bytes):
            asyncio.create_task(self.send(message))
        elif message == "subscribe":
            self.publisher.subscribe(self)
        elif len(message) >= 8 and message[0:8] == "request:":
            tag,value = message.split(":")
            self.publisher.request(int(value))
        elif message == "onSubscribe":
            asyncio.create_task(self.send(message))
        elif len(message) >= 7 and message[0:7] == "onNext:":
            asyncio.create_task(self.send(message))
        elif message == "onError":
            asyncio.create_task(self.send(message))
        elif message == "onComplete":
            asyncio.create_task(self.send(message))
        elif message == f"{self.name}-OK":
            self.peer_acknowledged = True
            asyncio.create_task(self.send(f"{self.name}-ACK"))
        elif message == f"{self.peer_name}-SYN":
            asyncio.create_task(self.send(f"{self.peer_name}-OK"))
        elif message == f"{self.peer_name}-ACK":
            self.self_acknowledged = True
        else:
            print(f"SubscriberProxy.process() UNHANDLED message: {message}")

    def onSubscribe(self, subscription: Subscription):
        print(f"SubscriberProxy.onSubscribe() subscription: {subscription}")
        self.subscription = subscription
        asyncio.create_task(self.enqueue("onSubscribe"))

    def onNext(self, item):
        print(f"SubscriberProxy.onNext() item: {item}")
        if type(item) == bytes:
            asyncio.create_task(self.enqueue(item))
        else:
            asyncio.create_task(self.enqueue(f"onNext:{item}"))

    def onError(self, error: Exception):
        print(f"SubscriberProxy.onError() error: {error}")
        asyncio.create_task(self.enqueue("onError"))

    def onComplete(self):
        print("SubscriberProxy.onComplete()")
        asyncio.create_task(self.enqueue("onComplete"))
