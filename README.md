# ishocon2-practice

My Practice repository for ISHOCON2.

https://github.com/showwin/ISHOCON2


How To
-------------

```
pip install -r python/requirements.txt
```


What's?
--------------

* myaap.py -> Flask Implementation.
* sanic_app.py -> Sanic Implementation.

Sanic is faster than flask.

SetUp Data
---------------

View ISHOCON2 setup -> https://github.com/showwin/ISHOCON2#%E5%95%8F%E9%A1%8C%E8%A9%B3%E7%B4%B0

I keep all `users` data on redis cache. Need two steps.

### 1st

mysql data change to URLEncodeddata.

```
python work.py
```

### 2nd

mysql data to redis.

```
python work2.py
```

My Score
----------------

#### Sanic

```
ubuntu@ip-172-31-23-113:~$ ./benchmark --ip 54.238.255.213 --workload 75
2018/08/28 14:32:16 Start GET /initialize
2018/08/28 14:32:16 期日前投票を開始します
2018/08/28 14:32:17 期日前投票が終了しました
2018/08/28 14:32:17 投票を開始します  Workload: 75
2018/08/28 14:33:02 投票が終了しました
2018/08/28 14:33:02 投票者が結果を確認しています
2018/08/28 14:33:18 投票者の感心がなくなりました
2018/08/28 14:33:18 {"score": 202920, "success": 181960, "failure": 0}
```
