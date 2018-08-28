from collections import Counter, defaultdict
from functools import lru_cache
from hashlib import md5
import os
from urllib.parse import unquote_plus
import asyncio

import constants
import jinja2
import jinja2_sanic
from sanic import Sanic, response
from sanic.response import HTTPResponse, text
from aioredis import create_redis_pool


app = Sanic(__name__)
app.config.KEEP_ALIVE_TIMEOUT = 75

app.secret_key = os.environ.get('ISHOCON2_SESSION_SECRET', 'showwin_happy')

jinja2_sanic.setup(
    app,
    loader=jinja2.FileSystemLoader('./templates', encoding='utf8')
)
render_template = jinja2_sanic.render_template
render_string = jinja2_sanic.render_string


"""
    text = render_string(template_name, request, context, app_key=app_key)
    content_type = "text/html; charset={encoding}".format(encoding=encoding)

    return HTTPResponse(
        text, status=status, headers=headers,
        content_type=content_type
    )
"""

@app.listener('before_server_start')
async def aio_redis_configure(_app, loop):
    _app.redis1 = await create_redis_pool(loop=loop, **{
        'address': ('127.0.0.1', 6379),
        'db': 0,
    })
    _app.redis2 = await create_redis_pool(loop=loop, **{
        'address': ('127.0.0.1', 6379),
        'db': 1,
    })


@app.listener('after_server_stop')
async def close_redis(_app, _loop):
    _app.redis1.close()
    _app.redis2.close()

    await _app.redis1.wait_closed()
    await _app.redis2.wait_closed()


async def get_election_results():
    result = []
    for candidate_id, data in constants.CANDIDATES_MASTER.items():
        data['count'] = await get_vote_count_cache_by_candidate_id(candidate_id)
        result.append(data)

    result.sort(key=lambda x: x['count'], reverse=True)
    return result


async def get_voice_of_supporter_by_id(candidate_id):
    """
    {keyword1: 100, keyword2: 200}
    """
    return [unquote_cached(r[0]) for r in await get_vote_keyword_count_cache_by_candidate_id_top_10(candidate_id)]


async def get_voice_of_supporter(candidate_ids):
    total_keywords = Counter()
    for candidate_id in candidate_ids:
        total_keywords += await get_vote_keyword_count_cache_by_candidate_id(candidate_id)

    return [unquote_cached(r[0]) for r in total_keywords.most_common(10)]


def get_all_party_name():
    return list(constants.PARTY_MASTER.keys())


def get_candidate_by_id(candidate_id):
    return constants.CANDIDATES_MASTER.get(candidate_id, None)


def db_initialize():
    pass


@app.route('/')
async def get_index(request):
    html = await get_index_cache()
    if not html:
        candidates = []
        election_results = await get_election_results()
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
        html = render_string(
            'index.html',
            request,
            context=dict(
                candidates=candidates,
                parties=parties,
                sex_ratio=sex_ratio
            )
        )
        await set_index_cache(html)

    return HTTPResponse(
        html,
        status=200,
        content_type="text/html; charset=utf-8",
    )


@app.route('/candidates/<candidate_id:int>')
async def get_candidate(request, candidate_id):
    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        return response.redirect('/')
    html = await get_candidate_cache(candidate_id)
    if not html:
        votes = await get_vote_count_cache_by_candidate_id(candidate_id)
        keywords = await get_voice_of_supporter_by_id(candidate_id)
        html = render_string(
            'candidate.html',
            request,
            context=dict(
                candidate=candidate,
                votes=votes,
                keywords=keywords,
            )
        )
        await set_candidate_cache(candidate_id, html)
    return HTTPResponse(
        html,
        status=200,
        content_type="text/html; charset=utf-8",
    )


@app.route('/political_parties/<name>')
async def get_political_party(request, name):
    votes = 0
    name = constants.QUOTED_PARTY_MAP.get(name)
    html = await get_party_cache(name)
    if not html:
        for r in await get_election_results():
            if r['political_party'] == name:
                votes += r['count'] or 0
    #    cur.execute('SELECT * FROM candidates WHERE political_party = "{}"'.format(name))
        candidate_ids = constants.PARTY_MASTER.get(name)
        candidates = [get_candidate_by_id(candidate_id) for candidate_id in candidate_ids]
        keywords = await get_voice_of_supporter(candidate_ids)
        html = render_string(
            'political_party.html',
            request,
            context=dict(
                political_party=name,
                votes=votes,
                candidates=candidates,
                keywords=keywords
            )
        )
        await set_party_cache(name, html)

    return HTTPResponse(
        html,
        status=200,
        content_type="text/html; charset=utf-8",
    )


@app.route('/vote')
async def get_vote(request):
    return text(constants.VOTE_HTML)

@app.route('/vote', methods=['POST'])
async def post_vote(request):
    raw_params = request.body.decode('utf-8').split('&')
    form_base = {x.split('=')[0]: x.split('=')[1] for x in raw_params}
    data = (form_base['mynumber'], form_base['name'], form_base['address'])
    cache = await get_user_cache(*data)
    if cache:
        user_id, user_votes = cache
    else:
        user_id, user_votes = (None, None)

    candidate_id = get_candidate_id_by_name(form_base['candidate'])
    voted_count = 0
    if user_id:
        voted_count = await get_voted_count_cache_by_user_id(user_id)
    if not user_id:
        return text(constants.VOTE_FAIL1_HTML)
    elif user_votes < (int(form_base['vote_count']) + voted_count):
        return text(constants.VOTE_FAIL2_HTML)
    elif not form_base['candidate']:
        return text(constants.VOTE_FAIL3_HTML)
    elif not candidate_id:
        return text(constants.VOTE_FAIL4_HTML)
    elif not form_base['keyword']:
        return text(constants.VOTE_FAIL5_HTML)

    vote_count = int(form_base['vote_count'])
    asyncio.gather(
        set_vote_count_cache_by_candidate_id(candidate_id, vote_count),
        set_vote_keyword_count_cache_by_candidate_id(candidate_id, form_base['keyword'], vote_count),
        set_voted_count_cache_by_user_id(user_id, vote_count),
        incr_vote_counter(),
    )
    return text(constants.VOTE_SUCCESS_HTML)


@app.route('/initialize')
async def get_initialize(request):
    db_initialize()
    global VOTE_CACHE, VOTE_COUNT_CACHE, VOTE_KEYWORD_CACHE, HTML_CACHE, VOTE_COUNTER
    VOTE_CACHE = defaultdict(int)
    VOTE_COUNT_CACHE = defaultdict(int)
    VOTE_KEYWORD_CACHE = defaultdict(Counter)
    HTML_CACHE = {}
    VOTE_COUNTER = 0
    return HTTPResponse()


def myint(base, defalut=0):
    if base:
        return int(base)
    return defalut

def mydecode(base, defalut=None):
    if base:
        return base.decode('utf-8')
    return defalut


def get_candidate_id_by_name(name):
    return constants.QUOTED_CANDIDATES.get(name, None)


# caches
VOTE_CACHE = defaultdict(int)
VOTE_COUNT_CACHE = defaultdict(int)
VOTE_KEYWORD_CACHE = defaultdict(Counter)
HTML_CACHE = {}
VOTE_COUNTER = 0
async def incr_vote_counter():
    global VOTE_COUNTER
    VOTE_COUNTER += 1


async def set_voted_count_cache_by_user_id(user_id, voted_count):
    VOTE_CACHE[user_id] += voted_count


async def get_voted_count_cache_by_user_id(user_id):
    return VOTE_CACHE[user_id]


async def set_vote_count_cache_by_candidate_id(candidate_id, voted_count):
    VOTE_COUNT_CACHE[candidate_id] += voted_count


async def get_vote_count_cache_by_candidate_id(candidate_id):
    return VOTE_COUNT_CACHE[candidate_id]


async def set_vote_keyword_count_cache_by_candidate_id(candidate_id, keyword, vote_count):
    VOTE_KEYWORD_CACHE[candidate_id][keyword] += vote_count


async def get_vote_keyword_count_cache_by_candidate_id(candidate_id):
    return VOTE_KEYWORD_CACHE[candidate_id]


async def get_vote_keyword_count_cache_by_candidate_id_top_10(candidate_id):
    return VOTE_KEYWORD_CACHE[candidate_id].most_common(10)


async def get_user_cache(mynumber, name, address):
    key_name = md5('{}{}{}'.format(
        mynumber, name, address
    ).encode('utf-8')).hexdigest()
    cache = await app.redis2.get(key_name)
    if cache:
        user_id, votes = cache.decode('utf-8').split(':')
        return int(user_id), int(votes)
    return None


async def set_index_cache(html):
    HTML_CACHE['index_{}'.format(VOTE_COUNTER)] = html


async def get_index_cache():
    return HTML_CACHE.get('index_{}'.format(VOTE_COUNTER))


async def set_party_cache(name, html):
    HTML_CACHE['party_{}{}'.format(name, VOTE_COUNTER)] = html


async def get_party_cache(name):
    return HTML_CACHE.get('party_{}{}'.format(name, VOTE_COUNTER))


async def set_candidate_cache(candidate_id, html):
    HTML_CACHE['candidate_{}_{}'.format(candidate_id, VOTE_COUNTER)] = html


async def get_candidate_cache(candidate_id):
    return HTML_CACHE.get('candidate_{}_{}'.format(candidate_id, VOTE_COUNTER))


@lru_cache(maxsize=100)
def unquote_cached(keyword):
    return unquote_plus(keyword)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, workers=1, access_log=False)
