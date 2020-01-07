##
# File: SessionManagerTests.py
# Date:  23-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for SessionManager
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"
import unittest

from wwpdb.utils.session.SessionManager import SessionManager


class SessionTests(unittest.TestCase):
    def setUp(self):
        pass

    def testId(self):
        """Tests generation of session id for python"""
        sm = SessionManager()
        # Not set
        self.assertEqual(sm.getId(), None)

        sm.setId("12345")
        self.assertEqual(sm.getId(), "12345")

        self.assertNotEqual(sm.assignId(), None, "Failed to return id")
        self.assertNotEqual(sm.getId(), "12345", "Failed to generate new id")


if __name__ == "__main__":
    unittest.main()
