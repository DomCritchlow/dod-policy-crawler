# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import pymongo

from scrapy.exceptions import DropItem
import logging


class DodpolicycrawlerPipeline:
    def process_item(self, item, spider):
        return item


class MongoDBPipeline(object):

    def __init__(self):
        connection = pymongo.MongoClient(
            os.environ['MONGODB_URI'],
            username=os.environ['MONGO_INITDB_ROOT_USERNAME'],
            password=os.environ['MONGO_INITDB_ROOT_PASSWORD'],
            authMechanism=os.environ['MONGO_INITDB_AUTHMECH']
        )
        db = connection[os.environ['MONGODB_DB']]
        self.collection = db[os.environ['MONGODB_COLLECTION']]

    def process_item(self, item, spider):
        valid = True
        for data in item:
            if not data:
                valid = False
                raise DropItem("Missing {0}!".format(data))
        if valid:
            item['_id']=item['version_hash']
            item['_needs_download'] = True
            if self.collection.count_documents({"_id":item["_id"]},limit=1):
                logging.debug("Record already exists!")
                return None
            self.collection.insert_one(dict(item))
            logging.debug("Created a new record of policy!")
        return item