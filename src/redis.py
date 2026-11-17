from upstash_redis import Redis as R
from dotenv import load_dotenv

load_dotenv()


class Redis:
    def __init__(self):
        self.redis = R.from_env()


class RedisStream(Redis):
    def __init__(self):
        super().__init__()

    def add(self, key: str, data):
        return self.redis.xadd(key, "*", data)

    def get_random_data(self, key: str):
        LUA_SCRIPT = """
local len = redis.call('XLEN', KEYS[1])
if len == 0 then return nil end
local idx = math.random(1, len)
local entries = redis.call('XRANGE', KEYS[1], '-', '+')
return entries[idx]
"""
        result = self.redis.eval(LUA_SCRIPT, [key], [])
        if not result:
            return None

        id, raw_fields = result
        data = dict(zip(raw_fields[::2], raw_fields[1::2]))
        return data

    def get_latest_data(self, key: str):
        result = self.redis.xrevrange(key, "+", "-", count=1)
        if not result:
            return None

        id, raw_fields = result[0]
        data = dict(zip(raw_fields[::2], raw_fields[1::2]))
        return data
