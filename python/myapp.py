import datetime

from functools import lru_cache
import os
import uwsgi
import pickle
import pathlib
from urllib.parse import unquote_plus

import MySQLdb.cursors
import constants

from flask import Flask, abort, redirect, render_template, request, session

static_folder = pathlib.Path(__file__).resolve().parent / 'public'
app = Flask(__name__, static_folder=str(static_folder), static_url_path='')

app.secret_key = os.environ.get('ISHOCON2_SESSION_SECRET', 'showwin_happy')

_config = {
    'db_host': os.environ.get('ISHOCON2_DB_HOST', 'localhost'),
    'db_port': int(os.environ.get('ISHOCON2_DB_PORT', '3306')),
    'db_username': os.environ.get('ISHOCON2_DB_USER', 'ishocon'),
    'db_password': os.environ.get('ISHOCON2_DB_PASSWORD', 'ishocon'),
    'db_database': os.environ.get('ISHOCON2_DB_NAME', 'ishocon2'),
}


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
        'autocommit': True,
    })
    cur = db.cursor()
    cur.execute("SET SESSION sql_mode='TRADITIONAL,NO_AUTO_VALUE_ON_ZERO,ONLY_FULL_GROUP_BY'")
    cur.execute('SET NAMES utf8mb4')
    return db


DB_POOL = [get_conn() for _ in range(3)]


def db():
    if hasattr(request, 'db'):
        return request.db
    else:
        request.db = DB_POOL.pop()
        return request.db


@app.teardown_request
def teardown(exception=None):
    if hasattr(request, 'db'):
        DB_POOL.append(request.db)
        delattr(request, 'db')


def get_election_results():
    cur = db().cursor()
    cur.execute("""
SELECT c.id, c.name, c.political_party, c.sex, v.count
FROM candidates AS c
LEFT OUTER JOIN
  (SELECT candidate_id, sum(vote_count) AS count
  FROM votes
  GROUP BY candidate_id) AS v
ON c.id = v.candidate_id
ORDER BY v.count DESC
""")
    return cur.fetchall()


def get_voice_of_supporter(candidate_ids):
    cur = db().cursor()
    candidate_ids_str = ','.join([str(cid) for cid in candidate_ids])
    cur.execute("""
SELECT keyword
FROM votes
WHERE candidate_id IN ({})
GROUP BY keyword
ORDER BY sum(vote_count) DESC
LIMIT 10
""".format(candidate_ids_str))
    records = cur.fetchall()
    return [unquote_cached(r['keyword']) for r in records]


def get_all_party_name():
    return list(constants.PARTY_MASTER.keys())


def get_candidate_by_id(candidate_id):
    return constants.CANDIDATES_MASTER.get(candidate_id, None)


def db_initialize():
    cur = db().cursor()
    cur.execute('DELETE FROM votes')


@app.route('/')
def get_index():
    candidates = []
    election_results = get_election_results()
    # 上位10人と最下位のみ表示
    candidates += election_results[:10]
    candidates.append(election_results[-1])

    parties_name = get_all_party_name()
    parties = {}
    for name in parties_name:
        parties[name] = 0
    for r in election_results:
        parties[r['political_party']] += r['count'] or 0
    parties = sorted(parties.items(), key=lambda x: x[1], reverse=True)

    sex_ratio = {'men': 0, 'women': 0}
    for r in election_results:
        if r['sex'] == '男':
            sex_ratio['men'] += r['count'] or 0
        elif r['sex'] == '女':
            sex_ratio['women'] += r['count'] or 0

    return render_template('index.html',
                           candidates=candidates,
                           parties=parties,
                           sex_ratio=sex_ratio)


@app.route('/candidates/<int:candidate_id>')
def get_candidate(candidate_id):
    cur = db().cursor()
    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        return redirect('/')

    cur.execute('SELECT sum(vote_count) AS count FROM votes WHERE candidate_id = {}'.format(candidate_id))
    votes = cur.fetchone()['count']
    keywords = get_voice_of_supporter([candidate_id])
    return render_template('candidate.html',
                           candidate=candidate,
                           votes=votes,
                           keywords=keywords)


@app.route('/political_parties/<string:name>')
def get_political_party(name):
    cur = db().cursor()
    votes = 0
    for r in get_election_results():
        if r['political_party'] == name:
            votes += r['count'] or 0

    cur.execute('SELECT * FROM candidates WHERE political_party = "{}"'.format(name))
    candidates = cur.fetchall()
    candidate_ids = [c['id'] for c in candidates]
    keywords = get_voice_of_supporter(candidate_ids)
    return render_template('political_party.html',
                           political_party=name,
                           votes=votes,
                           candidates=candidates,
                           keywords=keywords)


@app.route('/vote')
def get_vote():
    cur = db().cursor()
    cur.execute('SELECT * FROM candidates')
    candidates = cur.fetchall()
    return render_template('vote.html',
                           candidates=candidates,
                           message='')


@app.route('/vote', methods=['POST'])
def post_vote():
    cur = db().cursor()
    raw_params = request._get_stream_for_parsing().read().decode('utf-8').split('&')
    #form_base = {x.split('=')[0]: unquote_plus(x.split('=')[1]) for x in raw_params}
    form_base = {x.split('=')[0]: x.split('=')[1] for x in raw_params}
    cur.execute('SELECT id, votes FROM users WHERE mynumber = %s AND name = %s AND address = %s', (
        form_base['mynumber'], form_base['name'], form_base['address']
    ))
    user = cur.fetchone()
    candidate_id = get_candidate_id_by_name(form_base['candidate'])
    voted_count = 0
    if user:
        voted_count = get_voted_count_cache(user['id'])
        # cur.execute('SELECT sum(vote_count) AS count FROM votes WHERE user_id = %s', (user['id'],))
        # voted_count = cur.fetchone()['count']
        # if not voted_count:
        #     voted_count = 0
    if not user:
        return constants.VOTE_FAIL1_HTML
    elif user['votes'] < (int(form_base['vote_count']) + voted_count):
        return constants.VOTE_FAIL2_HTML
    elif not form_base['candidate']:
        return constants.VOTE_FAIL3_HTML
    elif not candidate_id:
        return constants.VOTE_FAIL4_HTML
    elif not form_base['keyword']:
        return constants.VOTE_FAIL5_HTML

    data = (user['id'], candidate_id, form_base['keyword'], int(form_base['vote_count']))
    cur.execute('INSERT INTO votes (user_id, candidate_id, keyword, vote_count) VALUES (%s, %s, %s, %s)', data)

    set_voted_count_cache(user['id'], int(form_base['vote_count']))
    return constants.VOTE_SUCCESS_HTML


@app.route('/initialize')
def get_initialize():
    db_initialize()
    return ''


def get_candidate_id_by_name(name):
    return constants.QUOTED_CANDIDATES.get(name, None)


def set_cache(key, val):
    if not uwsgi.cache_exists(key):
        uwsgi.cache_set(key, pickle.dumps(val))
    else:
        uwsgi.cache_update(key, pickle.dumps(val))


def get_cache(key, default=None):
    try:
        return pickle.loads(uwsgi.cache_get(key))
    except:
        return default


def get_voted_count_cache(user_id):
    key_name = 'voted_{}'.format(user_id)
    return get_cache(key_name, 0)


def set_voted_count_cache(user_id, voted_count):
    key_name = 'voted_{}'.format(user_id)
    set_cache(key_name, get_cache(key_name, 0) + voted_count)



def add_vote_buffer(data):
    uwsgi.queue_push(pickle.dumps(data))


def get_all_vote_buffer():
    result = []
    for queue in uwsgi.queue_pop():
        if not queue:
            break
        result.append(pickle.loads(queue))
    return result


def get_vote_buffer_len():
    return uwsgi.queue_size()


@lru_cache(maxsize=100)
def unquote_cached(keyword):
    return unquote_plus(keyword)


from wsgi_lineprof.filters import FilenameFilter
from wsgi_lineprof.middleware import LineProfilerMiddleware
f = open("/run/mylog/profile.log", "a")  # 複数ワーカが書き込むので多分wじゃだめな気がする。
filters = [
    FilenameFilter('myapp.py'),  # プロファイル対象のファイル名指定
]
# stremで出力ファイルを指定、filtersでフィルタを追加
app_profile = LineProfilerMiddleware(app, stream=f, filters=filters, async_stream=True)


#uwsgi.queue_push("Hello, uWSGI stack!")
# Pop it back
#print(uwsgi.queue_last(10))

if __name__ == "__main__":
    app.run()
