"""
utils.py

Utility functions like retry logic.
"""

import time


def retry(func, retries=3, delay=2):
    """
    Retry wrapper for robustness.

    Args:
        func (callable)
        retries (int)
        delay (int)

    Returns:
        function result
    """

    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            print(f"Retry {attempt + 1} failed: {e}")
            time.sleep(delay)

    raise Exception("Max retries exceeded")