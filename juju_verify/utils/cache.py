# Copyright 2021 Canonical Limited.
#
# This file is part of juju-verify.
#
# juju-verify is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# juju-verify is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see https://www.gnu.org/licenses/.
"""Helper function to manage cache."""
from collections import OrderedDict
from contextlib import contextmanager, _GeneratorContextManager
from typing import Any, List, Optional, Generator


class Cache:
    """Cache for storing outputs using specific keys.

    Usage example:
    cache = Cache()

    def run_action(name: str) -> Any:
        if name in cache:
            return cache[name]

        return _run_action(name)

    run_action('test')  # action 'test' is executed
    run_action('test')  # action 'test' is not executed
    run_action('test')  # action 'test' is not executed
    """

    def __init__(self, maxsize: int):
        """Initialize cache object."""
        self._cache: OrderedDict = OrderedDict()
        self.maxsize: int = maxsize

    def __getitem__(self, key: int) -> Any:
        """Get cached value."""
        if key in self._cache:
            self._cache.move_to_end(key)  # reorder cache

        return self._cache[key]

    def __setitem__(self, key: int, value: Any) -> None:
        """Cache the value using the key."""
        self._cache[key] = value

        # remove the oldest key
        if len(self._cache) > self.maxsize:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

    def __iter__(self) -> Generator:
        """Iterate over cache keys."""
        for key in self._cache:
            yield key

    def clear(self) -> None:
        """Clear cached data."""
        self._cache.clear()

    @property
    def keys(self) -> List[Any]:
        """Return cached keys."""
        return list(self._cache.keys())


class CacheManager:
    """A cache manager that determines when to use this cache.

    Usage example:
    cache_manager = CacheManager(enabled=True)
    cache = Cache()

    def run_action(name: str) -> Any:
        if cache_manager.enabled and name in cache:
            return cache[name]

        return _run_action(name)

    run_action('test')  # action 'test' is executed
    run_action('test')  # action 'test' is not executed

    with cache_manager(use_cache=False):
        run_action('test')  # action 'test' is executed

    run_action('test')  # action 'test' is not executed
    """

    def __init__(self, enabled: bool = True):
        """Init the Cache class with default state."""
        self._previous_state: Optional[bool] = None
        self._enabled: bool = enabled

    def __call__(self, use_cache: Optional[bool] = None) -> _GeneratorContextManager:
        """Return cache contextmanager if instance is called."""
        return self.cache_contextmanager(use_cache)

    @property
    def enabled(self) -> bool:
        """Return True if cache is enabled."""
        return self._enabled

    @property
    def previous_state(self) -> bool:
        """Return previous cache state."""
        if self._previous_state is None:
            return self.enabled

        return self._previous_state

    def set_state(self, use_cache: Optional[bool] = None) -> None:
        """Set the cache state."""
        if use_cache is True:
            self.enable()
        elif use_cache is False:
            self.disable()

    def enable(self) -> None:
        """Enable the cache."""
        self._previous_state = self.enabled
        self._enabled = True

    def disable(self) -> None:
        """Disable the cache."""
        self._previous_state = self.enabled
        self._enabled = False

    @contextmanager
    def cache_contextmanager(self, use_cache: Optional[bool] = None) -> Generator:
        """Possibility to temporarily run the cache."""
        self.set_state(use_cache)
        try:
            yield
        finally:
            self.set_state(self.previous_state)
