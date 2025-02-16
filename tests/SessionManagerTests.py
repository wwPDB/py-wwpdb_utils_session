##
# File: SessionManagerTests.py
# Date:  23-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for SessionManager"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import platform
import shutil
import unittest

from wwpdb.utils.session.SessionManager import SessionManager


class SessionTests(unittest.TestCase):
    def setUp(self):
        HERE = os.path.abspath(os.path.dirname(__file__))
        TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
        if not os.path.exists(TESTOUTPUT):  # pragma: no cover
            os.makedirs(TESTOUTPUT)
        self.__sessiontop = TESTOUTPUT

    def testId(self):
        """Tests generation of session id for python"""
        sm = SessionManager()
        # Not set
        self.assertEqual(sm.getId(), None)

        sm.setId("12345")
        self.assertEqual(sm.getId(), "12345")

        self.assertNotEqual(sm.assignId(), None, "Failed to return id")
        self.assertNotEqual(sm.getId(), "12345", "Failed to generate new id")
        self.assertIn("SessionManager()", str(sm), "Failed to get string representation")
        self.assertIn("SessionManager()", repr(sm), "Failed to get repr representation")
        self.assertIsNotNone(sm.getTopPath(), "Top path should not be none")
        self.assertIsNotNone(sm.getRelativePath(), "Relative path should not be none")

    def testBadPath(self):
        """Tests bad path access"""
        here = os.path.abspath(os.path.dirname(__file__))
        badpath = os.path.join(here, "bad_dir_for_sessions")
        sm = SessionManager(badpath)
        self.assertIsNone(sm.getPath(), "Expected path should be None")

        # Test with path of None - should error out
        sm = SessionManager(None)
        self.assertIsNone(sm.getPath(), "Expected path should be None")
        self.assertIsNone(sm.getTopPath(), "Top path expected to be none")

    def testSessionPathCreation(self):
        """Tests creation of session dir"""
        sessdir = os.path.join(self.__sessiontop, "sesscreate")
        if os.path.exists(sessdir):  # pragma: no cover
            shutil.rmtree(sessdir)
        sm = SessionManager(sessdir, verbose=True)
        # Fail without uid set
        self.assertIsNone(sm.makeSessionPath(), "Creating session path uid not set")
        self.assertIsNone(sm.remakeSessionPath(), "Creating session path uid not set")
        self.assertIsNone(sm.getRelativePath(), "Relative path should be none with uid not set")

        self.assertIsNotNone(sm.assignId())
        self.assertIsNotNone(sm.makeSessionPath(), "Creating session path uid set")
        self.assertIsNotNone(sm.remakeSessionPath(), "Creating session path uid set")
        self.assertIsNotNone(sm.getPath(), "Expected path should not be None")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
