from flask import Flask
from flask import request
import json
import uuid
import csv

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# request format:
# -- "format": label or identifier for a data format or ingest pre-processing -- this is the transformation piece which knows specific data formats (e.g., EDF) and converts to standard format
# -- "stream-identifier": label or identifier [optional?] -- short string that will uniquely identify the stream; user can remember it and use it later
# -- "description":  long string, a sentence or two describing the data
# -- "tags" [optional]: list of tags to enable searching and filtering
# 
# 
@app.route('/publish', methods=['POST'])
def publish():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        req_dict = json.loads(request.json)

        my_uuid = uuid.uuid4()

        # write format, stream-identifier, description, tags, and my_uuid to csv
        csv_columns = ['uuid', 'format', 'stream-identifier', 'description', 'tags']
        req_dict['uuid'] = my_uuid

        file_name = "stream-metadata-" + my_uuid + ".csv"
        try:
            with open(file_name, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writeheader()
                writer.writerow(req_dict)
        except IOError:
            print("I/O error")

        # instantiate web socket connection

        return {
          "uuid": my_uuid,
          "url": "dummy-url"
        }
    else:
        return 'Content-Type not supported!'