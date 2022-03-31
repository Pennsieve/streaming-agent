#!/usr/bin/env python

import uuid
from flask import Flask, request, jsonify
from flask_sock import Sock
#from flask_cors import CORS

# --++
#
# Requirements:
#   - pip install flask-sock (Note this will update Flask to 2.1.1)
#
# Notes:
#   - this implementation is likely not very safe due to:
#       (1) the use of `data` in the global namespace
#       (2) potential concurrent read and write access to `data`
#
# ----


# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
sock = Sock(app)

# enable CORS
#CORS(app, resources={r'/*': {'origins': '*'}})

# index: maps user-provided label to stream id
index = {}
# streams: keeps track of requests, and publish and subscribe URLs
streams = {}
# data: the streams of data
data = {}

def publish_url(host, id):
    return f"ws://{host}/publish/{id}"

def subscribe_url(host, id):
    return f"ws://{host}/subscribe/{id}"

#
# /publish endpoint
#
#   request: a JSON fragment
#   response: a JSON fragment
#
@app.route('/publish', methods=['POST'])
def publish_post():
    publish_request = request.get_json()
    id = str(uuid.uuid4())
    host = request.host
    pub_url = publish_url(host, id)
    sub_url = subscribe_url(host, id)
    index[publish_request["label"]] = id
    streams[id] = {"request": publish_request, 
                   "publish_url": f"{pub_url}",
                   "subscribe_url": f"{sub_url}"}
    data[id] = []
    response_object = {
        'status': 'success',
        'url': pub_url,
        }
    return jsonify(response_object)

@app.route('/publish/<id>', methods=['GET'])
def publish_get(id):
    response_object = streams[id]["request"]
    return jsonify(response_object)
    
#
# /publish websocket
#
# TODO: handle close of WebSocket from peer (currently this raises a ConnectionError)
#
@sock.route('/publish/<id>')
def ingest(sock, id):
    while True:
        message = sock.receive()
        data[id].append(message)
        
#
# /dump debugging endpoint 
#
@app.route('/dump', methods=['GET'])
def dump():
    print(streams)
    print(index)
    response = {}
    return jsonify(response)

if __name__ == '__main__':
    app.run(host="localhost", port=5678)