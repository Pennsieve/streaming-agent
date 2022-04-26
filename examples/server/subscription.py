import reactivestreams

class Subscription(reactivestreams.Subscription):
    def __init__(self, publisher: reactivestreams.Publisher, subscriber: reactivestreams.Subscriber):
        self.active = True
        self.publisher = publisher
        self.subscriber = subscriber

    def request(self, N: int):
        if self.active:
            self.publisher.request(N)

    def cancel(self):
        self.active = False
