#! python3
# coding: utf-8
# Reference and edit from
# 1. https://stackoverflow.com/a/23036785
# 2. https://stackoverflow.com/a/72963552

# 如果 python >= 3.8, 可以直接使用 unittest.IsolatedAsyncioTestCase, 參見: https://stackoverflow.com/a/59333941
# 該方法提供給 < 3.8 版本的使用

import asyncio
import functools
from typing import Tuple

__all__: Tuple[str] = ("async_test",)


def async_test(func):
    """Decorator to turn an async function into a test case."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coro)

    return wrapper
