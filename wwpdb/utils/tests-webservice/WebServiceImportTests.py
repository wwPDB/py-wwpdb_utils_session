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

from wwpdb.utils.webservice.SessionManager    import SessionManager
from wwpdb.utils.webservice.UtilDataStore     import UtilDataStore
from wwpdb.utils.webservice.WebAppWorkerBase  import WebAppWorkerBase 
from wwpdb.utils.webservice.WebDownloadUtils  import WebDownloadUtils
from wwpdb.utils.webservice.WebRequest        import WebRequest
from wwpdb.utils.webservice.WebUploadUtils    import WebUploadUtils


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        vc = WebRequest()
        # Needs a valid reqobj
        #vc = UtilDataStore()
        #vc = WebAppWorkerBase()
        #vc = WebDownloadUtils()
        #vc = WebUploadUtils()

if __name__ == '__main__':
    unittest.main()


    
