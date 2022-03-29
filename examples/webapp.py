#!/usr/bin/env python

import uuid
from flask import Flask, request, jsonify
#from flask_cors import CORS


# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# enable CORS
#CORS(app, resources={r'/*': {'origins': '*'}})


# sanity check route
@app.route('/publish', methods=['POST'])
def publish():
    publish_request = request.get_json()
    host = request.host
    publish_url = f"ws://{host}/{uuid.uuid4()}"
    response_object = {
        'status': 'success',
        'url': publish_url,
        }
    return jsonify(response_object)


if __name__ == '__main__':
    app.run(host="localhost", port=5678)