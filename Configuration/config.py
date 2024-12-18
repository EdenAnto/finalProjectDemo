import os

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

    
    def updateProcessing(self, update):
        self.processing = update
    
    