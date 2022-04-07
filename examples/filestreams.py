from collections.abc import Iterator
from enum import Enum
import reactivestreams
from counter import Counter
import asyncio
from asyncio.queues import Queue, QueueEmpty
from subscription import Subscription

class FileSource(Iterator):
    def __init__(self, file_path):
        self.file_path = file_path
        self.generator = self.generator()

    def __repr__(self):
        return f"{self.__class__.__name__}:{self.file_path}"

    def __str__(self):
        return self.file_path

    def __next__(self):
        return self.next()

    def generator(self):
        for line in open(self.file_path, "r"):
            yield line.strip()

    def next(self):
        return next(self.generator)

# TODO: create a Subscription. call Subscriber.onSubscribe()
class FilePublisher(reactivestreams.Publisher):
    def __init__(self, file_path):
        self.subscriber = None
        self.subscription = None
        self.source = FileSource(file_path)

    def subscribe(self, subscriber: reactivestreams.Subscriber):
        print(f"FilePublisher.subscribe() subscriber: {subscriber}")
        self.subscriber = subscriber
        self.subscription = Subscription(self, subscriber)
        subscriber.onSubscribe(self.subscription)

    def request(self, N):
        print(f"FilePublisher.request(): {N}")
        try:
            for i in range(N):
                self.subscriber.onNext(self.source.next())
        except StopIteration as e:
            self.subscriber.onComplete()
        except Exception as e:
            self.subscriber.onError(e)
        else:
            pass
        finally:
            pass

class FileSubscriber(reactivestreams.Subscriber):
    def __init__(self, file_path, buffer_size=10):
        self.active = True
        self.done = False
        self.subscription = None
        self.file_path = file_path
        self.buffer_size = buffer_size
        self.queue = Queue(self.buffer_size)
        self.requested = 0
        self.received = 0
        self.completion_task = None

    def buffer_space_available(self, N):
        return N <= (self.queue.maxsize - self.queue.qsize())

    def outstanding(self):
        return self.requested - self.received

    async def enqueue(self, item):
        await self.queue.put(item)

    async def dequeue(self):
        return self.queue.get_nowait()

    async def completion_future(self):
        while self.done is False:
            await asyncio.sleep(0.01)

    def notify(self):
        if self.completion_task is None:
            self.completion_task = asyncio.create_task(self.completion_future(), name="FileSubscriber->completion_future()")
        return self.completion_task

    async def writer(self, file_path):
        with open(file_path, "w") as file:
            while self.active or self.queue.qsize() > 0:
                asyncio.create_task(self.request(self.buffer_size), name="FileSubscriber->request()")
                try:
                    item = await self.dequeue()
                    self.received += 1
                    print(f"write(): {item}")
                    file.write(f"{item}\n")
                except QueueEmpty as e:
                    await asyncio.sleep(0.001)
            self.done = True

    def onSubscribe(self, subscription: reactivestreams.Subscription):
        print(f"FileSubscriber.onSubscribe(): {subscription}")
        self.subscription = subscription
        self.async_writer = asyncio.create_task(self.writer(self.file_path), name="FileSubscriber->writer()")

    def onNext(self, item):
        print(f"FileSubscriber.onNext(): {item}")
        asyncio.create_task(self.enqueue(item), name="FileSubscriber->enqueue()")

    def onError(self, error: Exception = None):
        print(f"FileSubscriber.onError() error: {error}")
        self.subscription.cancel()
        self.active = False

    def onComplete(self):
        print(f"FileSubscriber.onComplete()")
        self.active = False

    async def request(self, N):
        if self.active and self.buffer_space_available(N) and self.outstanding() == 0:
            print(f"FileSubscriber.request(): {N}")
            self.requested += N
            self.subscription.request(N)
