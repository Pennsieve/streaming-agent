#!/usr/bin/env python

import logging
from enum import Enum 
import reactivestreams
from subscription import Subscription
import queue

class MessageHandler:
    def __init__(self):
        logging.debug(f"MessageHandler [construct] {self}")
    
    def __call__(self, message):
        logging.debug(f"MessageHandler() message: {message}")

#
# Synchronization
#
# 1. client connects to server
# 2. server sends "SYN"
# 3. client receives "SYN" and sends "ACK"
# 4. server receives "ACK" and sends "OK"
# 5. client receives "OK" and sends "DONE"
#

class ProxySynchronization(Enum):
    NOP  = "Proxy-NOP"
    SYN  = "Proxy-SYN"
    ACK  = "Proxy-ACK"
    OK   = "Proxy-OK"
    DONE = "Proxy-DONE"
    
    def isNOP(message):
        if message == ProxySynchronization.NOP or message == ProxySynchronization.NOP.value:
            return True
        else:
            return False
        
    def isSYN(message):
        if message == ProxySynchronization.SYN or message == ProxySynchronization.SYN.value:
            return True
        else:
            return False
        
    def isACK(message):
        if message == ProxySynchronization.ACK or message == ProxySynchronization.ACK.value:
            return True
        else:
            return False
        
    def isOK(message):
        if message == ProxySynchronization.OK or message == ProxySynchronization.OK.value:
            return True
        else:
            return False
        
    def isDONE(message):
        if message == ProxySynchronization.DONE or message == ProxySynchronization.DONE.value:
            return True
        else:
            return False

class ProxySynchronizer:
    def __init__(self):
        self.state = ProxySynchronization.NOP
        
    def __call__(self):
        return self.synchronized()

    def synchronized(self):
        return self.state == ProxySynchronization.DONE
        
    def init(self):
        return self.event(self.state)
    
    def message(self):
        return self.state.value
    
    def event(self, message):
        send = True
        logging.debug(f"ProxySynchronizer.event() message: {message}")
        if ProxySynchronization.isNOP(message):
            logging.debug("ProxySynchronizer.event() received NOP next SYN")
            self.state = ProxySynchronization.SYN
        elif ProxySynchronization.isSYN(message):
            logging.debug("ProxySynchronizer.event() received SYN next ACK")
            self.state = ProxySynchronization.ACK
        elif ProxySynchronization.isACK(message):
            logging.debug("ProxySynchronizer.event() received ACK next OK")
            self.state = ProxySynchronization.OK
        elif ProxySynchronization.isOK(message):
            logging.debug("ProxySynchronizer.event() received OK next DONE")
            self.state = ProxySynchronization.DONE
        elif ProxySynchronization.isDONE(message):
            logging.debug("ProxySynchronizer.event() received DONE next DONE")
            send = False
            self.state = ProxySynchronization.DONE
        else:
            logging.debug("ProxySynchronizer.event() received <unknown> next SYN")
            self.state = ProxySynchronization.SYN
            
        return send

class PublisherProxy(reactivestreams.Publisher):
    def __init__(self, messenger = None, synchronize = False):
        logging.debug(f"PublisherProxy [construct] {self} messenger: {messenger} synchronize: {synchronize}")
        self.queue = queue.Queue()
        self.messenger = messenger
        self.synchronized = ProxySynchronizer()
        if synchronize and self.synchronized.init():
            self.messenger(self.synchronized.message())

    def event(self, message):
        logging.debug(f"PublisherProxy.event() message: {message}")
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
            self.subscriber.onError("error")
        elif len(message) > 5 and message[0:5] == "Proxy":
            if self.synchronized.event(message):
                self.messenger(self.synchronized.message())
            else:
                self.send(None)
        else:
            logging.debug("PublisherProxy.event() UNHANDLED")
        
    def send(self, message):
        if message is not None:
            logging.debug(f"PublisherProxy.send() ENQUEUE message: {message}")
            self.queue.put(message)
        if self.synchronized():
            while self.queue.empty() is False:
                item = self.queue.get()
                logging.debug(f"PublisherProxy.send() SEND item: {item}")
                self.messenger(item)
        
    def subscribe(self, subscriber: reactivestreams.Subscriber):
        logging.debug(f"PublisherProxy.subscribe() subscriber: {subscriber}")
        self.subscriber = subscriber
        self.send("subscribe")
    
    def request(self, N):
        logging.debug(f"PublisherProxy.request() N: {N}")
        self.send(f"request:{N}")


class SubscriberProxy(reactivestreams.Subscriber):
    def __init__(self, publisher: reactivestreams.Publisher, messenger = None, synchronize = False):
        logging.debug(f"SubscriberProxy [construct] {self} messenger: {messenger} synchronize: {synchronize}")
        self.queue = queue.Queue()
        self.messenger = messenger
        self.publisher = publisher
        self.synchronized = ProxySynchronizer()
        if synchronize and self.synchronized.init():
            self.messenger(self.synchronized.message())

    def event(self, message):
        logging.debug(f"SubscriberProxy.event() message: {message}")
        if message == "subscribe":
            self.publisher.subscribe(self)
        elif len(message) >= 8 and message[0:8] == "request:":
            tag,value = message.split(":")
            self.subscription.request(int(value))
        elif len(message) > 5 and message[0:5] == "Proxy":
            if self.synchronized.event(message):
                self.messenger(self.synchronized.message())
            else:
                self.send(None)
        else:
            logging.debug("SubscriberProxy.event() UNHANDLED")
        
    def send(self, message):
        if message is not None:
            logging.debug(f"SubscriberProxy.send() ENQUEUE message: {message}")
            self.queue.put(message)
        if self.synchronized():
            while self.queue.empty() is False:
                item = self.queue.get()
                logging.debug(f"SubscriberProxy.send() SEND item: {item}")
                self.messenger(item)
    
    def onSubscribe(self, subscription: Subscription):
        logging.debug(f"SubscriberProxy.onSubscribe() subscription: {subscription}")
        self.subscription = subscription
        self.send("onSubscribe")
    
    def onNext(self, item):
        logging.debug(f"SubscriberProxy.onNext() item: {item}")
        if type(item) == bytes:
            self.send(item)
        else:
            self.send(f"onNext:{item}")
    
    def onError(self, error: Exception):
        logging.debug(f"SubscriberProxy.onError() error: {error}")
        self.send("onError")
    
    def onComplete(self):
        logging.debug("SubscriberProxy.onComplete()")
        self.send("onComplete")
