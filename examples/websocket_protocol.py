class PublisherProtocol():
    def __init__(self, source):
        self.source = source

    def process(self, message):
        response = None
        if message == "connected()" or message == "Subscriber()":
            response = "Publisher()"
        elif message == "subscribe()":
            response = "onSubscribe()"
        elif message == "request()":
            try:
                if next(self.source):
                    response = "onNext()"
            except StopIteration as e:
                response = "onComplete()"
            except Exceptionn as e:
                response = "onError()"
        elif message == "cancel()":
            response == "goodbye()"
        return response

class SubscriberProtocol():
    def __init__(self):
        pass

    def process(self, message):
        response = None
        if message == "connected()":
            response = "Subscriber()"
        elif message == "Publisher()":
            response = "subscribe()"
        elif message == "onSubscribe()" or message == "onNext()":
            response = "request()"
        elif message == "onComplete()" or message == "onError()":
            response = "cancel()"
        elif message == "goodbye()":
            response = None
        return response
