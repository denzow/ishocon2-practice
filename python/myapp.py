import redis

from collections import Counter
from functools import lru_cache
from hashlib import md5
import os
import uwsgi
import pickle
import pathlib
from urllib.parse import unquote_plus

import constants

from flask import Flask, redirect, render_template, request

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

pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.StrictRedis(connection_pool=pool)

pool2 = redis.ConnectionPool(host='localhost', port=6379, db=1)
r2 = redis.StrictRedis(connection_pool=pool2)


def config(key):
    if key in _config:
        return _config[key]
    else:
        raise "config value of %s undefined" % key


def get_election_results():
    result = []
    for candidate_id, data in constants.CANDIDATES_MASTER.items():
        data['count'] = get_vote_count_cache_by_candidate_id(candidate_id)
        result.append(data)

    result.sort(key=lambda x: x['count'], reverse=True)
    return result


def get_voice_of_supporter_by_id(candidate_id):
    """
    {keyword1: 100, keyword2: 200}
    """
    keyword_cache = Counter(get_vote_keyword_count_cache_by_candidate_id(candidate_id))
    result = [unquote_cached(r[0]) for r in keyword_cache.most_common(10)]
    return result


def get_voice_of_supporter(candidate_ids):
    total_keywords = Counter()
    for candidate_id in candidate_ids:
        total_keywords.update(get_vote_keyword_count_cache_by_candidate_id(candidate_id))

    return [unquote_cached(r[0]) for r in total_keywords.most_common(10)]


def get_all_party_name():
    return list(constants.PARTY_MASTER.keys())


def get_candidate_by_id(candidate_id):
    return constants.CANDIDATES_MASTER.get(candidate_id, None)


def db_initialize():
    pass


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
    html = render_template('index.html',
                           candidates=candidates,
                           parties=parties,
                           sex_ratio=sex_ratio)

    return html

@app.route('/candidates/<int:candidate_id>')
def get_candidate(candidate_id):
    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        return redirect('/')
    votes = get_vote_count_cache_by_candidate_id(candidate_id)
    keywords = get_voice_of_supporter_by_id(candidate_id)
    return render_template('candidate.html',
                           candidate=candidate,
                           votes=votes,
                           keywords=keywords)


@app.route('/political_parties/<string:name>')
def get_political_party(name):
    votes = 0
    for r in get_election_results():
        if r['political_party'] == name:
            votes += r['count'] or 0

#    cur.execute('SELECT * FROM candidates WHERE political_party = "{}"'.format(name))
    candidate_ids = constants.PARTY_MASTER.get(name)
    candidates = [get_candidate_by_id(candidate_id) for candidate_id in candidate_ids]
    keywords = get_voice_of_supporter(candidate_ids)
    return render_template('political_party.html',
                           political_party=name,
                           votes=votes,
                           candidates=candidates,
                           keywords=keywords)


@app.route('/vote')
def get_vote():
    return constants.VOTE_HTML


@app.route('/vote', methods=['POST'])
def post_vote():
    raw_params = request._get_stream_for_parsing().read().decode('utf-8').split('&')
    form_base = {x.split('=')[0]: x.split('=')[1] for x in raw_params}
    data = (form_base['mynumber'], form_base['name'], form_base['address'])
    cache = get_user_cache(*data)
    if cache:
        user_id, user_votes = cache
    else:
        user_id, user_votes = (None, None)

    candidate_id = get_candidate_id_by_name(form_base['candidate'])
    voted_count = 0
    if user_id:
        voted_count = get_voted_count_cache(user_id)
    if not user_id:
        return constants.VOTE_FAIL1_HTML
    elif user_votes < (int(form_base['vote_count']) + voted_count):
        return constants.VOTE_FAIL2_HTML
    elif not form_base['candidate']:
        return constants.VOTE_FAIL3_HTML
    elif not candidate_id:
        return constants.VOTE_FAIL4_HTML
    elif not form_base['keyword']:
        return constants.VOTE_FAIL5_HTML

    vote_count = int(form_base['vote_count'])
    set_vote_count_cache_by_candidate_id(candidate_id, vote_count)
    set_vote_keyword_count_cache_by_candidate_id(candidate_id, form_base['keyword'],  vote_count)
    set_voted_count_cache(user_id, vote_count)

    return constants.VOTE_SUCCESS_HTML


@app.route('/initialize')
def get_initialize():
    db_initialize()
    r.flushdb()
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


def set_voted_count_cache(user_id, voted_count):
    key_name = 'voted_{}'.format(user_id)
    set_cache(key_name, get_cache(key_name, 0) + voted_count)


def get_voted_count_cache(user_id):
    key_name = 'voted_{}'.format(user_id)
    return get_cache(key_name, 0)


def set_vote_count_cache_by_candidate_id(candidate_id, voted_count):
    key_name = md5('cv_{}'.format(
        candidate_id,
    ).encode('utf-8')).hexdigest()
    set_cache(key_name, get_cache(key_name, 0) + voted_count)


def get_vote_count_cache_by_candidate_id(candidate_id):
    key_name = md5('cv_{}'.format(
        candidate_id,
    ).encode('utf-8')).hexdigest()
    return get_cache(key_name, 0)


def set_vote_keyword_count_cache_by_candidate_id(candidate_id, keyword, vote_count):
    key_name = 'ckv_{}_{}'.format(
        candidate_id, keyword
    )
    r.incr(key_name, vote_count)


def get_vote_keyword_count_cache_by_candidate_id(candidate_id):
    key_name = 'ckv_{}_*'.format(candidate_id)
    result = {}
    for key in r.keys(key_name):
        keyword = key.decode('utf-8').split('_')[2]
        result[keyword] = int(r.get(key))

    return result


def get_vote_buffer_len():
    return uwsgi.queue_size()


def get_user_cache(mynumber, name, address):
    key_name = md5('{}{}{}'.format(
        mynumber, name, address
    ).encode('utf-8')).hexdigest()
    cache = r2.get(key_name)
    if cache:
        user_id, votes = cache.decode('utf-8').split(':')
        return int(user_id), int(votes)
    return None


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


if __name__ == "__main__":
    app.run()
