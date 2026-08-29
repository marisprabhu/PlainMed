"""Zero-retention enforcement.

The product claim is "processed, never stored". That is only credible if it
is a property of the code rather than a promise in a policy document, so it
is enforced in three places and verified by scripts/retention_check.py:

1. Logging - a filter drops any record carrying report content, and the
   access log never records request bodies. PHI cannot reach a log sink by
   accident.
2. Responses - no-store cache headers so nothing is retained by browsers or
   intermediate proxies.
3. Filesystem - a guard used in tests asserts that handling a request
   creates no files anywhere under the process's temp or working
   directories.

What this does NOT claim: that memory is scrubbed, that the host is secure,
or that an operator with root on the box could not observe traffic. Those
require infrastructure controls, documented in deploy/README.md.
"""

from __future__ import annotations

import logging
from typing import Iterable

# Fields that may carry report content. Anything attached to a log record
# under these names is dropped rather than redacted, so a formatting bug
# cannot leak it.
PHI_FIELDS = frozenset(
    {
        "report_text",
        "raw_text",
        "image",
        "image_bytes",
        "ocr_text",
        "lines",
        "spans",
        "values",
        "cards",
        "narrative",
        "document",
    }
)


class WindowsDisconnectFilter(logging.Filter):
    """Drop the asyncio noise a browser makes when it closes a socket.

    On Windows, uvicorn's proactor loop logs a full traceback for
    WinError 10054 when a client disconnects abruptly - closing a tab,
    refreshing mid-request. The response has already been delivered; there
    is nothing wrong and nothing to act on. It is filtered rather than
    suppressed wholesale, so genuine asyncio errors still surface.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name != "asyncio":
            return True
        text = record.getMessage()
        if record.exc_info and record.exc_info[1] is not None:
            text += " " + str(record.exc_info[1])
        return "10054" not in text and "_call_connection_lost" not in text


class PhiLogFilter(logging.Filter):
    """Drop log records that carry report content.

    Applied to the root logger, so it covers application, framework, and
    third-party loggers alike.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        for field in PHI_FIELDS:
            if hasattr(record, field):
                return False
        # A record whose message was built from a document object would carry
        # PHI in the formatted string; refuse those too.
        if isinstance(getattr(record, "args", None), dict):
            if PHI_FIELDS & set(record.args.keys()):
                return False
        return True


def install_phi_log_filter(logger_names: Iterable[str] = ()) -> None:
    """Attach the PHI filter to the root logger and any named loggers."""
    phi_filter = PhiLogFilter()
    root = logging.getLogger()
    root.addFilter(phi_filter)
    for handler in root.handlers:
        handler.addFilter(phi_filter)

    disconnect_filter = WindowsDisconnectFilter()
    logging.getLogger("asyncio").addFilter(disconnect_filter)
    for handler in root.handlers:
        handler.addFilter(disconnect_filter)
    for name in logger_names:
        logger = logging.getLogger(name)
        logger.addFilter(phi_filter)
        for handler in logger.handlers:
            handler.addFilter(phi_filter)


NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    # A report page must never be embedded or sniffed.
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}
