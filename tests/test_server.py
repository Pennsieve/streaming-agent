import sys
import os
myDir = os.getcwd()
sys.path.append(myDir)

from server import app
from flask import json

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
    response = app.test_client().post(
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

    assert response is not None

    data = json.loads(response.get_data(as_text=True))

    assert response.status_code == 200
    assert data['url'] == 'dummy-url'