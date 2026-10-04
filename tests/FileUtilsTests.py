##
# File: FileUtilsTests.py
# Date:  06-Feb-2021  E. Peisach
#
# Updates:
#  03-Oct-2026  Add typing.  Exercise FileUtils rendering with mocked data access
##
"""Test cases for FileUtils"""

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import shutil
import tempfile
import unittest
from io import StringIO
from typing import Tuple, cast
from unittest import mock

from wwpdb.utils.config.ConfigInfoData import ConfigInfoData

from wwpdb.utils.session.FileUtils import FileUtils
from wwpdb.utils.session.WebRequest import InputRequest

FileTuple = Tuple[str, str, float]


class FileUtilsTestBase(unittest.TestCase):
    """Common setup - FileUtils with data access (DataExchange, PathInfo, ConfigInfo) mocked"""

    def setUp(self) -> None:
        self.tmpDir = tempfile.mkdtemp()
        self.reqObj = InputRequest({"TopSessionPath": [self.tmpDir]})
        sObj = self.reqObj.newSessionObj()
        self.sessionId = cast("str", sObj.getId())
        self.sessionPath = cast("str", sObj.getPath())

        self.deP = mock.patch("wwpdb.utils.session.FileUtils.DataExchange")
        self.piP = mock.patch("wwpdb.utils.session.FileUtils.PathInfo")
        self.ciP = mock.patch("wwpdb.utils.session.FileUtils.ConfigInfo")
        self.mockDE = self.deP.start()
        self.mockPI = self.piP.start()
        self.mockCI = self.ciP.start()
        self.milestones: list[str] = []
        self.mockCI.return_value.get.side_effect = lambda _ky: self.milestones
        self.de = self.mockDE.return_value
        self.de.getContentTypeFileList.return_value = []
        self.de.getLogFileList.return_value = []
        self.de.getMiscFileList.return_value = []

    def tearDown(self) -> None:
        mock.patch.stopall()
        shutil.rmtree(self.tmpDir, ignore_errors=True)

    def makeFileUtils(self, entryId: str = "D_1000000001", verbose: bool = False) -> FileUtils:
        return FileUtils(entryId, reqObj=self.reqObj, verbose=verbose, log=StringIO())

    def requestedContentTypes(self) -> list[str]:
        """Content types requested from DataExchange.getContentTypeFileList()"""
        ret: list[str] = []
        for cl in self.de.getContentTypeFileList.call_args_list:
            ret.extend(cl.kwargs["contentTypeList"])
        return ret


class FileUtilTests(FileUtilsTestBase):
    def getDownloadContentTypes(self, rDList: list[str] | None = None) -> set[str]:
        """Returns the set of content types FileUtils will request for downloads (no milestones)"""
        fu = self.makeFileUtils()
        fu.renderFileList(fileSource="archive", rDList=rDList)
        return set(self.requestedContentTypes())

    def testDownloadTypes(self) -> None:
        """Tests Download Types vs known in ConfigInfoData to prevent issues"""
        cttypes = self.getDownloadContentTypes()
        self.assertIn("model", cttypes)

        cId = ConfigInfoData(verbose=False, useCache=False)
        configDict = cId.getConfigDictionary()
        knownContentTypes = configDict["CONTENT_TYPE_BASE_DICTIONARY"]

        for ct in cttypes:
            self.assertIn(ct, knownContentTypes, "%s not in known content types" % ct)

    def testRestrictedList(self) -> None:
        """Tests only the requested categories are rendered, unknown categories ignored"""
        cttypes = self.getDownloadContentTypes(rDList=["Message Files", "Not a category"])
        self.assertEqual(
            cttypes,
            {"messages-from-depositor", "messages-to-depositor", "notes-from-annotator", "correspondence-to-depositor"},
        )
        self.assertEqual(self.de.getContentTypeFileList.call_count, 1)

    def testMilestones(self) -> None:
        """Tests milestone variants of content types are requested"""
        self.milestones = ["upload", "deposit"]
        fu = self.makeFileUtils()
        fu.renderFileList(fileSource="deposit", rDList=["Message Files"])
        cttypes = self.requestedContentTypes()
        self.assertIn("messages-to-depositor", cttypes)
        self.assertIn("messages-to-depositor-upload", cttypes)
        self.assertIn("messages-to-depositor-deposit", cttypes)

    def testSiteId(self) -> None:
        """Tests validation server site id remapping"""
        self.reqObj.setValue("WWPDB_SITE_ID", "WWPDB_DEPLOY_TEST")
        self.makeFileUtils(entryId="D_9000000001")
        self.mockCI.assert_called_with("WWPDB_DEPLOY_VALSRV_RU")

        self.makeFileUtils(entryId="D_1000000001")
        self.mockCI.assert_called_with("WWPDB_DEPLOY_TEST")

        self.reqObj.setValue("WWPDB_SITE_ID", "WWPDB_DEPLOY_OTHER")
        self.makeFileUtils(entryId="D_9000000001")
        self.mockCI.assert_called_with("WWPDB_DEPLOY_OTHER")

    def testRenderArchive(self) -> None:
        """Tests rendering of archive file listings including log files"""
        modelPath = "/archive/D_1000000001/D_1000000001_model_P1.cif.V1"
        logPath = "/archive/D_1000000001/log/D_1000000001_run.log"

        def ctList(fileSource: str, contentTypeList: list[str]) -> list[FileTuple]:  # noqa: ARG001 pylint: disable=unused-argument
            if "model" in contentTypeList:
                return [(modelPath, "2026-01-01 10:00:00", 12.7)]
            return []

        self.de.getContentTypeFileList.side_effect = ctList
        self.de.getLogFileList.return_value = [(logPath, "2026-01-02 10:00:00", 0.25)]

        fu = self.makeFileUtils(verbose=True)
        nTot, htmlList = fu.renderFileList(fileSource="archive", titlePrefix="Pre ", titleSuffix=" Post")
        self.assertEqual(nTot, 2)
        html = "\n".join(htmlList)
        self.assertIn("Pre Primary Data Files Post", html)
        self.assertIn("Archive Log Files", html)
        self.assertIn("D_1000000001_model_P1.cif.V1</a>", html)
        self.assertIn("sessionid=%s&file_path=%s" % (self.sessionId, modelPath), html)
        self.assertIn("<td>12</td>", html)
        self.assertIn("<td>0.250</td>", html)
        self.de.getLogFileList.assert_called_once_with("D_1000000001", fileSource="archive")

    def testRenderDeposit(self) -> None:
        """Tests deposit log files rendered"""
        self.de.getLogFileList.return_value = [("/deposit/x.log", "2026-01-02", 3.0)]
        fu = self.makeFileUtils()
        nTot, htmlList = fu.renderFileList(fileSource="deposit")
        self.assertEqual(nTot, 1)
        self.assertIn("Deposit Log Files", "\n".join(htmlList))
        self.de.getLogFileList.assert_called_once_with("D_1000000001", fileSource="deposit")

    def testRenderEmpty(self) -> None:
        """Tests nothing returned when no files found or unknown source"""
        fu = self.makeFileUtils()
        self.assertEqual(fu.renderFileList(fileSource="archive"), (0, []))
        self.assertEqual(fu.renderFileList(fileSource="unknown"), (0, []))

    def testDisplayImage(self) -> None:
        """Tests image symlinked into session and embedded"""
        imgSrc = os.path.join(self.tmpDir, "D_1000000001_img-emdb_P1.png.V1")
        with open(imgSrc, "w") as fout:
            fout.write("image")

        def ctList(fileSource: str, contentTypeList: list[str]) -> list[FileTuple]:  # noqa: ARG001 pylint: disable=unused-argument
            if "img-emdb" in contentTypeList:
                return [(imgSrc, "2026-01-01", 1.5)]
            return []

        self.de.getContentTypeFileList.side_effect = ctList
        fu = self.makeFileUtils()
        dst = os.path.join(self.sessionPath, os.path.basename(imgSrc))
        # Run twice - second time replaces existing link
        for _ in range(2):
            _nTot, htmlList = fu.renderFileList(fileSource="archive", displayImageFlag=True)
            self.assertTrue(os.path.islink(dst))
            html = "\n".join(htmlList)
            self.assertIn('<img src="/sessions/%s/%s"' % (self.sessionId, os.path.basename(imgSrc)), html)
            self.assertIn('colspan="3"', html)

    def testRenderInstance(self) -> None:
        """Tests workflow instance file listing"""
        instTop = os.path.join(self.tmpDir, "instance")
        for wf in ["W_000001", "W_000002"]:
            os.makedirs(os.path.join(instTop, wf))
        # A plain file should be ignored
        with open(os.path.join(instTop, "notadir"), "w") as fout:
            fout.write("x")
        self.mockPI.return_value.getInstanceTopPath.return_value = instTop

        def miscList(fPatternList: list[str], sortFlag: bool) -> list[FileTuple]:  # noqa: ARG001 pylint: disable=unused-argument
            if "W_000001" in fPatternList[0]:
                return [(os.path.join(instTop, "W_000001", "a.cif"), "2026-01-01", 2.0)]
            return []

        self.de.getMiscFileList.side_effect = miscList
        fu = self.makeFileUtils(verbose=True)
        nTot, htmlList = fu.renderFileList(fileSource="wf-instance")
        self.assertEqual(nTot, 1)
        html = "\n".join(htmlList)
        self.assertIn("Files in W_000001", html)
        self.assertNotIn("W_000002", html)
        self.assertEqual(self.de.getMiscFileList.call_count, 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
