import reactivestreams
from subscription import Subscription
from kafka import KafkaProducer, KafkaConsumer
import asyncio
from asyncio.queues import Queue, QueueEmpty

class KafkaPublisher(reactivestreams.Publisher):
    # A Reactive Streams Publisher that publishes data from Kafka
    # Source: Kafka topic (as a Kafka Consumer)
    # Destination: a reactivestreams.Subscriber

    def __init__(self, topic, broker="localhost:9092"):
        print(f"KafkaPublisher() [construct]")
        self.broker = broker
        self.topic = topic
        self.consumer = KafkaConsumer(self.topic, bootstrap_servers = self.broker)

    def subscribe(self, subscriber: reactivestreams.Subscriber):
        print(f"KafkaPublisher.subscribe() subscriber: {subscriber}")
        self.subscriber = subscriber
        self.subscriber.onSubscribe(Subscription(self, self.subscriber))

    def request(self, N):
        print(f"KafkaPublisher.request() N: {N}")
        for i in range(N):
            message = next(self.consumer)
            self.subscriber.onNext(message)

class KafkaSubscriber(reactivestreams.Subscriber):
    # A Reactive Streams Subscriber that stores data in Kafka
    # Source: a Reactive Streams Publisher
    # Destination: a Kafka topic (as a Kafka Producer)

    def __init__(self, topic, broker="localhost:9092", buffer_size=50):
        print(f"KafkaSubscriber() [construct]")
        self.active = True
        self.broker = broker
        self.topic = topic
        self.producer = KafkaProducer(bootstrap_servers=self.broker)
        self.buffer_size = buffer_size
        self.queue = Queue(self.buffer_size)
        self.requested = 0
        self.received = 0
        self.done = False
        self.completion_task = None

    def buffer_space_available(self, N):
        return N <= (self.queue.maxsize - self.queue.qsize())

    def outstanding(self):
        return self.requested - self.received

    async def enqueue(self, item):
        print(f"KafkaSubscriber.enqueue() item: {item}")
        await self.queue.put(item)

    async def dequeue(self):
        return self.queue.get_nowait()

    async def writer(self):
        print(f"KafkaSubscriber.writer() [starting]")
        while self.active or self.queue.qsize() > 0:
            asyncio.create_task(self.request(self.buffer_size), name="KafkaSubscriber->request()")
            try:
                item = await self.dequeue()
                print(f"KafkaSubscriber.writer() item: {item}")
                self.received += 1
                if type(item) == bytes:
                    self.producer.send(self.topic, item)
                else:
                    self.producer.send(self.topic, bytes(item, encoding='utf_8'))
            except QueueEmpty as e:
                await asyncio.sleep(0.001)
        self.producer.flush()
        self.done = True

    async def request(self, N):
        if self.active and self.buffer_space_available(N) and self.outstanding() == 0:
            print(f"KafkaSubscriber.request() N: {N}")
            self.requested += N
            self.subscription.request(N)

    async def completion_future(self):
        while self.done is False:
            await asyncio.sleep(0.01)

    def notify(self):
        if self.completion_task is None:
            self.completion_task = asyncio.create_task(self.completion_future(), name="KafkaSubscriber->completion_future()")
        return self.completion_task

    def onSubscribe(self, subscription: Subscription):
        print(f"KafkaSubscriber.onSubscribe() subscription: {subscription}")
        self.subscription = subscription
        self.async_writer = asyncio.create_task(self.writer(), name="KafkaSubscriber->writer()")

    def onNext(self, item):
        print(f"KafkaSubscriber.onNext() item: {item}")
        asyncio.create_task(self.enqueue(item))

    def onError(self, error: Exception):
        print(f"KafkaSubscriber.onError() error: {error}")
        self.subscription.cancel()
        self.active = False

    def onComplete(self):
        print(f"KafkaSubscriber.onComplete()")
        self.active = False
