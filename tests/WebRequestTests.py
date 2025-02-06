##
# File: WebRequestsTests.py
# Date:  07-Jan-2020  E. Peisach
#
# Updates:
##
"""Test cases for WebRequests"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import platform
import sys
import unittest
from datetime import datetime

from wwpdb.utils.session.WebRequest import InputRequest, ResponseContent, WebRequest


class MyWebRequest(WebRequest):
    """A class to provide access to methods for testing"""

    def getIntegerValue(self, myKey):
        return self._getIntegerValue(myKey)

    def getDoubleValue(self, myKey):
        return self._getDoubleValue(myKey)


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

    def testWebRequest(self):
        """Tests WebRequest access"""

        # No parameters
        wr = WebRequest()
        self.assertIn("WebRequest.printIt", str(wr))

        # With parameters to test code paths
        paramDict = {"TopSessionPath": [self.__sessiontop], "request_path": ["service/testpath"]}
        wr = WebRequest(paramDict)
        self.assertIn("WebRequest.printIt", str(wr))
        self.assertIn("WebRequest.printIt", repr(wr))
        wr.setValue("key1", "5")
        wr.setValueList("key2", ["6"])
        wr.printIt()
        self.assertIsInstance(wr.dump(format="html"), list)
        wr.setDictionary({"key3": "6", "key2": "string"})
        self.assertTrue(wr.exists("key3"))
        self.assertFalse(wr.exists("unknownkey"))
        js = wr.getJSON()
        wr.setJSON(js)
        self.assertEqual(wr.getValue("key1"), "5")
        self.assertEqual(wr.getValueOrDefault("key99", 7), 7)
        self.assertEqual(wr.getValueOrDefault("key1", 7), "5")
        # Empty spaces stripped
        wr.setValue("keyempty", " ")
        self.assertEqual(wr.getValueOrDefault("keyempty", "7"), "7")

        self.assertEqual(wr.getRawValue("key1"), "5")
        self.assertEqual(wr.getValueList("key1"), ["5"])

        self.assertIsInstance(wr.getDictionary(), dict)

        mywr = MyWebRequest()
        mywr.setValue("key1", 5)
        mywr.setValue("key2", "5")
        mywr.setValue("key3", "2.5")
        self.assertEqual(mywr.getIntegerValue("key1"), 5)
        self.assertEqual(mywr.getIntegerValue("key2"), 5)
        self.assertEqual(mywr.getDoubleValue("key3"), 2.5)

    def testInputRequest(self):
        """Tests InputRequest access"""

        paramDict = {"TopSessionPath": [self.__sessiontop], "request_path": ["service/testpath"]}
        ir = InputRequest(paramDict)
        # Test return format
        self.assertEqual(ir.getReturnFormat(), "")
        ir.setDefaultReturnFormat("html")
        ir.setReturnFormat("html")
        self.assertEqual(ir.getReturnFormat(), "html")
        self.assertEqual(ir.getRequestPath(), "service/testpath")
        sObj = ir.newSessionObj()
        self.assertNotEqual("", ir.getSessionId())
        self.assertIsNotNone(ir.getSessionPath())
        self.assertIsNotNone(ir.getTopSessionPath())
        # No semaphore available in this interface
        self.assertEqual(ir.getSemaphore(), "")
        sid = sObj.getId()
        self.assertIsNotNone(sid)
        sObj = ir.getSessionObj()
        self.assertEqual(sid, sObj.getId())
        sObj = ir.newSessionObj(forceNew=True)
        sid = sObj.getId()
        self.assertIsNotNone(sid)


class ResponseTests(unittest.TestCase):
    def setUp(self):
        HERE = os.path.abspath(os.path.dirname(__file__))
        TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
        if not os.path.exists(TESTOUTPUT):  # pragma: no cover
            os.makedirs(TESTOUTPUT)
        self.__sessiontop = TESTOUTPUT
        sdir = os.path.join(self.__sessiontop, "sessions")
        if not os.path.exists(sdir):  # pragma: no cover
            os.makedirs(sdir)
        self.__paramDict = {"TopSessionPath": [self.__sessiontop], "request_path": ["service/testpath"]}
        self.__HERE = HERE

    def testResponseConent(self):
        """Tests WebRequest access"""
        reqObj = InputRequest(self.__paramDict)
        rc = ResponseContent(reqObj)

        rc.setData(["test"])
        rc.setReturnFormat("jsonData")
        self.assertEqual(rc.get(), {"CONTENT_TYPE": "application/json", "RETURN_STRING": '["test"]'})

        # ResponseContent
        d = datetime.now()  # noqa: DTZ005
        rc.set("date", d, asJson=True)
        rc.set("Other", "value")
        rc.setReturnFormat("json")
        self.assertNotEqual(rc.get(), "")

        # Misc adds
        rc.appendHtmlList(["<p>Maybe</p>", "<p>There</p>"])
        rc.setHtmlList(["<p>Hello</p>", "<p>There</p>"])
        rc.appendHtmlList(["<p>Added</p>"])
        rc.setHtmlText("Some text")
        rc.setLocation("https://wwpdb.org")
        rc.setReturnFormat("html")
        self.assertNotEqual(rc.get(), "")
        rc.setReturnFormat("text")
        self.assertNotEqual(rc.get(), "")
        rc.setReturnFormat("json")
        self.assertNotEqual(rc.get(), "")
        rc.setReturnFormat("jsonText")
        self.assertNotEqual(rc.get(), "")
        rc.setReturnFormat("jsonData")
        self.assertNotEqual(rc.get(), "")
        rc.setReturnFormat("location")
        self.assertNotEqual(rc.get(), "")
        rc.setReturnFormat("jsonp")
        self.assertNotEqual(rc.get(), "")
        rc.setReturnFormat("jsonText")
        self.assertNotEqual(rc.get(), "")

        # Error handling
        rc.setStatus("ok")
        self.assertFalse(rc.isError())
        rc.setError("failed to compute")
        self.assertTrue(rc.isError())
        rc.setStatusCode("ok")

        # Templates
        rc.setHtmlTextFromTemplate(os.path.join(self.__HERE, "template.txt"), self.__HERE, parameterDict={"T1": 2})
        sys.stderr.write("%s\n" % rc.dump())
        # Should error
        rc.setHtmlTextFromTemplate(
            os.path.join(self.__HERE, "missingtemplate.txt"), self.__HERE, parameterDict={"T1": 2}
        )

        # Files
        rc.setTextFile(os.path.join(self.__HERE, "template.txt"))
        rc.setHtmlContentPath("https://wwpdb.org")
        self.assertEqual(("text/plain", None), rc.getMimetypeAndEncoding(os.path.join(self.__HERE, "template.txt")))
        rc.setBinaryFile(os.path.join(self.__HERE, "template.txt"))
        rc.wrapFileAsJsonp(os.path.join(self.__HERE, "template.txt"), "")
        rc.setReturnFormat("binary")
        rc.get()

        self.assertIn("dump", rc.dump()[0])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
