##
# File: WebRequestsTests.py
# Date:  07-Jan-2020  E. Peisach
#
# Updates:
##
"""Test cases for WebRequests
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import unittest
import platform

# from datetime import datetime

from wwpdb.utils.session.WebRequest import WebRequest


class MyWebRequest(WebRequest):
    """A class to provide access to methods for testing"""

    def __init__(self, paramDict=None, verbose=False):
        super(MyWebRequest, self).__init__(paramDict, verbose)
        self.__verbose = verbose

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

    def testWebRequest(self):
        """Tests WebRequest access"""

        # No parameters
        wr = WebRequest()
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


# ResponseContent
#        d = datetime.now()
#        wr.set("date", d, asJson=True)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
