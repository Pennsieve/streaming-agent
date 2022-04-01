# Examples

## Files in this folder

| File | Description                      |
| ---- | -------------------------------- |
| web-service.py | ??? |


## Prerequisites
The following packages must be installed
- [Python](https://www.python.org) 3.9.10
- [Flask](https://flask.palletsprojects.com/en/2.1.x/) 2.1.1
- [Flask-Sock](https://flask-sock.readthedocs.io/en/latest/) 0.5.2
- [PyEDFlib](https://pyedflib.readthedocs.io/en/latest/) 0.1.28
- [websockets](https://websockets.readthedocs.io/en/stable/) 10.2
- Protocol Buffers 3.19.4

## Running the Example Implementation

1. start the Web Service
```
./web-service.py
```

2. make a request to **publish**
```
./publish-request.sh
```
  - take note of the URL in the response:
```json
{
  "status": "success",
  "url": "ws://localhost:5678/publish/d397fb58-e941-47fc-93ad-1b806df37473"
}
```

3. run the EDF streamer to stream data into the WebService
```
./edf-streamer.py --file test.edf --endpoint ws://localhost:5678/publish/d397fb58-e941-47fc-93ad-1b806df37473
```

4. make a request to **subscribe**
```
./subscribe-request.sh
```
  - take note of the URL in the response:
  ```json
{
  "status": "success",
  "url": "ws://localhost:5678/subscribe/d397fb58-e941-47fc-93ad-1b806df37473"
}
```

5. stream the data out of the WebService
```
./streaming-subscriber.py --endpoint ws://localhost:5678/subscribe/d397fb58-e941-47fc-93ad-1b806df37473
```
  - Note: this will output a lot of data to stdout

## Protocol Buffers

### Installation

Install the Protocol Buffer compiler:
```
brew install protobuf
```

Install the protobuf Python package
```
pip install protobuf=3.19.4
```

### Time-series

The protocol buffer definitions are in `timeseries.proto`

Compile the protocol buffer definitions with:
```
mkdir -p ./pennsieve
protoc -I=. --python_out=pennsieve timeseries.proto
```
