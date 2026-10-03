##
# File: WebRequestsTests.py
# Date:  07-Jan-2020  E. Peisach
#
# Updates:
#  03-Oct-2026  Add typing.  Test file iterator, binary/jsonp responses, templates and failure paths
##
"""Test cases for WebRequests"""

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import gzip
import json
import os
import platform
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from io import StringIO
from typing import Any
from unittest import mock

from wwpdb.utils.session.WebRequest import (
    FileIterator,
    InputRequest,
    ResponseContent,
    WebRequest,
    json_serializer_helper,
)


class MyWebRequest(WebRequest):
    """A class to provide access to methods for testing"""

    def getIntegerValue(self, myKey: str) -> int | None:
        ret: int | None = self._getIntegerValue(myKey)
        return ret

    def getDoubleValue(self, myKey: str) -> float | None:
        ret: float | None = self._getDoubleValue(myKey)
        return ret


class Unprintable:
    """Object which cannot be converted to a string"""

    def __str__(self) -> str:
        raise ValueError("no string")


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

    def testWebRequest(self) -> None:
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

    def testWebRequestMissing(self) -> None:
        """Tests access to missing or invalid values"""
        wr = MyWebRequest()
        wr.setValue("str", "abc")
        self.assertEqual(wr.getValue("missing"), "")
        self.assertIsNone(wr.getRawValue("missing"))
        self.assertEqual(wr.getValueList("missing"), [])
        self.assertIsNone(wr.getIntegerValue("missing"))
        self.assertIsNone(wr.getIntegerValue("str"))
        self.assertIsNone(wr.getDoubleValue("str"))

    def testWebRequestOutput(self) -> None:
        """Tests printIt/dump contents"""
        wr = WebRequest({"b": ["2"], "a": ["1"]})
        out = StringIO()
        wr.printIt(ofh=out)
        txt = out.getvalue()
        self.assertLess(txt.index("Key: a"), txt.index("Key: b"))
        dL = wr.dump()
        self.assertNotIn("<pre>\n", dL)
        self.assertEqual(wr.dump(format="html")[0], "<pre>\n")

    def testSetDictionary(self) -> None:
        """Tests setDictionary overwrite control"""
        wr = WebRequest()
        wr.setValue("k1", "orig")
        wr.setDictionary({"k1": "new", "k2": "v2"})
        self.assertEqual(wr.getValue("k1"), "orig")
        self.assertEqual(wr.getValue("k2"), "v2")
        wr.setDictionary({"k1": "new"}, overWrite=True)
        self.assertEqual(wr.getValue("k1"), "new")

    def testInputRequest(self) -> None:
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

    def testInputRequestSession(self) -> None:
        """Tests joining existing sessions and defaults"""
        ir = InputRequest({"TopSessionPath": [self.__sessiontop]})
        ir.setDefaultReturnFormat("json")
        self.assertEqual(ir.getReturnFormat(), "json")
        # Existing format not replaced by default
        ir.setDefaultReturnFormat("html")
        self.assertEqual(ir.getReturnFormat(), "json")

        sid = ir.newSessionObj().getId()
        sObj = ir.newSessionObj()
        self.assertEqual(sObj.getId(), sid)
        self.assertEqual(ir.getSessionPath(), os.path.join(self.__sessiontop, "sessions"))
        self.assertEqual(ir.getTopSessionPath(), self.__sessiontop)

        # No session path provided - defaults to current directory
        ir = InputRequest({"sessionid": ["abc"]})
        sObj = ir.getSessionObj()
        self.assertEqual(sObj.getId(), "abc")
        self.assertEqual(sObj.getTopPath(), ".")


class ResponseTests(unittest.TestCase):
    def setUp(self) -> None:
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

    def testResponseConent(self) -> None:
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
        rc.setHtmlTextFromTemplate(os.path.join(self.__HERE, "missingtemplate.txt"), self.__HERE, parameterDict={"T1": 2})

        # Files
        rc.setTextFile(os.path.join(self.__HERE, "template.txt"))
        rc.setHtmlContentPath("https://wwpdb.org")
        self.assertEqual(("text/plain", None), rc.getMimetypeAndEncoding(os.path.join(self.__HERE, "template.txt")))
        rc.setBinaryFile(os.path.join(self.__HERE, "template.txt"))
        rc.wrapFileAsJsonp(os.path.join(self.__HERE, "template.txt"), "")
        rc.setReturnFormat("binary")
        rc.get()

        self.assertIn("dump", rc.dump()[0])


class ResponseContentTests(unittest.TestCase):
    """Detailed ResponseContent behaviour - content is verified through the public get() interface"""

    def setUp(self) -> None:
        self.HERE = os.path.abspath(os.path.dirname(__file__))
        self.tmpDir = tempfile.mkdtemp()
        self.log = StringIO()
        self.content = b"Line of text\n" * 10
        self.txtFile = os.path.join(self.tmpDir, "file.txt")
        with open(self.txtFile, "wb") as fout:
            fout.write(self.content)
        self.gzFile = os.path.join(self.tmpDir, "file.txt.gz")
        with gzip.open(self.gzFile, "wb") as gout:
            gout.write(self.content)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpDir, ignore_errors=True)

    def makeRC(self, verbose: bool = True) -> ResponseContent:
        return ResponseContent(verbose=verbose, log=self.log)

    @staticmethod
    def contentDict(rc: ResponseContent) -> dict[str, Any]:
        """Return the response content dictionary via a json response"""
        rc.setReturnFormat("json")
        ret: dict[str, Any] = json.loads(rc.get()["RETURN_STRING"])
        return ret

    def testDefaults(self) -> None:
        """Tests response without request object"""
        rc = ResponseContent()
        self.assertEqual(rc.get(), {})
        cD = self.contentDict(rc)
        self.assertEqual(cD["sessionid"], "")
        self.assertEqual(cD["semaphore"], "")
        self.assertFalse(cD["errorflag"])

    def testDefaultsFromRequest(self) -> None:
        """Tests session id, semaphore and return format taken from request"""
        reqObj = InputRequest({"sessionid": ["abc"], "semaphore": ["sem"], "return_format": ["location"]})
        rc = ResponseContent(reqObj)
        rc.setLocation("https://wwpdb.org")
        self.assertEqual(rc.get(), {"CONTENT_TYPE": "location", "RETURN_STRING": "https://wwpdb.org"})
        cD = self.contentDict(rc)
        self.assertEqual(cD["sessionid"], "abc")
        self.assertEqual(cD["semaphore"], "sem")

    def testReturnFormat(self) -> None:
        rc = self.makeRC()
        self.assertTrue(rc.setReturnFormat("html"))
        self.assertFalse(rc.setReturnFormat("bogus"))
        rc.setHtmlText("hello")
        self.assertEqual(rc.get(), {"CONTENT_TYPE": "text/html", "RETURN_STRING": "hello"})

    def testSetters(self) -> None:
        rc = self.makeRC()
        rc.setText("text")
        rc.setHtmlLinkText("link")
        rc.addDictionaryItems({"extra1": 1, "extra2": [2]})
        rc.addDictionaryItems()
        rc.set("asjson", {"a": 1}, asJson=True)
        rc.setStatus("all good", semaphore="s1")
        rc.setStatusCode(200)
        rc.setHtmlContentPath("/path")
        cD = self.contentDict(rc)
        self.assertEqual(cD["textcontent"], "text")
        self.assertEqual(cD["htmllinkcontent"], "link")
        self.assertEqual(cD["extra1"], 1)
        self.assertEqual(cD["extra2"], [2])
        self.assertEqual(json.loads(cD["asjson"]), {"a": 1})
        self.assertEqual(cD["statustext"], "all good")
        self.assertEqual(cD["semaphore"], "s1")
        self.assertEqual(cD["statuscode"], 200)
        self.assertEqual(cD["htmlcontentpath"], "/path")

    def testHtmlList(self) -> None:
        rc = self.makeRC()
        rc.setReturnFormat("html")
        rc.appendHtmlList()
        rc.appendHtmlList(["a", "b"])
        rc.appendHtmlList(["c"])
        self.assertEqual(rc.get()["RETURN_STRING"], "a\nb\nc")
        rc.setHtmlList()
        self.assertEqual(rc.get()["RETURN_STRING"], "")

    def testErrorResponses(self) -> None:
        """Tests html and text responses return status on error"""
        rc = self.makeRC()
        rc.setHtmlText("html")
        rc.setText("text")
        rc.setError("bad", semaphore="sem")
        for fmt in ["html", "text"]:
            rc.setReturnFormat(fmt)
            self.assertEqual(rc.get(), {"CONTENT_TYPE": "text/html", "RETURN_STRING": "bad"})
        cD = self.contentDict(rc)
        self.assertEqual(cD["errortext"], "bad")
        self.assertEqual(cD["semaphore"], "sem")

        rc.setReturnFormat("jsonText")
        rD = rc.get()
        self.assertEqual(rD["CONTENT_TYPE"], "text/html")
        self.assertTrue(rD["RETURN_STRING"].startswith("<textarea>"))
        self.assertTrue(rD["RETURN_STRING"].endswith("</textarea>"))

    def testSetJsonFailure(self) -> None:
        """Tests failure to serialize value logged"""
        rc = self.makeRC()
        rc.set("bad", [Unprintable()], asJson=True)
        self.assertIn("+set() failed", self.log.getvalue())
        self.assertNotIn("bad", self.contentDict(rc))

    def testJsonSerializerHelper(self) -> None:
        d = datetime(2026, 10, 3, 12, 30)  # noqa: DTZ001
        self.assertEqual(json_serializer_helper(d), "2026-10-03T12:30:00")
        self.assertEqual(json_serializer_helper(5), "5")
        with self.assertRaises(TypeError):
            json_serializer_helper(Unprintable())

    def testMimetype(self) -> None:
        self.assertEqual(ResponseContent.getMimetypeAndEncoding("a.cif.V1"), ("text/plain", None))
        self.assertEqual(ResponseContent.getMimetypeAndEncoding("a.unknownext"), ("application/octet-stream", None))
        self.assertEqual(ResponseContent.getMimetypeAndEncoding("a.txt.gz"), ("text/plain", "gzip"))

    def testTextFile(self) -> None:
        rc = self.makeRC()
        rc.setReturnFormat("text")
        rc.setTextFile(os.path.join(self.tmpDir, "missing.txt"))
        self.assertEqual(rc.get(), {"CONTENT_TYPE": "text/plain", "RETURN_STRING": ""})
        rc.setTextFile(self.txtFile)
        self.assertEqual(rc.get(), {"CONTENT_TYPE": "text/plain", "RETURN_STRING": self.content})
        rc.setTextFileO(self.txtFile)
        self.assertEqual(rc.get()["RETURN_STRING"], self.content.decode("ascii"))

    def testTextFileFailure(self) -> None:
        rc = self.makeRC()
        with mock.patch("builtins.open", side_effect=OSError("cannot open")):
            rc.setTextFile(self.txtFile)
        self.assertIn("File read failed", self.log.getvalue())

    def testBinaryFile(self) -> None:
        rc = self.makeRC()
        rc.setReturnFormat("binary")
        rc.setBinaryFile(self.txtFile)
        self.assertEqual(
            rc.get(),
            {
                "CONTENT_TYPE": "text/plain",
                "RETURN_STRING": self.content,
                "ENCODING": None,
                "DISPOSITION": "inline; filename=file.txt",
            },
        )
        rc.setBinaryFile(self.txtFile, attachmentFlag=True)
        self.assertEqual(rc.get()["DISPOSITION"], "attachment; filename=file.txt")

    def testBinaryFileGzip(self) -> None:
        with open(self.gzFile, "rb") as fin:
            gzContent = fin.read()
        # Served compressed as attachment
        rc = self.makeRC()
        rc.setReturnFormat("binary")
        rc.setBinaryFile(self.gzFile, attachmentFlag=True)
        self.assertEqual(
            rc.get(),
            {
                "CONTENT_TYPE": "application/octet-stream",
                "RETURN_STRING": gzContent,
                "ENCODING": None,
                "DISPOSITION": "attachment; filename=file.txt.gz",
            },
        )
        # Inline - file extension stripped
        rc.setBinaryFile(self.gzFile)
        self.assertEqual(rc.get()["DISPOSITION"], "inline; filename=file.txt")

        # Served with gzip encoding
        rc = self.makeRC()
        rc.setReturnFormat("binary")
        rc.setBinaryFile(self.gzFile, attachmentFlag=True, serveCompressed=False)
        self.assertEqual(
            rc.get(),
            {
                "CONTENT_TYPE": "text/plain",
                "RETURN_STRING": gzContent,
                "ENCODING": "gzip",
                "DISPOSITION": "attachment; filename=file.txt",
            },
        )

    def testBinaryFileMissing(self) -> None:
        rc = self.makeRC()
        rc.setReturnFormat("binary")
        rc.setBinaryFile(os.path.join(self.tmpDir, "missing.txt"))
        self.assertEqual(rc.get(), {"CONTENT_TYPE": None, "RETURN_STRING": None, "ENCODING": None})

    def testBinaryFileFailure(self) -> None:
        rc = self.makeRC()
        with mock.patch("builtins.open", side_effect=OSError("cannot open")):
            rc.setBinaryFile(self.txtFile)
        self.assertIn("setBinaryFile() File read failed", self.log.getvalue())

    def testMultipart(self) -> None:
        """Tests large files returned with file iterator"""
        with mock.patch.object(ResponseContent, "MULTIPART_THRESHOLD", 10):
            rc = self.makeRC()
            rc.setReturnFormat("binary")
            rc.setBinaryFile(self.txtFile)
            rD = rc.get()
            self.assertIsInstance(rD["FILE_ITERATOR"], FileIterator)
            self.assertNotIn("RETURN_STRING", rD)
            self.assertEqual(b"".join(rD["FILE_ITERATOR"]), self.content)
            self.assertIn("sending as multipart", self.log.getvalue())

            rc = self.makeRC()
            rc.setReturnFormat("text")
            rc.setTextFile(self.txtFile)
            rD = rc.get()
            self.assertEqual(b"".join(rD["FILE_ITERATOR"]), self.content)

            # Compressed file served uncompressed
            rc = self.makeRC()
            rc.setReturnFormat("binary")
            rc.setBinaryFile(self.gzFile, serveCompressed=False)
            fi = rc.get()["FILE_ITERATOR"]
            self.assertEqual(fi.fileSize, len(self.content))
            self.assertEqual(b"".join(fi), self.content)

    def testFileIterator(self) -> None:
        with mock.patch.object(FileIterator, "CHUNK_SIZE", 7):
            fi = FileIterator(self.txtFile, 0)
            self.assertEqual(fi.fileName, "file.txt")
            self.assertEqual(fi.fileSize, len(self.content))
            self.assertIs(iter(fi), fi)
            chunks = list(fi)
            self.assertEqual(len(chunks[0]), 7)
            self.assertEqual(b"".join(chunks), self.content)

            fi = FileIterator(self.gzFile, 5, uncompress=True)
            self.assertEqual(fi.fileSize, len(self.content))
            self.assertEqual(b"".join(fi), self.content)

    def testJsonp(self) -> None:
        rc = self.makeRC()
        rc.setReturnFormat("jsonp")
        rc.wrapFileAsJsonp(self.txtFile, "cb")
        rD = rc.get()
        self.assertEqual(rD["CONTENT_TYPE"], "application/x-javascript")
        self.assertEqual(rD["RETURN_STRING"], "cb(" + json.dumps({"data": self.content.decode("ascii")}) + ");")

        jsFile = os.path.join(self.tmpDir, "data.json")
        with open(jsFile, "w") as fout:
            fout.write('{"a": 1}')
        rc.wrapFileAsJsonp(jsFile, "cb")
        self.assertEqual(rc.get()["RETURN_STRING"], 'cb({"a": 1});')

    def testJsonpFailure(self) -> None:
        rc = self.makeRC()
        # No callback provided
        rc.wrapFileAsJsonp(self.txtFile)
        self.assertIn("wrapFileAsJsonp() File read failed", self.log.getvalue())

    def testTemplate(self) -> None:
        rc = self.makeRC()
        rc.setReturnFormat("html")
        rc.setHtmlTextFromTemplate(os.path.join(self.HERE, "template.txt"), self.HERE, parameterDict={"T1": "VAL"})
        html = rc.get()["RETURN_STRING"]
        self.assertIn("Subsitute the value VAL here", html)
        self.assertIn("This should be inserted in template", html)

    def testTemplateInsert(self) -> None:
        tFile = os.path.join(self.tmpDir, "template.html")
        with open(tFile, "w") as fout:
            fout.write('<!--#insert virtual="/includetest.txt"-->\n')
            fout.write('<!--#include virtual="/missing.txt"-->\n')
            fout.write("End\n")
        rc = self.makeRC()
        rc.setReturnFormat("html")
        rc.setHtmlTextFromTemplate(tFile, self.HERE, insertContext=True)
        html = rc.get()["RETURN_STRING"]
        self.assertIn("This should be inserted in template", html)
        self.assertIn("End", html)
        self.assertIn("failed to include", self.log.getvalue())

        # Without context the insert line is left in place
        rc.setHtmlTextFromTemplate(tFile, self.HERE)
        html = rc.get()["RETURN_STRING"]
        self.assertIn("<!--#insert", html)

    def testTemplateFailure(self) -> None:
        rc = self.makeRC()
        rc.setReturnFormat("html")
        rc.setHtmlTextFromTemplate(os.path.join(self.tmpDir, "missing.html"), self.HERE)
        self.assertEqual(rc.get()["RETURN_STRING"], "")
        self.assertIn("__processTemplate() failed", self.log.getvalue())

    def testDump(self) -> None:
        rc = self.makeRC()
        rc.setHtmlText("x" * 50)
        rc.addDictionaryItems({"adict": {"k": "v"}})
        dump = "".join(rc.dump(maxLength=10))
        self.assertIn("value(1-10): xxxxxxxxxx\n", dump)
        self.assertIn("dict : [('k', 'v')]", dump)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
