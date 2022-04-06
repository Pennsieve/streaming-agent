#!/usr/bin/env python

import argparse
import asyncio
import websockets
import json
import time
from datetime import timedelta
from pyedflib import EdfReader
from collections import namedtuple
import pennsieve.timeseries_pb2
from counter import Counter

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

    def stream_protobuf(self, channels=None):
        if channels == None: channels = self.channels
        starttime = self.edf.getStartdatetime()
        pages = self.edf.file_duration
        for page in range(pages):
            for channel in channels:
                frequency = self.edf.getSampleFrequency(channel)
                page_time = starttime + timedelta(seconds=page)
                timestamp = int(time.mktime(starttime.timetuple()))
                begin = page * int(frequency)
                end = begin + int(frequency)
                ingest_segment = pennsieve.timeseries_pb2.IngestSegment()
                ingest_segment.channelId = str(channel)
                ingest_segment.samplePeriod = frequency
                ingest_segment.startTime = timestamp
                ingest_segment.data.extend(list(self.signals[channel][begin:end]))
                yield ingest_segment.SerializeToString()

async def main(endpoint, file):
    count = 0
    edf = EdfFile(file)
    async with websockets.connect(endpoint) as websocket:
        #await websocket.send(json.dumps(edf.header()))
        for data in edf.stream_protobuf():
            count += 1
            await websocket.send(data)
        await websocket.close()
        print(f"sent {count} messages")

parser = argparse.ArgumentParser()
parser.add_argument('--file', type=str)
parser.add_argument('--endpoint', type=str)
args = parser.parse_args()
asyncio.run(main(args.endpoint, args.file))
