from redis import Redis
import os

host = os.environ["HOST_NAME"]
port = os.environ["PORT"]
redis = Redis(host=host, port=port, db=0)

# Redis接続の依存関数を定義
def get_redis():
    return redis