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
# ----


# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
sock = Sock(app)

# enable CORS
#CORS(app, resources={r'/*': {'origins': '*'}})

streams = {}

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
    publish_url = f"ws://{host}/publish/{id}"
    streams[id] = {"request": publish_request,
                   "url": publish_url,
                   "data" : []}
    response_object = {
        'status': 'success',
        'url': publish_url,
        }
    return jsonify(response_object)

@app.route('/publish/<id>', methods=['GET'])
def publish_get(id):
    response_object = streams[id]["request"]
    return jsonify(response_object)
    
#
# /publish websocket
#
@sock.route('/publish/<id>')
def ingest(sock, id):
    while True:
        data = sock.receive()
        streams[id]['data'].append(data)
        
#
# /dump debugging endpoint 
#
@app.route('/dump', methods=['GET'])
def dump():
    print(streams)
    response = {}
    return jsonify(response)

if __name__ == '__main__':
    app.run(host="localhost", port=5678)