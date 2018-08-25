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
"""

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