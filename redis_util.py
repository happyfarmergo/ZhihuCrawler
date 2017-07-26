import redis

'''
RedisUtil实际上合并了Redis Set和Redis List的操作
'''
class RedisUtil:
    def __init__(self, host, port, namespace):
        self.__connection_pool = redis.ConnectionPool(host=host, port=port)
        self.__db = redis.Redis(connection_pool=self.__connection_pool)
        self.__key = namespace
        self.__pipeline = None

    def begin_pipeline(self):
        assert self.__pipeline is None
        self.__pipeline = self.__db.pipeline(transaction=True)

    def end_pipeline(self):
        self.__pipeline.execute()
        self.__pipeline = None

    def sadd_items(self, setname, *items):
        self.__db.sadd(setname, *items)

    def sismem(self, setname, item):
        return self.__db.sismember(setname, item)

    def ssize(self, setname):
        return self.__db.scard(setname)

    def empty(self, name):
        name = self.__key + ':%s' % name
        return self.__db.llen(name) == 0

    def get(self, name):
        name = self.__key + ':%s' % name
        user = self.__db.lpop(name)
        return user if user else None

    def put(self, name, *items):
        name = self.__key + ':%s' % name
        self.__db.rpush(name, *items)

