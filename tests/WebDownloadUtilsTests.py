##
# File: WebDownloadUtilsTests.py
# Date:  03-Oct-2026
#
# Updates:
##
"""Test cases for WebDownloadUtils"""

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import json
import os
import shutil
import tempfile
import unittest
from io import StringIO
from typing import Any
from unittest import mock

from wwpdb.utils.session.WebDownloadUtils import WebDownloadUtils
from wwpdb.utils.session.WebRequest import InputRequest


class WebDownloadUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpDir = tempfile.mkdtemp()
        self.filePath = os.path.join(self.tmpDir, "D_1000000001_model_P1.cif.V1")
        with open(self.filePath, "w") as fout:
            fout.write("data_test\n")
        piP = mock.patch("wwpdb.utils.session.WebDownloadUtils.PathInfo")
        self.mockPI = piP.start()
        self.addCleanup(piP.stop)
        self.mockPI.return_value.getFilePath.return_value = self.filePath

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpDir, ignore_errors=True)

    def makeResponse(self, params: dict[str, str]) -> dict[str, Any]:
        paramDict: dict[str, list[Any]] = {"TopSessionPath": [self.tmpDir]}
        for k, v in params.items():
            paramDict[k] = [v]
        reqObj = InputRequest(paramDict)
        reqObj.newSessionObj()
        wdu = WebDownloadUtils(reqObj, verbose=True, log=StringIO())
        rD: dict[str, Any] = wdu.makeDownloadResponse().get()
        return rD

    def assertFailure(self, rD: dict[str, Any]) -> None:
        self.assertEqual(rD["CONTENT_TYPE"], "application/json")
        ret = json.loads(rD["RETURN_STRING"])
        self.assertTrue(ret["errorflag"])
        self.assertIn("Download failure", ret["statustext"])

    def testDownload(self) -> None:
        """Tests successful download with defaults"""
        rD = self.makeResponse({"data_set_id": "D_1000000001", "content_type": "model"})
        self.assertEqual(rD["RETURN_STRING"], b"data_test\n")
        self.assertEqual(rD["CONTENT_TYPE"], "text/plain")
        self.assertEqual(rD["DISPOSITION"], "attachment; filename=D_1000000001_model_P1.cif.V1")
        self.mockPI.return_value.getFilePath.assert_called_once_with(
            "D_1000000001",
            wfInstanceId=None,
            contentType="model",
            formatType="pdbx",
            fileSource="archive",
            versionId="latest",
            partNumber="1",
        )

    def testDownloadOptions(self) -> None:
        """Tests request options passed through to PathInfo"""
        self.makeResponse(
            {
                "data_set_id": "D_1000000001",
                "content_type": "model",
                "file_source": "wf-instance",
                "wf_instance": "W_000001",
                "format": "pdb",
                "version": "2",
                "part": "3",
            }
        )
        self.mockPI.return_value.getFilePath.assert_called_once_with(
            "D_1000000001",
            wfInstanceId="W_000001",
            contentType="model",
            formatType="pdb",
            fileSource="wf-instance",
            versionId="2",
            partNumber="3",
        )

    def testBadRequests(self) -> None:
        """Tests incomplete or invalid requests fail"""
        self.assertFailure(self.makeResponse({"content_type": "model"}))
        self.assertFailure(self.makeResponse({"data_set_id": "D_1000000001"}))
        self.assertFailure(
            self.makeResponse({"data_set_id": "D_1000000001", "content_type": "model", "file_source": "bad"})
        )
        self.mockPI.return_value.getFilePath.assert_not_called()

    def testMissingFile(self) -> None:
        """Tests file returned from PathInfo does not exist"""
        self.mockPI.return_value.getFilePath.return_value = os.path.join(self.tmpDir, "missing")
        self.assertFailure(self.makeResponse({"data_set_id": "D_1000000001", "content_type": "model"}))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
