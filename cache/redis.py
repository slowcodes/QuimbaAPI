import redis


def get_redis_client():
    return redis.Redis(host="localhost", port=6379, db=0)


def decode_bytes(obj):
    if isinstance(obj, bytes):
        # decode assuming UTF-8; adjust if needed
        return obj.decode("utf-8")
    elif isinstance(obj, dict):
        return {k: decode_bytes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decode_bytes(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(decode_bytes(i) for i in obj)
    else:
        return obj
