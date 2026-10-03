##
# File: UtilDataStoreTests.py
# Date:  03-Oct-2026
#
# Updates:
##
"""Test cases for UtilDataStore"""

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

from wwpdb.utils.session.UtilDataStore import UtilDataStore
from wwpdb.utils.session.WebRequest import InputRequest


class UtilDataStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpDir = tempfile.mkdtemp()
        self.reqObj = InputRequest({"TopSessionPath": [self.tmpDir]})
        self.sessionPath: str = self.reqObj.newSessionObj().getPath()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpDir, ignore_errors=True)

    def testFilePath(self) -> None:
        """Tests data store file location with default and explicit prefix"""
        uds = UtilDataStore(self.reqObj, verbose=True, log=StringIO())
        self.assertEqual(uds.getFilePath(), os.path.join(self.sessionPath, "general-util-session.pic"))
        uds = UtilDataStore(self.reqObj, prefix="mine")
        self.assertEqual(uds.getFilePath(), os.path.join(self.sessionPath, "mine-util-session.pic"))

    def testSetGet(self) -> None:
        """Tests set/get/append/extend/updateDict"""
        uds = UtilDataStore(self.reqObj)
        self.assertEqual(uds.get("missing"), "")
        self.assertTrue(uds.set("k1", 5))
        self.assertEqual(uds.get("k1"), 5)
        self.assertTrue(uds.append("l1", "a"))
        self.assertTrue(uds.append("l1", "b"))
        self.assertEqual(uds.get("l1"), ["a", "b"])
        self.assertTrue(uds.extend("l2", [1, 2]))
        self.assertTrue(uds.extend("l2", [3]))
        self.assertEqual(uds.get("l2"), [1, 2, 3])
        self.assertTrue(uds.updateDict("d1", "s1", 1))
        self.assertTrue(uds.updateDict("d1", "s2", 2))
        self.assertEqual(uds.get("d1"), {"s1": 1, "s2": 2})
        self.assertEqual(uds.getDictionary(), {"k1": 5, "l1": ["a", "b"], "l2": [1, 2, 3], "d1": {"s1": 1, "s2": 2}})

        uds.reset()
        self.assertEqual(uds.getDictionary(), {})

    def testTypeMismatch(self) -> None:
        """Tests failures when existing values have the wrong type"""
        uds = UtilDataStore(self.reqObj)
        uds.set("k1", 5)
        self.assertFalse(uds.append("k1", 1))
        self.assertFalse(uds.extend("k1", [1]))
        self.assertFalse(uds.updateDict("k1", "s", 1))
        self.assertFalse(uds.set(["unhashable"], 1))
        self.assertEqual(uds.get("k1"), 5)

    def testPersistence(self) -> None:
        """Tests serialize/deserialize round trip, isolated by prefix"""
        uds = UtilDataStore(self.reqObj, prefix="p1")
        self.assertFalse(uds.deserialize())
        uds.set("k1", "v1")
        uds.extend("l1", [1, 2])
        uds.serialize()
        self.assertTrue(os.path.exists(uds.getFilePath()))

        uds2 = UtilDataStore(self.reqObj, prefix="p1")
        self.assertEqual(uds2.get("k1"), "v1")
        self.assertEqual(uds2.get("l1"), [1, 2])

        uds3 = UtilDataStore(self.reqObj, prefix="p2")
        self.assertEqual(uds3.getDictionary(), {})

    def testNoSession(self) -> None:
        """Tests no session path available - store works in memory only"""
        reqObj = InputRequest({"TopSessionPath": [os.path.join(self.tmpDir, "missing")], "sessionid": ["abc"]})
        log = StringIO()
        uds = UtilDataStore(reqObj, log=log)
        self.assertIn("Failed to open data store", log.getvalue())
        self.assertIsNone(uds.getFilePath())
        self.assertTrue(uds.set("k1", 1))
        # Must not raise
        uds.serialize()
        self.assertFalse(uds.deserialize())
        self.assertEqual(uds.get("k1"), 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
