from __future__ import annotations

from typing import Any, Awaitable, Callable

MessageHandler = Callable[[Any], Awaitable[Any]]
Behavior = Callable[[MessageHandler], MessageHandler]
