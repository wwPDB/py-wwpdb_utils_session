##
# File: WwPdbWebObTests.py
# Date:  12-Mar-2021  E. Peisach
#
# Updates:
##
"""Test cases for FileUtils
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

from io import BytesIO
import os
import unittest

from wwpdb.utils.session.WwPdbWebOb import WwPdbRequest, WwPdbResponse


class WwPdbWebObTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_Post_empty(self):
        """Tests request with no data. Code path completeness"""
        data = b""
        wsgi_input = BytesIO(data)
        environ = {
            "wsgi.input": wsgi_input,
            "webob.is_body_seekable": True,
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "multipart/form-data; " "boundary=----------------------------deb95b63e42a",
            "CONTENT_LENGTH": len(data),
        }
        with WwPdbRequest(environ) as req:
            p = req.params
            self.assertEqual(len(p), 0)

    def test_Post_nofile(self):
        """Tests request with no data. Code path completeness"""
        data = b"------------------------------deb95b63e42a\n" b'Content-Disposition: form-data; name="foo"\n' b"\n" b"foo\n" b"------------------------------deb95b63e42a--\n"
        wsgi_input = BytesIO(data)
        environ = {
            "wsgi.input": wsgi_input,
            "webob.is_body_seekable": True,
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "multipart/form-data; " "boundary=----------------------------deb95b63e42a",
            "CONTENT_LENGTH": len(data),
        }
        with WwPdbRequest(environ) as req:
            p = req.params
            self.assertEqual(len(p), 1)

    def test_Post_multipart(self):
        """Tests file download - file descriptor leak wrapper fix"""

        data = (
            b"------------------------------deb95b63e42a\n"
            b'Content-Disposition: form-data; name="foo"\n'
            b"\n"
            b"foo\n"
            b"------------------------------deb95b63e42a\n"
            b'Content-Disposition: form-data; name="bar"; filename="bar.txt"\n'
            b"Content-type: application/octet-stream\n"
            b"\n"
            b'these are the contents of the file "bar.txt"\n'
            b"\n"
            b"------------------------------deb95b63e42a--\n"
        )
        wsgi_input = BytesIO(data)
        environ = {
            "wsgi.input": wsgi_input,
            "webob.is_body_seekable": True,
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "multipart/form-data; " "boundary=----------------------------deb95b63e42a",
            "CONTENT_LENGTH": len(data),
        }
        with WwPdbRequest(environ) as req:
            p = req.params
            self.assertEqual(len(p), 2)

    def test_Post_multipart_large(self):
        """Tests file download - file descriptor leak wrapper fix"""

        # File larger than 8kb
        dirpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session")
        bigfile = os.path.join(dirpath, "WebRequest.py")
        with open(bigfile, "rb") as fin:
            fdata = fin.read()

        data = (
            b"------------------------------deb95b63e42a\n"
            b'Content-Disposition: form-data; name="foo"\n'
            b"\n"
            b"foo\n"
            b"------------------------------deb95b63e42a\n"
            b'Content-Disposition: form-data; name="bar"; filename="bar.txt"\n'
            b"Content-type: application/octet-stream\n"
            b"\n" + fdata + b"\n"
            b'these are the contents of the file "bar.txt"\n'
            b"\n"
            b"------------------------------deb95b63e42a--\n"
        )
        wsgi_input = BytesIO(data)
        environ = {
            "wsgi.input": wsgi_input,
            "webob.is_body_seekable": True,
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "multipart/form-data; " "boundary=----------------------------deb95b63e42a",
            "CONTENT_LENGTH": len(data),
        }
        with WwPdbRequest(environ) as req:
            p = req.params
            self.assertEqual(len(p), 2)

    def testResponse(self):
        r = WwPdbResponse()
        r.status = "200 OK"
        r.content_type = "text/html"
        r.write("Test")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
