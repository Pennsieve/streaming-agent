import reactivestreams
import websockets
import asyncio
from subscription import Subscription

class PublisherProxy(reactivestreams.Publisher):
    def __init__(self, websocket=None):
        self.websocket = websocket
        self.recv_task = None
        self.start_recv()

    def start_recv(self):
        if self.websocket is not None:
            self.recv_task =  asyncio.create_task(self.recv(self.websocket))

    def connect(self, endpoint):
        self.websocket = await websockets.connect(endpoint)
        self.start_recv()

    async def send(self, message):
        await self.websocket.send(message)

    async def recv(self, websocket):
        async for message in websocket:
            self.process(message)

    def process(self, message):
        if (type(data) == bytes):
            self.subscriber.onNext(message)
        elif message == "onSubscribe":
            self.subscription = Subscription(self, self.subscriber)
            self.subscriber.onSubscribe(self.subscription)
        elif message == "onComplete":
            self.subscriber.onComplete()
        elif message == "onError":
            self.subscriber.onError()

    def subscribe(self, subscriber: reactivestreams.Subscriber):
        # send "subscribe" over the websocket
        self.subscriber = subscriber
        self.send("subscribe")

    def request(self, N):
        self.send(f"request:{N}")

class SubscriberProxy(reactivestreams.Subscriber):
    def __init__(self, publisher: reactivestreams.Publisher, websocket=None):
        self.publisher = publisher
        self.websocket = websocket
        self.recv_task = None
        self.start_recv()

    def start_recv(self):
        if self.websocket is not None:
            self.recv_task =  asyncio.create_task(self.recv(self.websocket))

    def connect(self, endpoint):
        self.websocket = await websockets.connect(endpoint)
        self.start_recv()

    async def send(self, message):
        await self.websocket.send(message)

   async def recv(self, websocket):
       for message in websocket:
           self.process(message)

    def process(self, message):
        if message == "subscribe":
            self.publisher.subscribe(self)
        elif ":" in message:
            tag,value = message.split(":")
            if tag == "request":
                self.publisher.request(int(value))

    def onSubscribe(self, subscription: Subscription):
        self.subscription = subscription
        self.send("onSubscribe")

    def onNext(self, item):
        self.send(item)

    def onError(self, error: Exception):
        self.send("onError")

    def onComplete(self):
        self.send("onComplete")
