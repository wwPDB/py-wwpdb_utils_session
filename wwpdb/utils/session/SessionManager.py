##
# File:    SessionManager.py
# Date:    14-Dec-2009
#
# Updates:
# 20-Apr-2010 jdw Ported to module seqmodule.
# 05-Aug-2010 jdw Ported to module ccmodule
#                 Replace deprecated sha module with hashlib
# 21-Sep-2010 jdw Remove 'sessions' from internal path used by this module.
#                 topPath now points to the directory containing the hash directory.
# 20-Feb-2013 jdw Application neutral version moved to utils/rcsb
##
"""
Provides containment and access for session information.  Methods
are provided to create temporary directories to preserve session files.

"""

import contextlib
import hashlib
import os.path
import shutil
import sys
import time
from typing import Optional

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


class SessionManager:
    """
    Utilities for session directory maintenance.

    """

    def __init__(self, topPath: str = ".", verbose: bool = False) -> None:
        """
        Organization of session directory is --
        <topPath>/<sha-hash>/<session_files>

        Parameters:
        :topPath: is the path to the directory containing the hash-id sub-directory.


        """
        self.__verbose = verbose
        self.__topSessionPath = topPath
        self.__uid: Optional[str] = None

    def __str__(self) -> str:
        return "\n+SessionManager() Session top path: %s\nUnique identifier: %s\nSession path: %s\n" % (
            self.__topSessionPath,
            self.__uid,
            self.getPath(),
        )

    def __repr__(self) -> str:
        return self.__str__()

    def setId(self, uid: Optional[str]) -> None:
        self.__uid = uid

    def getId(self) -> Optional[str]:
        return self.__uid

    def assignId(self) -> str:
        # Need to convert to str (python2)/bytes (python3)
        tmp = repr(time.time()).encode("utf-8")
        uid = hashlib.sha1(tmp).hexdigest()  # noqa: S324
        self.__uid = uid
        return uid

    def getSessionsPath(self) -> str:
        return os.path.join(self.getTopPath(), "sessions")

    def getPath(self) -> Optional[str]:
        if self.__uid is None:
            return None
        try:
            pth = os.path.join(self.getSessionsPath(), self.__uid)
            if self.__verbose:
                sys.stderr.write("+SessionManager.getPath() path %s\n" % pth)
            if os.access(pth, os.F_OK):
                return pth
            return None
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def getTopPath(self) -> str:
        return self.__topSessionPath

    def getRelativePath(self) -> Optional[str]:
        if self.__uid is None:
            return None
        pth: Optional[str] = None
        with contextlib.suppress(Exception):
            pth = os.path.join("/sessions", self.__uid)
        return pth

    def makeSessionPath(self) -> Optional[str]:
        """If the path to the current session directory does not exist
        create it and return the session path.
        """
        if self.__uid is None:
            return None
        try:
            pth = os.path.join(self.getSessionsPath(), self.__uid)
            if not os.access(pth, os.F_OK):
                os.makedirs(pth)
            return pth
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def remakeSessionPath(self) -> Optional[str]:
        if self.__uid is None:
            return None
        try:
            pth = os.path.join(self.getSessionsPath(), self.__uid)
            if os.access(pth, os.F_OK):
                shutil.rmtree(pth, True)
            os.makedirs(pth)
            return pth
        except:  # noqa: E722 pylint: disable=bare-except
            return None
