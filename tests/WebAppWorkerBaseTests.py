##
# File: WebAppWorkerBaseTests.py
# Date:  09-Jan-2020  E. Peisach
#
# Updates:
#  03-Oct-2026  Add typing.  Test service dispatch, session context and failure paths
##
"""Test cases for WebAppWorkerBaseTests"""

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import filecmp
import json
import os
import platform
import shutil
import tempfile
import unittest
from io import BytesIO, StringIO
from typing import Any, Callable, cast
from unittest import mock

from webob.compat import cgi_FieldStorage

from wwpdb.utils.session.WebAppWorkerBase import WebAppWorkerBase
from wwpdb.utils.session.WebRequest import InputRequest, ResponseContent


# The following is from https://stackoverflow.com/questions/12032807/how-to-create-cgi-fieldstorage-for-testing-purposes
def _create_fs(mimetype: str, content: str, filename: str = "uploaded.txt", name: str = "file") -> Any:
    bcontent = content.encode("utf-8")
    headers = {
        "content-disposition": f'form-data; name="{name}"; filename="{filename}"',
        "content-length": len(bcontent),
        "content-type": mimetype,
    }
    environ = {"REQUEST_METHOD": "POST"}
    fp = BytesIO(bcontent)
    return cgi_FieldStorage(fp=fp, headers=headers, environ=environ)  # type: ignore[call-arg]


class MyWebAppWorker(WebAppWorkerBase):
    """A class to provide access to methods for testing"""

    def setSemaphore(self) -> str:
        return str(self._setSemaphore())

    def openSemaphoreLog(self, semaphore: str = "TMP_") -> None:
        self._openSemaphoreLog(semaphore)

    def closeSemaphoreLog(self, semaphore: str = "TMP_") -> None:
        self._closeSemaphoreLog(semaphore)

    def postSemaphore(self, semaphore: str = "TMP_", value: str = "OK") -> str:
        return str(self._postSemaphore(semaphore, value))

    def semaphoreExists(self, semaphore: str = "TMP_") -> bool:
        return bool(self._semaphoreExists(semaphore))

    def getSemaphore(self, semaphore: str = "TMP_") -> str:
        return str(self._getSemaphore(semaphore))

    def newSessionOp(self) -> ResponseContent:
        rC: ResponseContent = self._newSessionOp()
        return rC

    def getSession(self, forceNew: bool = False, useContext: bool = False, overWrite: bool = True) -> None:
        self._getSession(forceNew=forceNew, useContext=useContext, overWrite=overWrite)

    def verifySessionContext(self, apikyfn: Callable[[str], bool], overWrite: bool = True) -> bool:
        return bool(self._verifySessionContext(apikyfn, overWrite=overWrite))

    def isFileUpload(self, fileTag: str = "file") -> bool:
        return bool(self._isFileUpload(fileTag))

    def uploadFile(self, fileTag: str = "file") -> str | None:
        ret: str | None = self._uploadFile(fileTag)
        return ret

    def getFileText(self, filePath: str) -> ResponseContent:
        rC: ResponseContent = self._getFileText(filePath)
        return rC

    def saveSessionParameter(
        self,
        param: str | None = None,
        value: Any = None,
        pvD: dict[str, Any] | None = None,
        prefix: str | None = None,
    ) -> bool:
        return bool(self._saveSessionParameter(param, value, pvD, prefix))

    def getSessionParameter(self, param: str | None = None, prefix: str | None = None) -> Any:
        return self._getSessionParameter(param, prefix)

    # Service operations for doOp() dispatch
    @staticmethod
    def okOp() -> ResponseContent:
        rC = ResponseContent()
        rC.setHtmlText("okOp called")
        return rC

    @staticmethod
    def failOp() -> ResponseContent:
        raise ValueError("failOp")  # noqa: EM101


class SessionTests(unittest.TestCase):
    def setUp(self) -> None:
        HERE = os.path.abspath(os.path.dirname(__file__))
        TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
        if not os.path.exists(TESTOUTPUT):  # pragma: no cover
            os.makedirs(TESTOUTPUT)
        self.__sessiontop = TESTOUTPUT
        sdir = os.path.join(self.__sessiontop, "sessions")
        if not os.path.exists(sdir):  # pragma: no cover
            os.makedirs(sdir)

        fname = os.path.join(HERE, "WebAppWorkerBaseTests.py")
        with open(fname) as fin:
            content = fin.read()
        fs = _create_fs("text", content, filename=fname)
        self.__paramDict: dict[str, list[Any]] = {
            "TopSessionPath": [self.__sessiontop],
            "request_path": ["service/testpath"],
            "file": [fs],
        }
        self.__reffile = fname

    def testWebappWorkerSemaphore(self) -> None:
        """Tests WebAppWorker semaphore"""
        reqObj = InputRequest(self.__paramDict)
        app = MyWebAppWorker(reqObj, verbose=True)
        self.assertIsNotNone(app.newSessionOp())

        # Semaphore testing
        sem = app.setSemaphore()
        self.assertTrue(sem.startswith("TMP_"))
        self.assertEqual(reqObj.getSemaphore(), sem)
        self.assertFalse(app.semaphoreExists())
        self.assertEqual(app.getSemaphore(), "FAIL")
        # This redirects class self._lfh
        app.openSemaphoreLog()
        self.assertEqual(app.postSemaphore(value="Working"), "TMP_")
        self.assertTrue(app.semaphoreExists())
        self.assertEqual(app.getSemaphore(), "Working")
        app.closeSemaphoreLog()

    def testWebappWorkerUpload(self) -> None:
        """Tests WebAppWorker upload file"""
        reqObj = InputRequest(self.__paramDict)
        app = MyWebAppWorker(reqObj, verbose=True)
        self.assertIsNotNone(app.newSessionOp())

        # File uploaded
        sObj = reqObj.getSessionObj()
        sesspath = cast("str", sObj.getPath())
        self.assertTrue(app.isFileUpload())
        self.assertEqual(app.uploadFile(), "WebAppWorkerBaseTests.py")
        # Ensure present
        dst = os.path.join(sesspath, "WebAppWorkerBaseTests.py")
        self.assertTrue(os.path.exists(dst))
        self.assertTrue(filecmp.cmp(dst, self.__reffile))
        self.assertEqual(reqObj.getValue("filePath"), dst)
        self.assertEqual(reqObj.getValue("fileName"), "WebAppWorkerBaseTests.py")

    def testWebappWorkerParameter(self) -> None:
        """Tests WebAppWorker parameter setting"""
        reqObj = InputRequest(self.__paramDict)
        app = MyWebAppWorker(reqObj, verbose=True)
        self.assertIsNotNone(app.newSessionOp())

        self.assertTrue(app.saveSessionParameter("test", "5", {"value1": 2, "value2": 3}))
        self.assertEqual(app.getSessionParameter("test"), "5")
        self.assertEqual(app.getSessionParameter("value1"), 2)
        self.assertEqual(app.getSessionParameter("value2"), 3)


class WebAppWorkerTests(unittest.TestCase):
    """Tests using an isolated temporary session tree"""

    def setUp(self) -> None:
        self.tmpDir = tempfile.mkdtemp()
        self.log = StringIO()
        self.reqObj = InputRequest({})

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpDir, ignore_errors=True)

    def makeApp(self, extra: dict[str, list[Any]] | None = None, verbose: bool = True) -> MyWebAppWorker:
        paramDict: dict[str, list[Any]] = {"TopSessionPath": [self.tmpDir], "return_format": ["json"]}
        if extra:
            paramDict.update(extra)
        self.reqObj = InputRequest(paramDict)
        return MyWebAppWorker(self.reqObj, verbose=verbose, log=self.log)

    @staticmethod
    def responseDict(rC: ResponseContent) -> dict[str, Any]:
        rC.setReturnFormat("json")
        ret: dict[str, Any] = json.loads(rC.get()["RETURN_STRING"])
        return ret

    def testDoOpUnknown(self) -> None:
        """Tests unknown service"""
        app = self.makeApp({"request_path": ["/service/unknown"]})
        rC = app.doOp()
        self.assertTrue(rC.isError())
        self.assertEqual(self.responseDict(rC)["statustext"], "Unknown operation")

    def testDoOp(self) -> None:
        """Tests service dispatch"""
        app = self.makeApp({"request_path": ["/service/ok"]})
        app.addService("/service/ok", "okOp")
        rC = app.doOp()
        self.assertFalse(rC.isError())
        self.assertEqual(self.responseDict(rC)["htmlcontent"], "okOp called")

    def testDoOpRest(self) -> None:
        """Tests REST style review URL mapping"""
        app = self.makeApp({"request_path": ["/service/review/report/d_1000000001"]})
        app.addServices({"/service/review/report": "okOp", "/service/other": "failOp"})
        rC = app.doOp()
        self.assertFalse(rC.isError())
        self.assertEqual(self.reqObj.getValue("idcode"), "D_1000000001")

    def testDoOpFailure(self) -> None:
        """Tests failing service and service mapped to missing method"""
        app = self.makeApp({"request_path": ["/service/fail"]})
        app.addServices({"/service/fail": "failOp", "/service/missing": "noSuchOp"})
        rC = app.doOp()
        self.assertTrue(rC.isError())
        self.assertEqual(self.responseDict(rC)["statustext"], "Operation failure")
        self.assertIn("ValueError: failOp", self.log.getvalue())

        self.reqObj.setValue("request_path", "/service/missing")
        self.assertTrue(app.doOp().isError())

    def testNewSessionFailure(self) -> None:
        """Tests error returned if no session id assigned"""
        app = self.makeApp()
        with mock.patch.object(InputRequest, "getSessionId", return_value=""):
            rC = app.newSessionOp()
        self.assertTrue(rC.isError())
        self.assertEqual(self.responseDict(rC)["statustext"], "No session created")

    def testGetSessionContext(self) -> None:
        """Tests persisted session parameters imported into the request"""
        app = self.makeApp()
        app.getSession(forceNew=True)
        sessionId = self.reqObj.getSessionId()
        self.assertTrue(app.saveSessionParameter(pvD={"p1": "v1", "p2": "v2"}))

        # New request joining the existing session
        app = self.makeApp({"sessionid": [sessionId], "p2": ["mine"]})
        app.getSession(useContext=True, overWrite=False)
        self.assertEqual(self.reqObj.getSessionId(), sessionId)
        self.assertEqual(self.reqObj.getValue("p1"), "v1")
        self.assertEqual(self.reqObj.getValue("p2"), "mine")

        app.getSession(useContext=True)
        self.assertEqual(self.reqObj.getValue("p2"), "v2")

    def testSessionParameterPrefix(self) -> None:
        """Tests parameters isolated by prefix"""
        app = self.makeApp()
        app.getSession(forceNew=True)
        self.assertTrue(app.saveSessionParameter("p1", "v1", prefix="pre"))
        self.assertEqual(app.getSessionParameter("p1", prefix="pre"), "v1")
        self.assertEqual(app.getSessionParameter("p1"), "")

    def testSessionParameterFailure(self) -> None:
        """Tests data store failures"""
        app = self.makeApp()
        with mock.patch("wwpdb.utils.session.WebAppWorkerBase.UtilDataStore", side_effect=OSError("no store")):
            self.assertFalse(app.saveSessionParameter("p1", "v1"))
            self.assertEqual(app.getSessionParameter("p1"), "")
        self.assertIn("no store", self.log.getvalue())

    def testVerifySessionContext(self) -> None:
        """Tests session context with api key check"""
        app = self.makeApp()
        # No session directory
        self.assertFalse(app.verifySessionContext(lambda _k: True))

        app.getSession(forceNew=True)
        self.assertTrue(app.saveSessionParameter("apikey", "secret"))

        app = self.makeApp({"sessionid": [self.reqObj.getSessionId()]})
        self.assertTrue(app.verifySessionContext(lambda k: k == "secret"))
        self.assertFalse(app.verifySessionContext(lambda k: k == "other"))

        def badKey(_k: str) -> bool:
            raise ValueError("bad key function")  # noqa: EM101,TRY003

        self.assertFalse(app.verifySessionContext(badKey))
        self.assertIn("bad key function", self.log.getvalue())

    def testFileUpload(self) -> None:
        """Tests upload detection, windows paths and failures"""
        app = self.makeApp({"text": ["string"], "file": [_create_fs("text", "content", filename="C:\\dir\\win.txt")]})
        self.assertFalse(app.isFileUpload("text"))
        self.assertTrue(app.isFileUpload("file"))

        # No session yet - cannot store
        self.assertIsNone(app.uploadFile())
        self.assertIn("Upload failed", self.log.getvalue())

        app.getSession(forceNew=True)
        self.assertEqual(app.uploadFile(), "win.txt")
        self.assertTrue(os.path.exists(os.path.join(cast("str", self.reqObj.getSessionObj().getPath()), "win.txt")))

        app = self.makeApp(verbose=False)
        app.getSession(forceNew=True)
        self.assertIsNone(app.uploadFile("missing"))

    def testGetFileText(self) -> None:
        """Tests text file response"""
        fPath = os.path.join(self.tmpDir, "text.txt")
        with open(fPath, "w") as fout:
            fout.write("Some text")
        app = self.makeApp()
        rC = app.getFileText(fPath)
        self.assertEqual(self.reqObj.getReturnFormat(), "text")
        self.assertEqual(rC.get(), {"CONTENT_TYPE": "text/plain", "RETURN_STRING": b"Some text"})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
