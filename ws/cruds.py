from redis import Redis

import ws.schemas as schema

def get_redis(redis: Redis,key: str) -> str | None:
    value=redis.get(key)
    if value:
        return value
    else:
        return None
    
def post_redis(redis: Redis,key: str,value: str) -> None:
    redis.set(key, value)
    return None

def delete_redis(redis: Redis,key: str) -> None:
    value=redis.delete(key)
    return None

def get_redis_list(redis: Redis) -> schema.RedisGetListResponse | None:
    keys = redis.keys('*')
    items = [(key, redis.get(key)) for key in keys]
    return items