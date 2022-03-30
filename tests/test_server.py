import sys
import os
from time import sleep
myDir = os.getcwd()
sys.path.append(myDir)

from server import app
from flask import json

import websocket.websocket_functions as websocket_functions

import pytest

def test_hello_world():
    response = app.test_client().get('/')

    # print("======")
    # print(response)
    # print("======")

    data = response.get_data(as_text=True)

    assert response.status_code == 200
    assert data == "<p>Hello, World!</p>"

def test_publish():
    with app.test_client() as c:
      response = c.post(
          '/publish',
          data=json.dumps(
            {
              'format':'edf',
              'stream-identifier': 'test-id',
              'description': 'this is a test stream',
              'tags': ['tag1', 'tag2']
            }
          ),
          content_type='application/json',
      )

      sleep(10)
      assert websocket_functions.is_port_in_use(8765)
      # print(websocket_functions.is_port_in_use(8766))
      # print(websocket_functions.is_port_in_use(8767))



      assert response is not None

      data = json.loads(response.get_data(as_text=True))

      assert response.status_code == 200
      assert data['url'] == 'dummy-url'