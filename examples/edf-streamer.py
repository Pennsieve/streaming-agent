#!/usr/bin/env python

import argparse
import asyncio
import websockets
import json
from datetime import timedelta
from pyedflib import EdfReader
from collections import namedtuple

class Counter():
    def __init__(self, start=0):
        self.counter = start - 1
        
    def __call__(self):
        self.counter += 1
        return self.counter
    
ChannelInfo = namedtuple("ChannelInfo",['index','label','frequency'])

class EdfFile:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.edf = EdfReader(self.file_path)
        self.channels = [x for x in range(len(self.edf.getSignalLabels()))]
        self.signals = [self.edf.readSignal(x) for x in self.channels]
        
    def header(self):
        hdr = self.edf.getHeader()
        hdr['startdate'] = str(hdr['startdate'])
        counter = Counter(0)
        return {
            "header" : hdr,
            "channels" : [ChannelInfo(counter(),x,int(y))._asdict() 
                          for x,y in list(zip(self.edf.getSignalLabels(), 
                                              list(self.edf.getSampleFrequencies())))]
        }
    
    def stream(self, channels=None):
        if channels == None: channels = self.channels
        starttime = self.edf.getStartdatetime()
        pages = self.edf.file_duration
        for page in range(pages):
            for channel in channels:
                frequency = int(self.edf.getSampleFrequency(channel))
                begin = page * frequency
                end = begin + frequency
                yield {
                    "starttime": str(starttime + timedelta(seconds=page)),
                    "channel": channel,
                    "frequency": frequency,
                    "values": list(self.signals[channel][begin:end])
                }
                    

async def main(endpoint, file):
    edf = EdfFile(file)
    async with websockets.connect(endpoint) as websocket:
        await websocket.send(json.dumps(edf.header()))
        for data in edf.stream():
            await websocket.send(json.dumps(data))
        await websocket.close()

parser = argparse.ArgumentParser()
parser.add_argument('--file', type=str)
parser.add_argument('--endpoint', type=str)
args = parser.parse_args()
asyncio.run(main(args.endpoint, args.file))
