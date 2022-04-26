from collections.abc import Iterator
import reactivestreams
import asyncio
from subscription import Subscription
from queue import Queue, Empty
from threading import Thread, Event
import time
import logging

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

#
# REFACTOR: FilePublisher
# - decouple request() and calling sunscriber.onNext() 
# - make delivery of items to subscriber asynchronous
#
class FilePublisher(reactivestreams.Publisher):
    def __init__(self, file_path=None, file_source=None):
        logging.debug("FilePublisher() [construct]")
        self.subscriber = None
        self.subscription = None
        if file_source is not None:
            self.source = file_source
        elif file_path is not None:
            self.source = FileSource(file_path)
        else:
            raise ValueError("must provide file_source or file_path")

    def subscribe(self, subscriber: reactivestreams.Subscriber):
        logging.debug(f"FilePublisher.subscribe() subscriber: {subscriber}")
        self.subscriber = subscriber
        self.subscription = Subscription(self, subscriber)
        subscriber.onSubscribe(self.subscription)

    def request(self, N):
        logging.debug(f"FilePublisher.request() N: {N}")
        try:
            for i in range(N):
                self.subscriber.onNext(self.source.next())
        except StopIteration:
            self.subscriber.onComplete()
        except Exception as e:
            self.subscriber.onError(e)
        else:
            pass
        finally:
            pass

#
# REFACTOR: FileSubscriber
# - replace use of async/await with Threads
#
# [√] 1. remove loop (in constructor, and as an attribute)
# [√] 2. remove from asyncio.queues import Queue, QueueEmpty
# [√] 3. add import queue, change Queue type
# [-] 4. re-think completion (completion task, completion_future, notify)
# [√] 5. writer becomes a Thread: started when onSubscribe() is called
# [√] 6. remove async/await from enqueue() and dequeue()
# [√] 7. dequeue() needs optional timeout parameter with default = 0
# [√] 8. request becomes a Thread: started on FileSubscriber construction
# [√] 9. how do we signal request to execute? threading.Event
#
# REFACTOR: queue handling
# 1. make queue size buffer_size + a small amount
# 2. block on enqueue() - with a timeout? how will we handle Full exception?
# 3. don't block on dequeue(), but permit a timeout?
#
class FileSubscriber(reactivestreams.Subscriber):
    def __init__(self, file_path, buffer_size=10):
        logging.debug(f"FileSubscriber() [construct] file_path: {file_path} buffer_size: {buffer_size}")
        self.active = True
        self.done = False
        self.subscription = None
        self.file_path = file_path
        self.buffer_size = buffer_size
        self.queue = Queue(maxsize=buffer_size)
        self.requested = 0
        self.received = 0
        #self.completion_task = None
        self.event = Event()
        self.writer_thread = None
        self.request_thread = Thread(target=self.request, args=(self.buffer_size, self.event), name="FileSubscriber.request()")
        self.request_thread.start()

    def buffer_space_available(self, N):
        return N <= (self.queue.maxsize - self.queue.qsize())

    def outstanding(self):
        return self.requested - self.received

    def enqueue(self, item):
        self.queue.put(item)

    def dequeue(self, timeout=0):
        return self.queue.get_nowait()

    #async def completion_future(self):
    #    while self.done is False:
    #        await asyncio.sleep(0.01)
    #
    #def notify(self):
    #    if self.completion_task is None:
    #        self.completion_task = self.loop.create_task(self.completion_future(), name="FileSubscriber->completion_future()")
    #    return self.completion_task

    def writer(self, file_path, event):
        logging.debug(f"FileSubscriber.writer() [starting] file_path: {file_path} event: {event}")
        with open(file_path, "w") as file:
            while self.active or self.queue.qsize() > 0:
                event.set()
                try:
                    item = self.dequeue()
                    self.received += 1
                    logging.debug(f"write(): {item}")
                    file.write(f"{item}\n")
                except Empty:
                    time.sleep(0.001)
            self.done = True

    def onSubscribe(self, subscription: reactivestreams.Subscription):
        logging.debug(f"FileSubscriber.onSubscribe() subscription: {subscription}")
        self.subscription = subscription
        self.writer_thread = Thread(target=self.writer, args=(self.file_path, self.event), name="FileSubscriber.writer()")
        self.writer_thread.start()

    def onNext(self, item):
        logging.debug(f"FileSubscriber.onNext() item: {item}")
        self.enqueue(item)

    def onError(self, error: Exception = None):
        logging.debug(f"FileSubscriber.onError() error: {error}")
        self.subscription.cancel()
        self.active = False

    def onComplete(self):
        logging.debug("FileSubscriber.onComplete()")
        self.active = False

    def request(self, N, event):
        logging.debug(f"FileSubscriber.request() [starting] N: {N} event: {event}")
        while True:
            event.wait()
            if self.active and self.buffer_space_available(N) and self.outstanding() == 0:
                logging.debug(f"FileSubscriber.request() N: {N}")
                self.requested += N
                self.subscription.request(N)
            event.clear()
