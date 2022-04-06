#
# Reactive Streams Implementation
#

from abc import ABC, abstractmethod

class Subscription(ABC):
    @abstractmethod
    def request(self, N: int):
        ...

    @abstractmethod
    def cancel(self):
        ...

class Subscriber:
    @abstractmethod
    def onSubscribe(self, subscription: Subscription):
        ...

    @abstractmethod
    def onNext(self, item):
        ...

    @abstractmethod
    def onError(self, error: Exception):
        ...

    @abstractmethod
    def onComplete(self):
        ...

class Publisher(ABC):
    @abstractmethod
    def subscribe(self, subscriber: Subscriber):
        ...

    @abstractmethod
    def request(self, N):
        ...
