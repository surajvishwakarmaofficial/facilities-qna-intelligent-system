import redis
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, redis_client, max_requests=100, window_seconds=3600):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, user_id: str) -> bool:
        key = f"rate_limit:{user_id}"
        current = self.redis.get(key)
        
        if current is None:
            self.redis.setex(key, self.window_seconds, 1)
            return True
        
        if int(current) >= self.max_requests:
            return False
        
        self.redis.incr(key)
        return True