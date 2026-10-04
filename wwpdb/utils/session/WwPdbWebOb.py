##
# File:  wwPDBWebOb.py
# Date:  11-Mar-2021 E. Peisach
#
# Update:
##
"""
Wrapper for WebOB to cleanup file descriptors when going out of scope.
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "ezra.peisach@rcsb.org"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import contextlib
from types import TracebackType
from typing import Any, Dict, Optional, Type

from webob import Request as webob_Request
from webob import Response as webob_Response


class WwPdbRequest:
    def __init__(
        self,
        environ: Dict[str, Any],
        charset: Optional[str] = None,
        unicode_errors: Optional[str] = None,
        decode_param_names: Optional[bool] = None,
        **kw: Any,
    ) -> None:
        self.req = webob_Request(
            environ, charset=charset, unicode_errors=unicode_errors, decode_param_names=decode_param_names, **kw
        )

    def __enter__(self) -> webob_Request:
        return self.req

    def __exit__(
        self,
        type: Optional[Type[BaseException]],  # noqa: A002,A003 # pylint: disable=redefined-builtin
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:  # noqa: A002 # pylint: disable=redefined-builtin
        for name, fs in self.req.params.items():
            if isinstance(fs, (bytes, str)):
                continue
            if not hasattr(fs, "filename") or fs.filename == name:
                continue

            with contextlib.suppress(Exception):
                fs.file.close()
            # if exception - ignore

        # This is because WebOB will create a temporary file, and rely on garbage collection to close files. Python3, this is not happening when go out scope
        # For new webob, there might be subsequent changes to code - so protect
        if self.req.is_body_seekable:  # noqa: SIM102
            if self.req.body_file_raw and hasattr(self.req.body_file_raw, "close"):
                with contextlib.suppress(Exception):
                    self.req.body_file_raw.close()


class WwPdbResponse(webob_Response):  # type: ignore[misc,unused-ignore]
    """Pass through for webob Reponse class in case we need to add a wrapper later"""
