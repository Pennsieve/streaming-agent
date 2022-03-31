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

#
# /publish endpoint
#
#   request: a JSON fragment
#   response: a JSON fragment
#
@app.route('/publish', methods=['POST'])
def publish():
    publish_request = request.get_json()
    host = request.host
    publish_url = f"ws://{host}/publish/{uuid.uuid4()}"
    response_object = {
        'status': 'success',
        'url': publish_url,
        }
    return jsonify(response_object)

#
# /publish websocket
#
@sock.route('/publish/<id>')
def ingest(sock, id):
    while True:
        data = sock.receive()
        print(f"{id} data: {data}")

if __name__ == '__main__':
    app.run(host="localhost", port=5678)