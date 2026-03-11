import time
from functools import wraps

def cumulative_timer(func):
    total_time = 0.0

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal total_time
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        total_time += end - start
        wrapper.total_time = total_time
        return result

    wrapper.total_time = 0.0
    return wrapper