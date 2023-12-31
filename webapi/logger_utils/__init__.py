import logging
import sys


def get_logger():
    logger_ = logging.getLogger('root')

    logger_.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(levelname)s: [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger_.addHandler(handler)

    return logger_


logger = get_logger()
