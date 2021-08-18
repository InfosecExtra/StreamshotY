import os
from uuid import uuid4

from minio import Minio
import pymongo
from bson.json_util import dumps
import json
# import pql

from flask import Flask, render_template, request, url_for, redirect

from redis import Redis
from rq import Queue

MINIO_SERVER = os.environ['MINIO_SERVER']
MINIO_ACCESS_KEY = os.environ['MINIO_ACCESS_KEY']
MINIO_SECRET_KEY = os.environ['MINIO_SECRET_KEY']
MINIO_BUCKET = os.environ['MINIO_BUCKET']

MONGODB_SERVER = os.environ['MONGODB_SERVER']
MONGODB_DATABASE = os.environ['MONGODB_DATABASE']
MONGODB_COLLECTION = os.environ['MONGODB_COLLECTION']

REDIS_SERVER = os.environ['REDIS_SERVER']

q = Queue(connection=Redis(REDIS_SERVER))

mongoclient = pymongo.MongoClient(MONGODB_SERVER)
mydb = mongoclient[MONGODB_DATABASE]
mycol = mydb[MONGODB_COLLECTION]

mycol.create_index([("$**",pymongo.TEXT)]) #create a text index so we can do our string searches

app = Flask(__name__)

def gettask(taskid): #get task results, except content
    query = { "taskid":taskid}
    out = mycol.find_one(query, {"content":0})
    if out != None:
        return out
    else:
        return False


def gettaskcontent(taskid): #get task results but only content
    query = { "taskid":taskid}
    out = mycol.find_one(query, {"content":1})
    if out != None:
        return out
    else:
        return False


def getrecent(): #get 10 recent tasks but only get url and task id
    out = mycol.find({"private": { "$ne": True }},{"url":1,"taskid":1}).sort("_id", pymongo.DESCENDING).limit(10)
    if out != None:
        return list(out)
    else:
        return False

def getrecent_live(): #get 10 recent tasks but only get url and task id
    out = mycol.find({"private": { "$ne": True }, "error": {"$exists": False}},{"url":1,"taskid":1}).sort("_id", pymongo.DESCENDING).limit(6) #for this we are looking for filed error not existing because this field is only made when theres an error ..... "only find fileds that dont have error"
    if out != None:
        return list(out)
    else:
        return False


def getstringsearch(stringsearch): #do a string search and return 25 recent results
    query = { "$text": { "$search": f"{stringsearch}" }, "private": { "$ne": True } }
    out = mycol.find(query,{"url":1,"taskid":1}).sort("_id", pymongo.DESCENDING).limit(25)
    if out != None:
        return list(out)
    else:
        return False


def getquerysearch(querystring): #do query for a specific field for equal to or not equal to, returns 25 recent results
    if " EQL " in querystring:
        field = querystring.split(" EQL ")[0]
        value = querystring.split(" EQL ")[1]
        query = { field: { "$regex": f"{value}", "$options": 'i'}, "private": { "$ne": True } }
    elif " NQL " in querystring:
        field = querystring.split(" NQL ")[0]
        value = querystring.split(" NQL ")[1]
        query = { field: { "$not": { "$regex": f"{value}", "$options": 'i'} }, "private": { "$ne": True } }
    else:
        return False
    print(query)
    out = mycol.find(query,{"url":1,"taskid":1}).sort("_id", pymongo.DESCENDING).limit(25)
    if out != None:
        return list(out)
    else:
        return False

# index page, this shows recent tasks
@app.route('/index')
@app.route('/',methods=['GET'])
def index():
    out = getrecent()
    if out == False:
        return render_template("index.html")
    else:
        return render_template("index.html", recenttasks = out)

# scan page, this lets you start a task
@app.route('/scan',methods=['GET', 'POST'])
def scan():
    if request.method == 'POST':
        if request.form['url']:
            url = request.form['url'].strip()
            if 'http://' in url[0:8].lower() or 'https://' in url[0:8].lower():
                taskid = str(uuid4())
                if request.form.get('private'):
                    q.enqueue('worker.screenshot',args=(taskid,url,True))
                else:
                    q.enqueue('worker.screenshot',args=(taskid,url,False))
                return redirect(url_for('results', taskid=taskid))
            else:
                return "Error: URL must contain http:// or https://"
        else:
            return "Error: No URL found"
    else:
        return render_template("scan.html")

# results page, it shows results
@app.route('/results/<taskid>',methods=['GET'])
def results(taskid):
    out = gettask(taskid)
    if out == False: # keep refreshing until the results are found
        return """<meta http-equiv="refresh" content="10">
        <h1>No Results found. Refreshing every 10 seconds</h1>"""
    else:
        return render_template("results.html", taskinfo = out)

# this only returns content. including on results page slowed down the browser...
@app.route('/content/<taskid>',methods=['GET'])
def content(taskid):
    out = gettaskcontent(taskid)
    if out == False:
        return """<meta http-equiv="refresh" content="10">
        <h1>No Results found. Refreshing every 10 seconds</h1>"""
    else:
        return render_template("content.html", content=out['content'])

# json results, no content
@app.route('/json/results/<taskid>',methods=['GET'])
def jsonresults(taskid):
    out = gettask(taskid)
    if out == False: # keep refreshing until the results are found
        return "false"
    else:
        return json.loads(dumps(out))

# json reuslts, only content
@app.route('/json/content/<taskid>',methods=['GET'])
def jsoncontent(taskid):
    out = gettaskcontent(taskid)
    if out == False:
        return "false"
    else:
        return json.loads(dumps(out))

# this is for searching, it can either do string search or query with EQL or NQL
@app.route('/search',methods=['GET'])
def search():
    if request.args.get('stringsearch'):
        out = getstringsearch(request.args.get('stringsearch'))
        if out == False:
            return render_template("search.html")
        else:
            return render_template("search.html", results = out, query=request.args.get('stringsearch'))
    elif request.args.get('query'):
        out = getquerysearch(request.args.get('query'))
        if out == False:
            return render_template("search.html")
        else:
            return render_template("search.html", results = out, query=request.args.get('query'))
    else:
        return render_template("search.html")

# live page, this shows recent tasks
@app.route('/live')
def live():
    out = getrecent_live()
    if out == False:
        return render_template("live.html")
    else:
        return render_template("live.html", recenttasks = out)

if __name__ == '__main__':
    app.run(debug=False)
