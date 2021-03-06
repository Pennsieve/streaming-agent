#!/usr/bin/env python

import argparse
import uuid
import json
import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from proxy import PublisherProxy
from reactivestreams_kafka import KafkaSubscriber
from wsm import WebSocketMessenger
import simple_websocket
from counter import Counter

# configuration
DEBUG = True

global_broker = None
global_buffer_size = None

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})


# terminology:
#   label = user-provided identifier (or service generated)
#   stream id = UUID generated by this service

# index: maps user-provided label to stream id
#   key = stream id
#   value = label
INDEX = {}

# streams: keeps track of requests, and publish and subscribe URLs
#   key = stream id
#   value = dictionary
#     label = 
#     title = 
#     description = 
# 
STREAMS = {}

# TODO: make this into a generator, persist Counter state
label_counter = Counter(1)
def generated_label():
    return "ID-{number:05d}".format(number = label_counter())

def publish_url(host, id):
    return f"ws://{host}/publish/{id}"

def subscribe_url(host, id):
    return f"ws://{host}/subscribe/{id}"

def stream_details(stream_id):
    return STREAMS.get(stream_id, {})

def current_time():
    return time.strftime('%Y-%m-%d %H:%M:%S')

#
# state management (load/store using files)
#
def load_state():
    index = {}
    streams = {}
    try:
        with open('streams.json', 'r') as fp:
            streams = json.load(fp)
        with open('index.json', 'r') as fp:
            index = json.load(fp)
    except Exception as e:
        logging.warn(f"load_state() WARNING - Exception: {e}")
    return index, streams

def store_state(index, streams):
    try:
        with open('streams.json', 'w') as fp:
            json.dump(streams, fp)
        with open('index.json', 'w') as fp:
            json.dump(index, fp)
    except Exception as e:
        logging.warn(f"store_state() WARNING - Exception: {e}")

#
# /stream endpoint
#   GET:   return one stream by stream id (or label)
#
@app.route('/stream/<stream_id>', methods=['GET'])
def stream_get(stream_id):
    response_object = {
        'status': 'success'
        }
    if stream_id in STREAMS:
        response_object['stream'] = stream_details(stream_id)
    elif stream_id in INDEX:
        response_object['stream'] = stream_details(INDEX[stream_id])
    else:
        response_object['message'] = 'stream not found'
    return jsonify(response_object)


#
# /stream endpoint
#   POST:   create a new stream
#
#   request: a JSON fragment
#     {
#       label: a short, user-provided identifier (e.g., "ID-12345")
#       title: the title of the time-series stream
#       description: a longer description of the time-series data
#     }
#     Required: `title` and `description`
#     If a `label` is not provided, then one can be generated ("ID-nnnnn")
#
#   response: a JSON fragment
@app.route('/stream', methods=['POST'])
def stream_post():
    post_request = request.get_json()
    stream_id = str(uuid.uuid4())
    host = request.host
    pub_url = publish_url(host, stream_id)
    sub_url = subscribe_url(host, stream_id)
    label = post_request.get('label', generated_label())
    title = post_request.get('title', "(none)")
    description = post_request.get('description',"(none)")
    data_format = post_request.get('format', "(unknown)")
    metadata = post_request.get('metadata', {})
    INDEX[label] = stream_id
    STREAMS[stream_id] = {
        'stream_id': stream_id,
        'label': label,
        'title': title,
        'description': description,
        'format': data_format,
        'metadata': metadata,
        'active': False,
        'publish_url': f"{pub_url}",
        'subscribe_url': f"{sub_url}"
        }
    
    # save state
    store_state(INDEX, STREAMS)
    
    return jsonify({
        'status': 'success',
        'message': 'stream created',
        'publish_url': pub_url,
        'subscribe_url': sub_url
        })

#
# /stream endpoint
#   PUT:    update a stream
#
# TODO: implement (require entire JSON like POST? or accept partial fragments?)
#
@app.route('/stream/<stream_id>', methods=['PUT'])
def stream_put(stream_id):
    if stream_id in STREAMS:
        post_data = request.get_json()
        label = post_data.get('label')
        if label is not None:
            old_label = STREAMS[stream_id]['label']
            del INDEX[old_label]
            INDEX[label] = stream_id
            STREAMS[stream_id]['label'] = label
        title = post_data.get('title')
        if title is not None:
            STREAMS[stream_id]['title'] = title
        description = post_data.get('description')
        if description is not None:
            STREAMS[stream_id]['description'] = description
        
        # save state
        store_state(INDEX, STREAMS)
        
        return jsonify({
            'status': 'success',
            'message': 'stream updated',
            'publish_url': STREAMS[stream_id]['publish_url'],
            'subscribe_url': STREAMS[stream_id]['subscribe_url']
            })
    else:
        return jsonify({
            'status': 'success',
            'message': 'stream not found'
            })

#
# /stream endpoint
#   DELETE: remove a stream
#
# TODO: delete persisted stream data from Kafka
#
@app.route('/stream', methods=['DELETE'])
def stream_delete():
    response_object = {
        'status': 'success'
        }
    delete_request = request.get_json()
    stream_id = delete_request.get('stream_id')
    if stream_id is not None:
        if stream_id in STREAMS:
            label = STREAMS[stream_id]['label']
            del INDEX[label]
            del STREAMS[stream_id]
            response_object['message'] = 'stream deleted'
        else:
            response_object['message'] = 'stream not found'
    else:
        response_object['message'] = 'stream_id not provided'
    
    # save state
    store_state(INDEX, STREAMS)
    
    return jsonify(response_object)


#
# /streams endpoint
#
#   GET:   return all streams
#

@app.route('/streams', methods=['GET'])
def streams():
    return jsonify({
        'status': 'success',
        'streams': [STREAMS[s] for s in STREAMS]
        })


#
# /publish websocket
#
@app.route('/publish/<stream_id>', websocket=True)
def publish_stream(stream_id):
    ws = simple_websocket.Server(request.environ)
    connection_message = f"{current_time()} - web-service.publish_stream() START stream_id: {stream_id}"
    print(connection_message)
    logging.info(connection_message)
    topic = f"pennsieve.timeseries.{stream_id}"
    
    try:
        count = 0
        messenger = WebSocketMessenger(ws)
        publisher = PublisherProxy(messenger=messenger, synchronize=True)
        subscriber = KafkaSubscriber(topic=topic, broker=global_broker, buffer_size=global_buffer_size)
        publisher.subscribe(subscriber)
        logging.debug("web-service.publish_stream() starting receive loop...")
        STREAMS[stream_id]['active'] = True
        store_state(INDEX, STREAMS)
        while subscriber.complete() == False:
            message = ws.receive(timeout=1)
            if message is not None:
                count += 1
                logging.debug(f"web-service.publish_stream() ws.receive({count}) message: {message}")
                publisher.event(message)
    except simple_websocket.ConnectionClosed:
        logging.info("web-service.publish_stream() exception: simple_websocket.ConnectionClosed")
    finally:
        completion_message = f"{current_time()} - web-service.publish_stream() FINISH stream_id: {stream_id} received {count} messages"
        print(completion_message)
        logging.info(completion_message)
        ws.close()
    
    STREAMS[stream_id]['active'] = False
    store_state(INDEX, STREAMS)
    
    return jsonify({
        'status': 'success',
        'message': 'stream publishing complete'
        })

#
# /subscribe endpoint
#
#@app.route('/subscribe/<label>', methods=['GET'])
#def subscribe_get(label):
#    response = {}
#    if label in index:
#        id = index[label]
#        sub_url = streams[id]['subscribe_url']
#        response = {
#            'status': 'success',
#            'url': sub_url
#        }
#    else:
#        response = {
#            'status': 'failure',
#            'message': f"unknown label: {label}"
#        }
#    return jsonify(response)

#
# /subscribe websocket
#
# TODO: do something in exception handling branch
#
#@sock.route('/subscribe/<id>')
#def egress(ws, id):
#    print(f"web-service.egress() ws: {ws} [type: {type(ws)}]")
#    try:
#        #count = 0
#        topic = f"pennsieve.timeseries.{id}"
#        consumer = KafkaConsumer(topic)
#        for message in consumer:
#            ws.send(message)
#    except Exception:
#        pass
#    finally:
#        ws.close()


#
# /dump debugging endpoint
#
@app.route('/dump/<item>', methods=['GET'])
def dump(item):
    if item == "index":
        return jsonify(INDEX)
    elif item == "streams":
        return jsonify(STREAMS)


# health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'success',
        'health': 'OK'
        })


# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default="localhost")
parser.add_argument('--port', type=int, default=5678)
parser.add_argument('--broker', type=str, default="localhost:9092")
parser.add_argument('--buffer-size', type=int, default=10)
parser.add_argument('--log-file', type=str, default='server.log')
parser.add_argument('--log-level', type=str, default='DEBUG')
args = parser.parse_args()

# initialize logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename=args.log_file,
                    level=getattr(logging, args.log_level.upper()))

# set some parameters
global_broker = args.broker
global_buffer_size = args.buffer_size

# load state
INDEX, STREAMS = load_state()

# run the web service
logging.info(f"web-service starting host: {args.host} port: {args.port}")
app.run(host=args.host, port=args.port)
