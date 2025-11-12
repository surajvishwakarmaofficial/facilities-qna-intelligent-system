import redis
import json
from typing import Optional

class ResponseCache:
    def __init__(self, redis_client, ttl=3600):
        self.redis = redis_client
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[dict]:
        data = self.redis.get(f"cache:{key}")
        if data:
            return json.loads(data)
        return None
    
    def set(self, key: str, value: dict):
        self.redis.setex(
            f"cache:{key}",
            self.ttl,
            json.dumps(value)
        )