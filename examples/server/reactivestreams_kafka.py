import reactivestreams
from subscription import Subscription
from kafka import KafkaProducer, KafkaConsumer
from queue import Queue, Empty
import time
from threading import Thread, Event

#
# REFACTOR (overall)
# - replace async/await with Threads
#

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


#
# REFACTOR: KafkaSubscriber
# - replace use of async/await with Threads
#
# [x] 1. remove loop (in constructor, and as an attribute)
# [√] 2. remove from asyncio.queues import Queue, QueueEmpty
# [√] 3. add import queue, change Queue type
# [-] 4. re-think completion (completion task, completion_future, notify)
# [√] 5. writer becomes a Thread: started when onSubscribe() is called
# [√] 6. remove async/await from enqueue() and dequeue()
# [-] 7. dequeue() needs optional timeout parameter with default = 0
# [√] 8. request becomes a Thread: started on FileSubscriber construction
# [√] 9. how do we signal request to execute? threading.Event
#
class KafkaSubscriber(reactivestreams.Subscriber):
    # A Reactive Streams Subscriber that stores data in Kafka
    # Source: a Reactive Streams Publisher
    # Destination: a Kafka topic (as a Kafka Producer)

    def __init__(self, topic, broker="localhost:9092", buffer_size=50):
        print(f"KafkaSubscriber() [construct] topic: {topic} broker: {broker} buffer_size: {buffer_size}")
        self.active = True
        self.broker = broker
        self.topic = topic
        self.producer = KafkaProducer(bootstrap_servers=self.broker)
        self.buffer_size = buffer_size
        self.queue = Queue(self.buffer_size)
        self.requested = 0
        self.received = 0
        self.done = False
        #self.completion_task = None
        self.event = Event()
        self.writer_thread = None
        self.request_thread = Thread(target=self.request, args=(self.buffer_size, self.event), name="KafkaSubscriber.request()")
        self.request_thread.start()

    def buffer_space_available(self, N):
        return N <= (self.queue.maxsize - self.queue.qsize())

    def outstanding(self):
        return self.requested - self.received

    def enqueue(self, item):
        print(f"KafkaSubscriber.enqueue() item: {item}")
        self.queue.put(item)

    def dequeue(self):
        return self.queue.get_nowait()

    def writer(self, topic, event):
        print(f"KafkaSubscriber.writer() [starting] topic: {topic} event: {event}")
        while self.active or self.queue.qsize() > 0:
            event.set()
            try:
                item = self.dequeue()
                print(f"KafkaSubscriber.writer() item: {item}")
                self.received += 1
                if type(item) == bytes:
                    self.producer.send(topic, item)
                else:
                    self.producer.send(topic, bytes(item, encoding='utf_8'))
            except Empty:
                time.sleep(0.001)
        self.producer.flush()
        self.done = True

    def request(self, N, event):
        print(f"KafkaSubscriber.request() [starting] N: {N} event: {event}")
        while True:
            event.wait()
            if self.active and self.buffer_space_available(N) and self.outstanding() == 0:
                print(f"KafkaSubscriber.request() N: {N}")
                self.requested += N
                self.subscription.request(N)
            event.clear()

    #async def completion_future(self):
    #    while self.done is False:
    #        await asyncio.sleep(0.01)
    #
    #def notify(self):
    #    if self.completion_task is None:
    #        self.completion_task = asyncio.create_task(self.completion_future(), name="KafkaSubscriber->completion_future()")
    #    return self.completion_task
    #
    #def is_done(self):
    #    return self.done
    
    def onSubscribe(self, subscription: Subscription):
        print(f"KafkaSubscriber.onSubscribe() subscription: {subscription}")
        self.subscription = subscription
        self.writer_thread = Thread(target=self.writer, args=(self.topic, self.event), name="KafkaSubscriber.writer()")
        self.writer_thread.start()

    def onNext(self, item):
        print(f"KafkaSubscriber.onNext() item: {item}")
        self.enqueue(item)

    def onError(self, error: Exception):
        print(f"KafkaSubscriber.onError() error: {error}")
        self.subscription.cancel()
        self.active = False

    def onComplete(self):
        print(f"KafkaSubscriber.onComplete()")
        self.active = False
