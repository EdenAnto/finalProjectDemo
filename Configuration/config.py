import logging, os
from logging.handlers import RotatingFileHandler

class VideoDetectionCls:
    def __init__(self, videoName, fileName, format, hash):
        self.fileName = fileName
        self.name = videoName
        self.basePath = f'./static/Data/{self.fileName}'
        self.framesPath = f'./static/Data/{self.fileName}/frames/frames'
        self.taggedFramesPath = f'./static/Data/{self.fileName}/frames/taggedframes'
        self.inputPath = f'./static/Data/{self.fileName}/input/{fileName}{format}'
        self.outputFolder = f'./static/Data/{self.fileName}/output'
        self.outputPath = f'{self.outputFolder}/tagged_{self.fileName}{format}'
        self.hash=hash
        self.format=format
        self.frameCount=0
        self.data={}
        self.prompt={'current': ''}
        self.promptSet=set()
        self.nextStep= [-1]
        self.processing=''

        
    def logSet(self, logger):
        self.log = logger
    
    def updateProcessing(self, update):
        self.processing = update
    
  import os
from logging.handlers import RotatingFileHandler
import logging

def setup_logger(name, logPath):
    # Use /tmp directory for logs in environments with read-only filesystems
    writable_log_path = logPath if os.access(logPath, os.W_OK) else '/tmp/server.log'
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(writable_log_path, maxBytes=1024*1024*10, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


