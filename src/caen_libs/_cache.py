"""
Cache utilities
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

from functools import _lru_cache_wrapper, lru_cache, wraps
from typing import Optional
from weakref import ReferenceType, ref


class Manager(list[_lru_cache_wrapper]):
    """
    A simple list of functions returned by `@lru_cache` decorator.

    To be used with the optional parameter @p cache_manager of
    lru_cache_method(), that will store a reference to the cached
    function inside this list. This is a typing-safe way to call
    `cache_clear` and `cache_info` of the internal cached functions,
    even if not exposed directly by the inner function returned by
    lru_cache_method().
    """
    def clear_all(self) -> None:
        """Invoke `cache_clear` on all functions in the list"""
        for wrapper in self:
            wrapper.cache_clear()


# Typing support for decorators comes with Python 3.10.
# Omitted because very verbose.


def cached(cache_manager: Optional[Manager] = None, maxsize: int = 128, typed: bool = False):
    """
    LRU cache decorator that keeps a weak reference to self.

    To be used as decorator on methods that are known to return always
    the same value. This can improve the performances of some methods by
    a factor > 1000.
    This wrapper using weak references is required: functools.lru_cache
    holds a reference to all arguments: using directly on the methods it
    would hold a reference to self, introducing subtle memory leaks.

    @sa https://stackoverflow.com/a/68052994/3287591
    """

    def wrapper(method):

        @lru_cache(maxsize, typed)
        def cached_method(self_ref: ReferenceType, *args, **kwargs):
            self = self_ref()
            assert self is not None  # this function is always called by inner()
            return method(self, *args, **kwargs)

        @wraps(method)
        def inner(self, *args, **kwargs):
            return cached_method(ref(self), *args, **kwargs)

        # Optionally store a reference to lru_cache decorated function to
        # simplify cache management. See CacheManager documentation.
        if cache_manager is not None:
            cache_manager.append(cached_method)

        return inner

    return wrapper


def clear(cache_manager: Manager):
    """
    LRU cache decorator that clear cache.

    To be used as decorator on methods that are known to invalidate the
    cache.
    """

    def wrapper(method):

        def not_cached_method(self_ref: ReferenceType, *args, **kwargs):
            self = self_ref()
            assert self is not None  # this function is always called by inner()
            return method(self, *args, **kwargs)

        @wraps(method)
        def inner(self, *args, **kwargs):
            cache_manager.clear_all()
            return not_cached_method(ref(self), *args, **kwargs)

        return inner

    return wrapper
