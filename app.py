import random, base64
import sys,os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_from_directory
from shutil import rmtree
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

 
load_dotenv()

# ===============================     Server Configuration      ==================================  #

MONGO_URI = os.getenv('MONGO_URI')

app = Flask(__name__, static_folder='static')
client = MongoClient(MONGO_URI)
db = client.get_database('VideoAnalyze')
dbPrompts = db['demo']

CORS(app)

mainDir='./static/Data'
defaultDir= './static/Data/blank.png'

tasks = {}


# ===============================             Routers           ==================================  #


@app.route('/')
def index():
    global mainDir, defaultDir
    cards=[]
    try:
        files = os.listdir('./static/Data/')
        dataCount= len(files)-1
        random_files = random.sample(files, 9) if dataCount > 8 else files
        if 'blank.png' in random_files:
            random_files.remove('blank.png')
        else: 
            random_files.pop()
        

        i = 0
        while i < len(random_files):
            topicData= random_files[i].split('.')[0]
            description='' #TODO
            outDir =f'{mainDir}/{random_files[i]}/output' 
            dir=f'{mainDir}/{random_files[i]}/frames/frames'
            frame=int(len(os.listdir(dir))/2)
            dir = f'{dir}/frame_{frame}.jpg' if frame > 0 else defaultDir
            topic = topicData if frame > 0 else 'Soon'
            description = description if frame > 0 else 'Soon'
            processing = False if any(os.scandir(outDir)) else True
            cards.append([dir, topic, description,processing])
            i+=1
        while i < 8:
            cards.append([defaultDir,'Soon', ''])
            i+=1
    except:
        return render_template('index.html', cards=[])
    return render_template('index.html', cards= cards ,pdf='./static/welcome/welcome.pdf',blankCard=defaultDir)

@app.route('/res' , methods=['GET'])
def res():
    global tasks
    video_name = request.args.get('videoname')
    if not video_name:
        return render_template('notFound.html')
    decodedName = decode64(video_name)

    if not decodedName:
        return render_template('notFound.html')
    
    if decodedName in tasks:
        det = tasks[decodedName].getResDetails()
        framesPath = f'./static/Data/{det['nameNdate']}/frames/frames/'
        return render_template('res.html',videoName=det['name'],objects=det['objects'],prompts =det['prompts'],pathOrigin=det['inDir'],pathDetected=det['outDir'],statistics=det['stats'],fps=det['fps'],framesPath=framesPath)
    
    data=getVideoDetails({"name":decodedName})

    if not data:
        return render_template('notFound.html')

    format= data['videoFormat']
    input_video_path = f'./static/Data/{decodedName}/input/{decodedName}.{format}'
    tagged_video_path = f'./static/Data/{decodedName}/output/tagged_{decodedName}.{format}'
    name =decodedName.split('_')[0]
    stats=data["statistics"]
    fps= data['fps']
    framesPath = f'./static/Data/{decodedName}/frames/frames/'

    return render_template('res.html', videoName=name, objects=data['promptDistinct'], pathOrigin=input_video_path, pathDetected=tagged_video_path, statistics=stats, fps=fps, framesPath=framesPath)

@app.route('/processing')
def processing():
    return render_template('processingDemo.html')

@app.route('/advanced')
def advanced():
    return render_template('advanced.html')

@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/search', methods=['GET'])
def search():
    result=[]
    query = request.args.get('q', '').lower()
    if not query:
        data = getPromptsDB({})
    else:
        data = getPromptsDB( {"promptDistinct" : query} )
        
    if not data:
        return render_template('emptySearch.html')

    values = {}
    objects=[]
    formats = []
    vid={}
    for res in data:
        outDir =f'./static/Data/{res['name']}/output' 
        vid['videoName'] = res['name'].split('_')[0]
        vid['fileName'] = res['name']
        frame=int(res['frameCount'])//2
        vid['frameSrc']= f"./static/Data/{res['name']}/frames/frames/frame_{frame}.jpg"
        vid['processing'] = False if any(os.scandir(outDir)) else True
        result.append(vid)
        objects = objects + res['promptDistinct']
        formats.append(res['videoFormat'])
        vid={}
    if not result:
        pipe=generateRegexObjectPipe(query)
        objectSuggest= getObjectFromAggregate(pipe)
        return render_template('search.html', status=404, message="Not Found", results=result, query=query,values={}, objectSuggest=objectSuggest)
    
    values["objects"] = list(set(objects))
    values["formats"] = list(set(formats))
    return render_template('search.html', status=200, message="Search Results", results=result, query=query,values=values)

@app.route('/searchWithFilters', methods=['POST'])
def searchWithFilters():
    query = {}
    data = request.get_json()
    orFilters = []
    andFilters= []


    if data['objects']:
        query['promptDistinct'] = { '$all': data['objects'] }
        for obj in data['objectFilters']:
            for filter,value in data['objectFilters'][obj].items():
                if filter == 'minSeq':
                    andFilters.append({"$expr": {"$gte": [{"$ifNull": [{"$divide": [{ "$toDouble": f"$statistics.object.{obj}.maxSequence.count" },{ "$toDouble": "$fps" }]},0]},float(value)]}})
                elif filter == 'ObjectInFrame':
                    pipe = generateObjectInFramePipe(obj,int(value))
                    andFilters.append({ "_id": { "$in": getIdFromAggregate(pipe) }})

    if data['formats']:  # More Pythonic way to check if the list is non-empty
        orFilters = [{ 'videoFormat': format } for format in data['formats']]  # Use list comprehension

    if data['#Objects']:
        andFilters.append({ "$expr": { "$gte": [{ "$size": "$promptDistinct" }, int(data['#Objects'][0])] } })

    if orFilters:
        query['$or'] = orFilters

    if andFilters:
        query['$and'] = andFilters
    

    queryRes = getPromptsDB(query)
    result=[]
    vid={}
    for res in queryRes:
        vid['videoName'] = res['name'].split('_')[0]
        vid['fileName'] = res['name']
        frame=int(res['frameCount'])//2
        vid['frameSrc']= f"./static/Data/{res['name']}/frames/frames/frame_{frame}.jpg"
        result.append(vid)
        vid={}
    if queryRes:
        return jsonify({'status': 200, 'data':result})
    else:
        return jsonify({'status': 404, 'data':[]})

@app.errorhandler(404)
def page_not_found(error):
    return render_template('notFound.html'), 404


# ===============================        DataBase Queries       ==================================  #

def getPromptsDB(query):
    data = dbPrompts.find(query)
    result = []
    for prompt in data:
        prompt.pop('_id', None)  # Remove the '_id' field
        result.append(prompt)
    return result

def getIdFromAggregate(pipe):
    result = list(dbPrompts.aggregate(pipe))
    ids = [doc['_id'] for doc in result]
    return ids

def getObjectFromAggregate(pipe):
    result = list(dbPrompts.aggregate(pipe))
    objs = [item for doc in result for item in doc['matchedObject']]
    return list(set(objs))

def generateRegexObjectPipe(obj):
    return [
    {
        "$match": {
        "promptDistinct": {
            "$elemMatch": {
            "$regex": f"{obj}?",
            "$options": "i"
            }
        }
        }
    },
    {
        "$project": {
        "matchedObject": {
            "$filter": {
            "input": "$promptDistinct",
            "as": "item",
            "cond": { "$regexMatch": { "input": "$$item", "regex": f"{obj}?", "options": "i" } }
            }
        }
        }
    }
    ]

def generateObjectInFramePipe(obj,val):
    return[
    {
        "$project": {
            "_id": 1,
            "maxObjCount": {
                "$max": {
                    "$map": {
                        "input": { "$objectToArray": "$statistics.frame.rawData" },
                        "as": "frame",
                        "in": {
                            "$cond": {
                                "if": { "$gt": [ { "$ifNull": [ f"$$frame.v.{obj}", 0 ] }, 0 ] },
                                "then": f"$$frame.v.{obj}",
                                "else": 0
                            }
                        }
                    }
                }
            }
        }
    },
    {
        "$match": {
            "maxObjCount": { "$gte": val }
        }
    },
    {
        "$project": {
            "_id": 1  # Only return the _id field
        }
    }
]

def getVideoDetails(query):
    data = dbPrompts.find_one(query)
    if data:
        data.pop('_id', None)  # Remove the '_id' field
    return data

def updateDBPrompt(item):
    return dbPrompts.insert_one(item).acknowledged

def searchHash(hash):
    data = dbPrompts.find_one({'hash256': hash}, {'name': 1})
    if data:
        return True, data['name']
    return False, ''


# ===============================        Helpers Functions      ==================================  #

def decode64(param):
    try:
        decode= base64.b64decode(param).decode('utf-8')
        return decode
    except:
        return False

if __name__ == '__main__':
    app.run()
