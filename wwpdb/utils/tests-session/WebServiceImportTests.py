##
# File: WebServiceImportTests.py
# Date:  06-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for webservice - simply import everything to ensure imports work"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest
import os
import platform

from wwpdb.utils.session.SessionManager import SessionManager
from wwpdb.utils.session.UtilDataStore import UtilDataStore
from wwpdb.utils.session.WebAppWorkerBase import WebAppWorkerBase
from wwpdb.utils.session.WebDownloadUtils import WebDownloadUtils
from wwpdb.utils.session.WebRequest import WebRequest, InputRequest
from wwpdb.utils.session.WebUploadUtils import WebUploadUtils
from wwpdb.utils.session.FileUtils import FileUtils


class ImportTests(unittest.TestCase):
    def setUp(self):
        HERE = os.path.abspath(os.path.dirname(__file__))
        TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
        if not os.path.exists(TESTOUTPUT):  # pragma: no cover
            os.makedirs(TESTOUTPUT)
        self.__sessiontop = TESTOUTPUT
        sdir = os.path.join(self.__sessiontop, "sessions")
        if not os.path.exists(sdir):
            os.makedirs(sdir)

    def testInstantiate(self):
        _vc = WebRequest()  # noqa: F841
        params = {"TopSessionPath": [self.__sessiontop]}
        reqobj = InputRequest(params)

        # Needs a valid reqobj
        _vc = UtilDataStore(reqobj)  # noqa: F841
        _vc = WebAppWorkerBase(reqobj)  # noqa: F841
        _vc = WebDownloadUtils(reqobj)  # noqa: F841
        _vc = WebUploadUtils(reqobj)  # noqa: F841
        _vc = SessionManager()  # noqa: F841
        _vc = FileUtils("xxxx", reqobj)  # noqa: F841


if __name__ == "__main__":
    unittest.main()
