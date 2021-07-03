##
# File: WebAppWorkerBaseTests.py
# Date:  09-Jan-2020  E. Peisach
#
# Updates:
##
"""Test cases for WebAppWorkerBaseTests
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import unittest
import platform
import cgi
from io import BytesIO
import filecmp

from wwpdb.utils.session.WebAppWorkerBase import WebAppWorkerBase
from wwpdb.utils.session.WebRequest import InputRequest


# The following is from https://stackoverflow.com/questions/12032807/how-to-create-cgi-fieldstorage-for-testing-purposes
def _create_fs(mimetype, content, filename="uploaded.txt", name="file"):
    content = content.encode("utf-8")
    headers = {u"content-disposition": u'form-data; name="{}"; filename="{}"'.format(name, filename), u"content-length": len(content), u"content-type": mimetype}
    environ = {"REQUEST_METHOD": "POST"}
    fp = BytesIO(content)
    return cgi.FieldStorage(fp=fp, headers=headers, environ=environ)


class MyWebAppWorker(WebAppWorkerBase):
    """A class to provide access to methods for testing"""

    def setSemaphore(self):
        return self._setSemaphore()

    def openSemaphoreLog(self, semaphore="TMP_"):
        return self._openSemaphoreLog(semaphore)

    def closeSemaphoreLog(self, semaphore="TMP_"):
        return self._closeSemaphoreLog(semaphore)

    def postSemaphore(self, semaphore="TMP_", value="OK"):
        return self._postSemaphore(semaphore, value)

    def semaphoreExists(self, semaphore="TMP_"):
        return self._semaphoreExists(semaphore)

    def getSemaphore(self, semaphore="TMP_"):
        return self._getSemaphore(semaphore)

    def newSessionOp(self):
        return self._newSessionOp()

    def uploadFile(self, fileTag="file"):
        return self._uploadFile(fileTag)

    def saveSessionParameter(self, param=None, value=None, pvD=None, prefix=None):
        return self._saveSessionParameter(param, value, pvD, prefix)

    def getSessionParameter(self, param=None, prefix=None):
        return self._getSessionParameter(param, prefix)


class SessionTests(unittest.TestCase):
    def setUp(self):
        HERE = os.path.abspath(os.path.dirname(__file__))
        TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
        if not os.path.exists(TESTOUTPUT):  # pragma: no cover
            os.makedirs(TESTOUTPUT)
        self.__sessiontop = TESTOUTPUT
        sdir = os.path.join(self.__sessiontop, "sessions")
        if not os.path.exists(sdir):  # pragma: no cover
            os.makedirs(sdir)

        fname = os.path.join(HERE, "WebAppWorkerBaseTests.py")
        with open(fname, "r") as fin:
            content = fin.read()
        fs = _create_fs("text", content, filename=fname)
        self.__paramDict = {"TopSessionPath": [self.__sessiontop], "request_path": ["service/testpath"], "file": [fs]}
        self.__reffile = fname

    def testWebappWorkerSemaphore(self):
        """Tests WebAppWorker semaphore"""
        reqObj = InputRequest(self.__paramDict)
        app = MyWebAppWorker(reqObj, verbose=True)
        self.assertIsNotNone(app.newSessionOp())

        # Semaphore testing
        app.setSemaphore()
        self.assertFalse(app.semaphoreExists())
        # This redirects class self._lfh
        app.openSemaphoreLog()
        app.postSemaphore(value="Working")
        self.assertTrue(app.semaphoreExists())
        self.assertEqual(app.getSemaphore(), "Working")
        app.closeSemaphoreLog()

    def testWebappWorkerUpload(self):
        """Tests WebAppWorker upload file"""
        reqObj = InputRequest(self.__paramDict)
        app = MyWebAppWorker(reqObj, verbose=True)
        self.assertIsNotNone(app.newSessionOp())

        # File uploaded
        sObj = reqObj.getSessionObj()
        sesspath = sObj.getPath()
        app.uploadFile()
        # Ensure present
        dst = os.path.join(sesspath, "WebAppWorkerBaseTests.py")
        self.assertTrue(os.path.exists(dst))
        self.assertTrue(filecmp.cmp(dst, self.__reffile))

    def testWebappWorkerParameter(self):
        """Tests WebAppWorker parameter setting"""
        reqObj = InputRequest(self.__paramDict)
        app = MyWebAppWorker(reqObj, verbose=True)
        self.assertIsNotNone(app.newSessionOp())

        self.assertTrue(app.saveSessionParameter("test", "5", {"value1": 2, "value2": 3}))
        self.assertEqual(app.getSessionParameter("test"), "5")
        self.assertEqual(app.getSessionParameter("value1"), 2)
        self.assertEqual(app.getSessionParameter("value2"), 3)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
