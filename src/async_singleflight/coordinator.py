"""Core SingleFlight concurrency coordinator.

Deduplicates concurrent in-flight asynchronous operations.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import inspect
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    """The outcome of a SingleFlight execution.

    Attributes:
        val: The actual data returned (e.g., user data from the database).
        shared: True if 2 or more requests shared this exact result.
        callers: The total number of requests that received this result.
    """

    val: T
    shared: bool
    callers: int


class _Call(Generic[T]):
    """Represents a single in-flight operation holding the claim ticket."""

    __slots__ = ("future", "callers", "is_leader")

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        # This is the "Buzzer / Claim Ticket":
        # It starts empty (PENDING). Callers wait on it until the leader finishes.
        self.future: asyncio.Future[T] = loop.create_future()

        # How many callers have joined this specific flight
        self.callers: int = 1
        self.is_leader: bool = False


class SingleFlight:
    """Coordinates and coalesces duplicate concurrent asynchronous operations.

    Tracks all in-flight operations on an internal registry whiteboard (self._calls).
    """

    def __init__(self) -> None:
        # The Whiteboard: maps a unique key (e.g., "user:42") to its active _Call ticket
        self._calls: dict[str, _Call[Any]] = {}

        # The Lock: ensures only one coroutine updates the whiteboard at a time
        self._lock: asyncio.Lock | None = None

    @property
    def _safe_lock(self) -> asyncio.Lock:
        """Lazily initialize the lock on the currently active event loop."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def do(
        self,
        key: str,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute `fn(*args, **kwargs)` with request deduplication by `key`.

        If the key is already being fetched, this waits for that in-flight
        operation and returns the shared result.
        """
        result = await self.do_detailed(key, fn, *args, **kwargs)
        return result.val

    async def do_detailed(
        self,
        key: str,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> Result[T]:
        """Execute `fn(*args, **kwargs)` and return the data plus telemetry."""
        loop = asyncio.get_running_loop()

        # Step 1: Check the Whiteboard (under the lock)
        async with self._safe_lock:
            if key in self._calls:
                # Key already exists on whiteboard: WE ARE A FOLLOWER!
                call = self._calls[key]
                call.callers += 1
                is_leader = False
            else:
                # Key not on whiteboard: WE ARE THE LEADER!
                call = _Call[T](loop)
                call.is_leader = True
                self._calls[key] = call
                is_leader = True

        # Step 2: The Follower Path
        # We don't touch the database. We just wait for the Leader's buzzer to ring!
        if not is_leader:
            val = await call.future
            return Result(val=val, shared=True, callers=call.callers)

        # Step 3: The Leader Path
        # We are the Leader. We do the actual heavy lifting (e.g. database query).
        try:
            coro = fn(*args, **kwargs)
            if not inspect.isawaitable(coro):
                raise TypeError(
                    f"SingleFlight expected an awaitable from callable {fn!r}, "
                    f"got {type(coro).__name__}"
                )
            res = await coro

            # Ring the buzzer! All followers waiting on call.future wake up now!
            call.future.set_result(res)
            return Result(val=res, shared=call.callers > 1, callers=call.callers)

        except BaseException as exc:
            # If the database crashes, ring the buzzer with the exception
            # so all followers also get the error instead of hanging forever!
            if not call.future.done():
                call.future.set_exception(exc)
                if call.callers == 1:
                    # Clear unretrieved warning if no followers were waiting
                    call.future.exception()
            raise

        finally:
            # Step 4: Clean the Whiteboard!
            # Erase the key so subsequent calls in the future run freshly.
            async with self._safe_lock:
                self._calls.pop(key, None)

    def is_in_flight(self, key: str) -> bool:
        """Check if an operation for `key` is currently active on the whiteboard."""
        return key in self._calls

    def active_keys(self) -> list[str]:
        """Return a snapshot list of all keys currently in flight."""
        return list(self._calls.keys())

    async def reset(self) -> None:
        """Clear all active calls. Helpful for test teardowns."""
        async with self._safe_lock:
            self._calls.clear()
