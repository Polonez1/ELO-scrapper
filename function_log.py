import logging
import time

logging.basicConfig(level=logging.INFO)


def elapsed_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logging.info(f"start: {func.__name__}.")
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Time: {elapsed_time}")
        logging.info(f"End: {func.__name__}")
        return result

    return wrapper
