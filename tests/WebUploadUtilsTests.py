##
# File: WebUploadUtilsTests.py
# Date:  03-Oct-2026
#
# Updates:
##
"""Test cases for WebUploadUtils"""

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import gzip
import os
import shutil
import tempfile
import unittest
from io import BytesIO, StringIO
from typing import Any, cast

from webob.compat import cgi_FieldStorage

from wwpdb.utils.session.WebRequest import InputRequest
from wwpdb.utils.session.WebUploadUtils import WebUploadUtils


# The following is from https://stackoverflow.com/questions/12032807/how-to-create-cgi-fieldstorage-for-testing-purposes
def _create_fs(mimetype: str, content: bytes, filename: str = "uploaded.txt", name: str = "file") -> Any:
    headers = {
        "content-disposition": f'form-data; name="{name}"; filename="{filename}"',
        "content-length": len(content),
        "content-type": mimetype,
    }
    environ = {"REQUEST_METHOD": "POST"}
    fp = BytesIO(content)
    return cgi_FieldStorage(fp=fp, headers=headers, environ=environ)  # type: ignore[call-arg]


class WebUploadUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpDir = tempfile.mkdtemp()
        self.sessionPath = ""
        self.content = b"data_test\n_entry.id TEST\n"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpDir, ignore_errors=True)

    def makeUtils(self, extra: dict[str, list[Any]] | None = None, verbose: bool = True) -> WebUploadUtils:
        paramDict: dict[str, list[Any]] = {"TopSessionPath": [self.tmpDir]}
        if extra:
            paramDict.update(extra)
        reqObj = InputRequest(paramDict)
        self.sessionPath = cast("str", reqObj.newSessionObj().getPath())
        return WebUploadUtils(reqObj, verbose=verbose, log=StringIO())

    def testIsFileUpload(self) -> None:
        wuu = self.makeUtils({"file": [_create_fs("text", self.content)], "text": ["string"], "bytes": [b"b"]})
        self.assertTrue(wuu.isFileUpload())
        self.assertFalse(wuu.isFileUpload("text"))
        self.assertFalse(wuu.isFileUpload("bytes"))

    def testGetUploadFileName(self) -> None:
        wuu = self.makeUtils(
            {
                "file": [_create_fs("text", self.content, filename="/some/path/model.cif")],
                "winfile": [_create_fs("text", self.content, filename="C:\\Users\\me\\model2.cif")],
            }
        )
        self.assertEqual(wuu.getUploadFileName(), "model.cif")
        self.assertEqual(wuu.getUploadFileName("winfile"), "model2.cif")
        self.assertIsNone(wuu.getUploadFileName("missing"))

    def testCopyToSession(self) -> None:
        wuu = self.makeUtils({"file": [_create_fs("text", self.content, filename="C:\\dir\\model.cif")]})
        self.assertEqual(wuu.copyToSession(), "model.cif")
        with open(os.path.join(self.sessionPath, "model.cif"), "rb") as fin:
            self.assertEqual(fin.read(), self.content)

    def testCopyToSessionRename(self) -> None:
        wuu = self.makeUtils({"file": [_create_fs("text", self.content, filename="model.cif")]})
        self.assertEqual(wuu.copyToSession(sessionFileName="other.cif"), "other.cif")
        self.assertTrue(os.path.exists(os.path.join(self.sessionPath, "other.cif")))
        self.assertFalse(os.path.exists(os.path.join(self.sessionPath, "model.cif")))

    def testCopyToSessionGzip(self) -> None:
        gzContent = gzip.compress(self.content)
        wuu = self.makeUtils(
            {
                "file": [_create_fs("application/gzip", gzContent, filename="model.cif.gz")],
                "file2": [_create_fs("application/gzip", gzContent, filename="model2.cif.gz")],
            }
        )
        self.assertEqual(wuu.copyToSession(), "model.cif")
        with open(os.path.join(self.sessionPath, "model.cif"), "rb") as fin:
            self.assertEqual(fin.read(), self.content)

        # No uncompress
        self.assertEqual(wuu.copyToSession("file2", uncompress=False), "model2.cif.gz")
        self.assertFalse(os.path.exists(os.path.join(self.sessionPath, "model2.cif")))

    def testCopyToSessionFail(self) -> None:
        wuu = self.makeUtils({"text": ["string"]})
        self.assertIsNone(wuu.copyToSession("missing"))
        self.assertIsNone(wuu.copyToSession("text"))

    def testRenameSessionFile(self) -> None:
        wuu = self.makeUtils({"file": [_create_fs("text", self.content, filename="model.cif")]})
        wuu.copyToSession()
        self.assertTrue(wuu.renameSessionFile("model.cif", "model.cif"))
        self.assertTrue(wuu.renameSessionFile("model.cif", "copy.cif"))
        with open(os.path.join(self.sessionPath, "copy.cif"), "rb") as fin:
            self.assertEqual(fin.read(), self.content)
        self.assertFalse(wuu.renameSessionFile("missing.cif", "copy2.cif"))

    def testGetFileExtension(self) -> None:
        self.assertIsNone(WebUploadUtils.getFileExtension(None))
        self.assertIsNone(WebUploadUtils.getFileExtension(""))
        self.assertIsNone(WebUploadUtils.getFileExtension("noext"))
        self.assertEqual(WebUploadUtils.getFileExtension("a.cif"), "cif")
        self.assertEqual(WebUploadUtils.getFileExtension("a.cif.V2"), "V2")
        self.assertEqual(WebUploadUtils.getFileExtension("a.cif.V2", ignoreVersion=True), "cif")
        self.assertEqual(WebUploadUtils.getFileExtension("a.cif.v12", ignoreVersion=True), "cif")
        self.assertEqual(WebUploadUtils.getFileExtension("a.cif.gz", ignoreVersion=True), "gz")
        self.assertEqual(WebUploadUtils.getFileExtension("a.cif.Vx", ignoreVersion=True), "Vx")
        self.assertEqual(WebUploadUtils.getFileExtension("a.cif", ignoreVersion=True), "cif")

    def testPerceiveIdentifier(self) -> None:
        for verbose in [True, False]:
            wuu = self.makeUtils(verbose=verbose)
            self.assertEqual(wuu.perceiveIdentifier(None), (None, None))
            self.assertEqual(wuu.perceiveIdentifier(""), (None, None))
            self.assertEqual(wuu.perceiveIdentifier("rcsb012345.cif"), ("rcsb012345", "RCSB"))
            self.assertEqual(wuu.perceiveIdentifier("D_1000000001_model_P1.cif"), ("D_1000000001", "WF_ARCHIVE"))
            self.assertEqual(wuu.perceiveIdentifier("W_000001.cif"), ("W_000001", "WF_INSTANCE"))
            self.assertEqual(wuu.perceiveIdentifier("other.cif"), ("other", "UNKNOWN"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
