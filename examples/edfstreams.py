import reactivestreams
import filestreams
import time
from datetime import timedelta
from pyedflib import EdfReader
import pennsieve.timeseries_pb2

class EdfFileSource(filestreams.FileSource):
    def __init__(self, file_path):
        self.file_path = file_path
        self.edf = EdfReader(self.file_path)
        self.channels = [x for x in range(len(self.edf.getSignalLabels()))]
        self.signals = [self.edf.readSignal(x) for x in self.channels]
        self.generator = self.stream_protobuf()

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
