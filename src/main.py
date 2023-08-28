from fastapi import FastAPI, BackgroundTasks
import os 
import subprocess
import uuid
import pymongo
from datetime import datetime
from scrapy import spiderloader
from scrapy.utils.project import get_project_settings

app = FastAPI()

def connect(collection):

    connection = pymongo.MongoClient(
            os.environ['MONGODB_URI'],
            username=os.environ['MONGO_SCRAPY_USERNAME'],
            password=os.environ['MONGO_SCRAPY_PASSWORD'],
            authMechanism=os.environ['MONGO_SCRAPY_AUTHMECH']
        )
    db = connection[os.environ['MONGODB_DB']]
    collection = db[collection]
    return collection, connection

def get_download_count():
    collection, connection = connect(os.environ['MONGODB_COLLECTION'])

    count = collection.count_documents({"_needs_download": True})
    connection.close()
    return count

def update_task(task_id):
    collection, connection = connect(os.environ['MONGODB_COLLECTION_TASKS'])

    find_id = { "_id": task_id}
    update_values = { "$set": { "progress": "COMPLETE", "completion":datetime.now() } }
    collection.update_one(find_id, update_values)
    connection.close()

    return "COMPLETE"

def create_crawler_task(crawler_name: str):

    task_id = str(uuid.uuid4())
    item = {"_id":task_id,
            "progress":"IN PROGRESS", 
            "start_time": datetime.now(),
            "completion": None, 
            "task":"crawler", 
            "name":crawler_name
            }
    collection, connection = connect(os.environ['MONGODB_COLLECTION_TASKS'])
    collection.insert_one(dict(item))
    connection.close()

    return task_id

async def start_crawler(crawler_name: str, task_id: str):

    #subprocess.run(['python','run_spider.py',crawler_name])

    process = subprocess.Popen(['python','run_spider.py',crawler_name])
    process.wait()
    status = update_task(task_id)

    return status

def list_crawler_names():
    settings = get_project_settings()
    spider_loader = spiderloader.SpiderLoader.from_settings(settings)
    spiders = spider_loader.list()
    return spiders

def crawler_name_exists(crawler_name: str):
    if crawler_name in list_crawlers():
        return True
    else:
        return False

@app.get("/")
def read_root():
    return {"API endpoints to engage with scripts for crawlers"}

@app.post("/crawl/{crawler_name}")
async def start_specific_crawler(crawler_name: str, background_tasks: BackgroundTasks):
    if crawler_name_exists(crawler_name):
        task_id = create_crawler_task(crawler_name)
        background_tasks.add_task(start_crawler, crawler_name, task_id)
        return task_id
    else:
        return "No task found"

@app.get("/listcrawlers")
def list_crawlers():
    return list_crawler_names()

@app.get("/crawlerexists/{crawler_name}")
def crawler_exists(crawler_name):
    return crawler_name_exists(crawler_name)

@app.get("/downloadneeded/count")
def downloadneeded_count():
    return {"count": get_download_count()}

@app.post("/initiatedownload")
def initiatedownload():

    return {"not implemented yet"}