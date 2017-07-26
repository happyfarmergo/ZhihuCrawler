from pymongo import MongoClient


class Mongo:
    def __init__(self, database):
        self.db = MongoClient(host='127.0.0.1', port=27017).get_database(name=database)

    def __repr__(self):
        print(self.db.server_info())

    def save_user(self, userinfo):
        self.db.user.insert(userinfo)
