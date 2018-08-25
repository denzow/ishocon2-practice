VOTE_BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html" charset="utf-8">
<link rel="stylesheet" href="/css/bootstrap.min.css">
<title>ISUCON選挙結果</title>
</head>
<body>
<nav class="navbar navbar-inverse navbar-fixed-top">
<div class="container">
<div class="navbar-header">
<a class="navbar-brand" href="/">ISUCON選挙結果</a>
</div>
<div class="header clearfix">
<nav>
<ul class="nav nav-pills pull-right">
<li role="presentation"><a href="/vote">投票する</a></li>
</ul>
</nav>
</div>
</div>
</nav>
<div class="jumbotron">
<div class="container">
<h1>清き一票をお願いします！！！</h1>
</div>
</div>
<div class="container">
<div class="row">
<div class="col-md-6 col-md-offset-3">
<div class="login-panel panel panel-default">
<div class="panel-heading">
<h3 class="panel-title">投票フォーム</h3>
</div>
<div class="panel-body">
<form method="POST" action="/vote">
<fieldset>
<label>氏名</label>
<div class="form-group">
<input class="form-control" name="name" autofocus>
</div>
<label>住所</label>
<div class="form-group">
<input class="form-control" name="address" value="">
</div>
<label>私の番号</label>
<div class="form-group">
<input class="form-control" name="mynumber" value="">
</div>
<label>候補者</label>
<div class="form-group">
<select name="candidate">
<option value="伊藤 一郎">伊藤 一郎</option>
<option value="伊藤 三郎">伊藤 三郎</option>
<option value="伊藤 五郎">伊藤 五郎</option>
<option value="伊藤 四郎">伊藤 四郎</option>
<option value="伊藤 次郎">伊藤 次郎</option>
<option value="佐藤 一郎">佐藤 一郎</option>
<option value="佐藤 三郎">佐藤 三郎</option>
<option value="佐藤 五郎">佐藤 五郎</option>
<option value="佐藤 四郎">佐藤 四郎</option>
<option value="佐藤 次郎">佐藤 次郎</option>
<option value="渡辺 一郎">渡辺 一郎</option>
<option value="渡辺 三郎">渡辺 三郎</option>
<option value="渡辺 五郎">渡辺 五郎</option>
<option value="渡辺 四郎">渡辺 四郎</option>
<option value="渡辺 次郎">渡辺 次郎</option>
<option value="田中 一郎">田中 一郎</option>
<option value="田中 三郎">田中 三郎</option>
<option value="田中 五郎">田中 五郎</option>
<option value="田中 四郎">田中 四郎</option>
<option value="田中 次郎">田中 次郎</option>
<option value="鈴木 一郎">鈴木 一郎</option>
<option value="鈴木 三郎">鈴木 三郎</option>
<option value="鈴木 五郎">鈴木 五郎</option>
<option value="鈴木 四郎">鈴木 四郎</option>
<option value="鈴木 次郎">鈴木 次郎</option>
<option value="高橋 一郎">高橋 一郎</option>
<option value="高橋 三郎">高橋 三郎</option>
<option value="高橋 五郎">高橋 五郎</option>
<option value="高橋 四郎">高橋 四郎</option>
<option value="高橋 次郎">高橋 次郎</option>
</select>
</div>
<label>投票理由</label>
<div class="form-group">
<input class="form-control" name="keyword" value="">
</div>
<label>投票数</label>
<div class="form-group">
<input class="form-control" name="vote_count" value="">
</div>
<div class="text-danger">{message}</div>
<input class="btn btn-lg btn-success btn-block" type="submit" name="vote" value="投票" />
</fieldset>
</form>
</div>
</div>
</div>
</div>
</div>
</body>
</html>
""".replace('\n', '')

VOTE_HTML = VOTE_BASE_HTML.format(message='')
VOTE_SUCCESS_HTML = VOTE_BASE_HTML.format(message='投票に成功しました')
VOTE_FAIL1_HTML = VOTE_BASE_HTML.format(message='個人情報に誤りがあります')
VOTE_FAIL2_HTML = VOTE_BASE_HTML.format(message='投票数が上限を超えています')
VOTE_FAIL3_HTML = VOTE_BASE_HTML.format(message='候補者を記入してください')
VOTE_FAIL4_HTML = VOTE_BASE_HTML.format(message='候補者を正しく記入してください')
VOTE_FAIL5_HTML = VOTE_BASE_HTML.format(message='投票理由を記入してください')


import urllib
import urllib.parse

CANDIDATES = {
    '伊藤 一郎': 26,
    '伊藤 三郎': 28,
    '伊藤 五郎': 30,
    '伊藤 四郎': 29,
    '伊藤 次郎': 27,
    '佐藤 一郎': 1,
    '佐藤 三郎': 3,
    '佐藤 五郎': 5,
    '佐藤 四郎': 4,
    '佐藤 次郎': 2,
    '渡辺 一郎': 21,
    '渡辺 三郎': 23,
    '渡辺 五郎': 25,
    '渡辺 四郎': 24,
    '渡辺 次郎': 22,
    '田中 一郎': 16,
    '田中 三郎': 18,
    '田中 五郎': 20,
    '田中 四郎': 19,
    '田中 次郎': 17,
    '鈴木 一郎': 6,
    '鈴木 三郎': 8,
    '鈴木 五郎': 10,
    '鈴木 四郎': 9,
    '鈴木 次郎': 7,
    '高橋 一郎': 11,
    '高橋 三郎': 13,
    '高橋 五郎': 15,
    '高橋 四郎': 14,
    '高橋 次郎': 12,
}

QUOTED_CANDIDATES = {urllib.parse.quote_plus(k): v for k, v in CANDIDATES.items()}



CANDIDATES_MASTER = {
    1: {'id': 1, 'name': '佐藤 一郎', 'political_party': '夢実現党', 'sex': '男'},
    2: {'id': 2, 'name': '佐藤 次郎', 'political_party': '国民10人大活躍党', 'sex': '女'},
    3: {'id': 3, 'name': '佐藤 三郎', 'political_party': '国民10人大活躍党', 'sex': '女'},
    4: {'id': 4, 'name': '佐藤 四郎', 'political_party': '国民10人大活躍党', 'sex': '男'},
    5: {'id': 5, 'name': '佐藤 五郎', 'political_party': '国民元気党', 'sex': '女'},
    6: {'id': 6, 'name': '鈴木 一郎', 'political_party': '国民平和党', 'sex': '男'},
    7: {'id': 7, 'name': '鈴木 次郎', 'political_party': '国民元気党', 'sex': '女'},
    8: {'id': 8, 'name': '鈴木 三郎', 'political_party': '国民10人大活躍党', 'sex': '女'},
    9: {'id': 9, 'name': '鈴木 四郎', 'political_party': '国民元気党', 'sex': '女'},
    10: {'id': 10, 'name': '鈴木 五郎', 'political_party': '国民元気党', 'sex': '女'},
    11: {'id': 11, 'name': '高橋 一郎', 'political_party': '国民平和党', 'sex': '男'},
    12: {'id': 12, 'name': '高橋 次郎', 'political_party': '夢実現党', 'sex': '男'},
    13: {'id': 13, 'name': '高橋 三郎', 'political_party': '夢実現党', 'sex': '男'},
    14: {'id': 14, 'name': '高橋 四郎', 'political_party': '国民平和党', 'sex': '女'},
    15: {'id': 15, 'name': '高橋 五郎', 'political_party': '国民10人大活躍党', 'sex': '女'},
    16: {'id': 16, 'name': '田中 一郎', 'political_party': '夢実現党', 'sex': '男'},
    17: {'id': 17, 'name': '田中 次郎', 'political_party': '国民平和党', 'sex': '女'},
    18: {'id': 18, 'name': '田中 三郎', 'political_party': '夢実現党', 'sex': '女'},
    19: {'id': 19, 'name': '田中 四郎', 'political_party': '国民元気党', 'sex': '男'},
    20: {'id': 20, 'name': '田中 五郎', 'political_party': '夢実現党', 'sex': '女'},
    21: {'id': 21, 'name': '渡辺 一郎', 'political_party': '夢実現党', 'sex': '女'},
    22: {'id': 22, 'name': '渡辺 次郎', 'political_party': '国民平和党', 'sex': '女'},
    23: {'id': 23, 'name': '渡辺 三郎', 'political_party': '夢実現党', 'sex': '男'},
    24: {'id': 24, 'name': '渡辺 四郎', 'political_party': '国民平和党', 'sex': '女'},
    25: {'id': 25, 'name': '渡辺 五郎', 'political_party': '国民10人大活躍党', 'sex': '男'},
    26: {'id': 26, 'name': '伊藤 一郎', 'political_party': '夢実現党', 'sex': '女'},
    27: {'id': 27, 'name': '伊藤 次郎', 'political_party': '国民10人大活躍党', 'sex': '女'},
    28: {'id': 28, 'name': '伊藤 三郎', 'political_party': '国民平和党', 'sex': '女'},
    29: {'id': 29, 'name': '伊藤 四郎', 'political_party': '国民10人大活躍党', 'sex': '男'},
    30: {'id': 30, 'name': '伊藤 五郎', 'political_party': '国民元気党', 'sex': '男'}
}


PARTY_MASTER = {
    '国民10人大活躍党': [2,3,4,8,15,25,27,29],
    '国民元気党': [5,7,9,10,19,30],
    '国民平和党': [6,11,14,17,22,24,28],
    '夢実現党': [1,12,13,16,18,20,21,23,26],
}
