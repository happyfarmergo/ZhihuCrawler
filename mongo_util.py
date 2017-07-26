from pymongo import MongoClient


class Mongo:
    def __init__(self, database):
        self.db = MongoClient(host='127.0.0.1', port=27017).get_database(name=database)

    def __repr__(self):
        print(self.db.server_info())

    def save_user(self, userinfo):
        self.db.user.insert(userinfo)

    def save_comments(self, comments):
        if len(comments) == 0:
            return
        self.db.comment.insert_many(comments)

    def set_song(self, sid, attrs):
        self.db.song.update_one({'id': sid}, {'$set' : attrs})

    def save_playlist(self, list):
        self.db.playlist.insert(list)

    def save_songs(self, songs):
        if len(songs) == 0:
            return
        self.db.song.insert_many(songs)