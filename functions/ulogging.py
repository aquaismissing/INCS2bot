import atexit
import json
import logging.config
from logging.handlers import TimedRotatingFileHandler
import os.path
from pathlib import Path
import time
from typing import override


__all__ = ['setup_logging', 'get_logger']

class EnhancedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Combining `TimedRotatingFileHandler` and `RotatingFileHandler` (adds `maxBytes` to `TimedRotatingFileHandler`).
    Based on https://stackoverflow.com/questions/6167587/the-logging-handlers-how-to-rollover-after-time-or-maxbytes
    """

    @override
    def __init__(self, filename, when='h', interval=1, backupCount=0, maxBytes=0,
                 encoding='utf-8', delay=False, utc=False, atTime=None, errors=None):
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc, atTime, errors)
        self.maxBytes=maxBytes

    @override
    def shouldRollover(self, record):
        if self.stream is None:                 # delay was set...
            self.stream = self._open()
        if self.maxBytes > 0:                   # are we rolling over?
            msg = f"{self.format(record)}\n"
            self.stream.seek(0, 2)  # due to non-posix-compliant Windows feature
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return True
        t = int(time.time())
        if t >= self.rolloverAt:
            return True
        return False

    def doRollover(self):
        if self.stream:
            self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        if self.backupCount > 0:
            cnt=1
            dfn2="%s.%03d"%(dfn,cnt)
            while os.path.exists(dfn2):
                dfn2="%s.%03d"%(dfn,cnt)
                cnt+=1
            os.rename(self.baseFilename, dfn2)
            for s in self.getFilesToDelete():
                os.remove(s)
        else:
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        #print "%s -> %s" % (self.baseFilename, dfn)
        self.mode = 'w'
        self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName + "."
        plen = len(prefix)
        for fileName in fileNames:
            if fileName[:plen] == prefix:
                suffix = fileName[plen:-4]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result


def setup_logging(config_file: str | Path = None):
    """Applies all the settings from a logging config."""

    if config_file is not None:
        with open(config_file, encoding='utf-8') as f:
            config = json.load(f)
        logging.config.dictConfig(config)

    queue_handler = logging.getHandlerByName('queue_handler')
    if queue_handler is not None:
        # noinspection PyUnresolvedReferences
        queue_handler.listener.start()
        # noinspection PyUnresolvedReferences
        atexit.register(queue_handler.listener.stop)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
