# Python 3.14 | reroller/engine.py | deterministic sequential crafting engine
from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from typing import Callable, Protocol

from .domain import Item, Target, RerollError, validate_item
from .i18n import Message, msg


class Cancelled(RerollError):
    pass


class Connection(Protocol):
    def guard(self) -> None: ...
    def read_item(self) -> Item: ...
    def read_currency(self) -> int: ...
    def apply_once(self, before_click: Callable[[], None]) -> None: ...
    def wait(self, seconds: float) -> None: ...
    def begin_repeat(self) -> None: ...
    def end_repeat(self) -> None: ...


@dataclass(frozen=True)
class Timing:
    stable_seconds: float = 0.08
    result_timeout: float = 3.0
    poll_seconds: float = 0.015


@dataclass(frozen=True)
class Progress:
    attempts: int
    verified: int
    elapsed: float
    status: str
    item: Item | None = None
    message: Message | None = None


@dataclass(frozen=True)
class Result:
    reason: str
    attempts: int
    verified: int
    matched: bool
    elapsed: float
    message: Message | None = None


class Engine:
    def __init__(self, connection: Connection, target: Target, budget: int,
                 stop: threading.Event, emit: Callable[[Progress], None] = lambda p: None,
                 timing: Timing = Timing(), clock: Callable[[], float] = time.monotonic,
                 repeat: bool = False, validate_target: Callable[[Item], None] | None = None):
        if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
            raise RerollError(msg('budget_invalid'))
        self.connection, self.target, self.budget = connection, target, budget
        self.stop, self.emit, self.timing, self.clock = stop, emit, timing, clock
        self.attempts = self.verified = 0
        self.started = clock()
        self.repeat = repeat and budget > 1
        self.validate_target = validate_target

    def guard(self) -> None:
        if self.stop.is_set():
            raise Cancelled(msg('stopped'))
        self.connection.guard()

    def report(self, status: str, item: Item | None = None) -> None:
        message = status if isinstance(status, Message) else msg("detail", detail=status)
        self.emit(Progress(self.attempts, self.verified, self.clock() - self.started, str(message), item, message))

    def stable_item(self, previous: Item | None = None) -> Item:
        deadline = self.clock() + self.timing.result_timeout
        candidate: Item | None = None
        since = self.clock()
        while self.clock() < deadline:
            self.guard()
            item = self.connection.read_item()
            validate_item(item)
            if previous and item.identity != previous.identity:
                raise RerollError(msg('identity_changed'))
            if previous and item.fingerprint == previous.fingerprint:
                candidate = None
                since = self.clock()
            elif candidate and item.fingerprint == candidate.fingerprint:
                if self.clock() - since >= self.timing.stable_seconds:
                    return item
            else:
                candidate, since = item, self.clock()
            self.connection.wait(self.timing.poll_seconds)
        raise RerollError(msg('result_uncertain'))

    def currency_after(self, before: int) -> int:
        deadline = self.clock() + self.timing.result_timeout
        while self.clock() < deadline:
            self.guard()
            # A depleted slot cannot be distinguished from a missing stack by text alone.
            # The final application therefore remains unverified and stops conservatively.
            count = self.connection.read_currency()
            if count == before - 1:
                self.verified += 1
                return count
            if count != before:
                raise RerollError(msg('currency_unexpected'))
            self.connection.wait(self.timing.poll_seconds)
        raise RerollError(msg('consumption_unverified'))

    def run(self) -> Result:
        self.started = self.clock()
        matched = False
        repeating = False
        try:
            self.report(msg('checking_item'))
            item = self.stable_item()
            self.report(msg('item_read'), item)
            if self.target.matches(item):
                matched, reason = True, msg('already_matched')
            else:
                if self.validate_target:
                    self.validate_target(item)
                count = self.connection.read_currency()
                initial_count = count
                limit = min(self.budget, count) if self.repeat else self.budget
                reason = msg('budget_reached')
                if self.repeat:
                    repeating = True
                    self.connection.begin_repeat()
                while self.attempts < limit:
                    self.guard()
                    # Check again after travelling to the currency stack; never craft on stale identity.
                    check = self.stable_item()
                    if check.fingerprint != item.fingerprint:
                        raise RerollError(msg('item_changed_between'))
                    if self.target.matches(check):
                        matched, reason = True, msg('matched')
                        break

                    def before_click() -> None:
                        self.guard()
                        if self.attempts >= self.budget:
                            raise RerollError(msg('budget_reached'))
                        # Count uncertain input as an attempt, even if SendInput fails.
                        self.attempts += 1

                    self.connection.apply_once(before_click)
                    self.report(msg('waiting_result'))
                    updated = self.stable_item(previous=item)
                    self.report(msg('result_read'), updated)
                    # A target takes precedence over currency bookkeeping: no more inputs on a hit.
                    if self.target.matches(updated):
                        matched, reason = True, msg('matched')
                        break
                    if not self.repeat:
                        count = self.currency_after(count)
                    item = updated
                    self.report(msg('result_verified') if self.repeat else msg('result_currency_verified'), item)
                if self.repeat and not matched:
                    after = self.connection.read_currency()
                    if initial_count - after != self.attempts:
                        raise RerollError(msg('aggregate_unverified'))
                    self.verified = self.attempts
                    if limit < self.budget:
                        reason = msg('stack_limit')
        except RerollError as exc:
            reason = exc.message
        finally:
            if repeating:
                try:
                    self.connection.end_repeat()
                except RerollError as exc:
                    reason = msg("hit_cleanup", detail=exc.message) if matched else exc.message
        message = reason if isinstance(reason, Message) else msg("detail", detail=reason)
        result = Result(str(message), self.attempts, self.verified, matched, self.clock() - self.started, message)
        self.report(reason)
        return result
