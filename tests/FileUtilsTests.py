##
# File: FileUtilsTests.py
# Date:  06-Feb-2021  E. Peisach
#
# Updates:
##
"""Test cases for FileUtils"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest

from wwpdb.utils.config.ConfigInfoData import ConfigInfoData
from wwpdb.utils.session.FileUtils import FileUtilsBase


class MyFileUtilsBase(FileUtilsBase):
    """A class to provide access to methods for testing"""

    def getDownloadContentTypes(self):
        """Returns list of content types know for downloads"""
        rset = set()
        for ky in self._rDList:
            ctList = self._rD[ky]
            rset.update(ctList)
        return list(rset)


class FileUtilTests(unittest.TestCase):
    def setUp(self):
        pass

    def testDownloadTypes(self):
        """Tests Download Types vs known in ConfigInfoData to prevent issues"""
        mfu = MyFileUtilsBase()
        cttypes = mfu.getDownloadContentTypes()

        cId = ConfigInfoData(verbose=False, useCache=False)
        configDict = cId.getConfigDictionary()
        knownContentTypes = configDict["CONTENT_TYPE_BASE_DICTIONARY"]

        for ct in cttypes:
            self.assertIn(ct, knownContentTypes, "%s not in known content types" % ct)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
