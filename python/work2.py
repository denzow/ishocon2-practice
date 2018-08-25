import os
from concurrent import futures
import redis
import urllib
import time
import pickle
from hashlib import md5
import urllib.parse
import MySQLdb.cursors

"""
users をquotedに

"""
_config = {
    'db_host': os.environ.get('ISHOCON2_DB_HOST', 'localhost'),
    'db_port': int(os.environ.get('ISHOCON2_DB_PORT', '3306')),
    'db_username': os.environ.get('ISHOCON2_DB_USER', 'ishocon'),
    'db_password': os.environ.get('ISHOCON2_DB_PASSWORD', 'ishocon'),
    'db_database': os.environ.get('ISHOCON2_DB_NAME', 'ishocon2'),
}

pool2 = redis.ConnectionPool(host='localhost', port=6379, db=1)
r = redis.StrictRedis(connection_pool=pool2)

def config(key):
    if key in _config:
        return _config[key]
    else:
        raise "config value of %s undefined" % key

def get_conn():
    db = MySQLdb.connect(**{
        'host': config('db_host'),
        'port': config('db_port'),
        'user': config('db_username'),
        'passwd': config('db_password'),
        'db': config('db_database'),
        'charset': 'utf8mb4',
        'cursorclass': MySQLdb.cursors.DictCursor,
        'autocommit': False,
    })
    cur = db.cursor()
    cur.execute("SET SESSION sql_mode='TRADITIONAL,NO_AUTO_VALUE_ON_ZERO,ONLY_FULL_GROUP_BY'")
    cur.execute('SET NAMES utf8mb4')
    return db


def cache(users):
    pipe = r.pipeline()
    for user in users:
        pipe.set(md5('{}{}{}'.format(
            user['mynumber'], user['name'], user['address']
        ).encode('utf-8')).hexdigest(), '{}:{}'.format(user['id'], user['votes']))
    pipe.execute()
    return True

conn = get_conn()
cur = conn.cursor()
# 4000000
# 800000
# 1600000
# 2400000
# 3200000
# 4000000

#cur.execute('select *  FROM users where id >= 0 and id < 800000')
#cur.execute('select *  FROM users where id >= 800000 and id < 1600000')
#cur.execute('select *  FROM users where id >= 1600000 and id < 2400000')
#cur.execute('select *  FROM users where id >= 2400000 and id < 3200000')
#cur.execute('select *  FROM users where id >= 3200000 and id <= 4000000')

BUFFER = []
TASK_LIST = []
count = 0

begin_id = 0
while begin_id <= 4000000:
    cur.execute('select *  FROM users where id between %s and %s', (begin_id, begin_id + 800000))
    for row in cur:
        BUFFER.append(row)
        if len(BUFFER) > 10000:
            count += 1
            print('execute', count)
            cache(BUFFER)
            BUFFER = []
    begin_id += 800000
# for future in futures.as_completed(TASK_LIST):
#     print('commit')
#     subconn = future.result()

cache(BUFFER)

