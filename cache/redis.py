import redis
import os


def get_redis_client():
    # Use environment variable or default to 'cache' (Docker service name)
    redis_host = os.getenv("REDIS_HOST", "cache")
    redis_port = int(os.getenv("REDIS_PORT", 6379))

    return redis.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        decode_responses=True,  # Important for string responses
        socket_connect_timeout=5,  # Connection timeout
        socket_keepalive=True,  # Keep connection alive
        retry_on_timeout=True  # Retry on timeout
    )


#
# def read_write_cache(cache_key: str, data: dict, refresh: int = 0):
#     try:
#         redis = get_redis_client()
#         cached_client_cart = redis.get(cache_key)
#
#         if cached_client_cart and refresh == 0:
#             cart = json.loads(cached_client_cart.decode("utf-8"))
#             return JSONResponse(status_code=status.HTTP_200_OK, content=cart)
#         data = repo.get_client_carts(client_id=client_id, skip=skip, limit=limit)
#         safe_data = jsonable_encoder(data)
#         redis.set(cache_key, json.dumps(safe_data), ex=300)  # Cache for 5 minutes
#         return data
#     except Exception as e:
#         print(e)
#         raise HTTPException(status_code=500, detail="Failed to retrieve client cart items") from e


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
