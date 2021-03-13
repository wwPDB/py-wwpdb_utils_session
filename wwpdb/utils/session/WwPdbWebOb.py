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

from webob import Request as webob_Request
from webob import Response as webob_Response


class WwPdbRequest(object):
    def __init__(self, environ, charset=None, unicode_errors=None, decode_param_names=None, **kw):
        self.req = webob_Request(environ, charset=charset, unicode_errors=unicode_errors, decode_param_names=decode_param_names, **kw)

    def __enter__(self):
        return self.req

    def __exit__(self, type, value, traceback):  # pylint: disable=redefined-builtin
        for name, fs in self.req.params.items():
            if (fs is None) or (isinstance(fs, str)) or (isinstance(fs, bytes)):
                continue
            if not hasattr(fs, "filename") or fs.filename == name:
                continue
            try:
                fs.file.close()
            except:  # noqa: E722 pylint: disable=bare-except
                pass
        # This is because WebOB will create a temporary file, and rely on garbage collection to close files. Python3, this is not happening when go out scope
        # For new webob, there might be subsequent changes to code - so protect
        if self.req.is_body_seekable:
            if self.req.body_file_raw and hasattr(self.req.body_file_raw, "close"):
                try:
                    self.req.body_file_raw.close()
                except:  # noqa: E722 pylint: disable=bare-except
                    pass


class WwPdbResponse(webob_Response):
    """Pass through for webob Reponse class in case we need to add a wrapper later"""
