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
import sys
import hashlib
import time
import os.path
import shutil

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


class SessionManager(object):
    """
        Utilities for session directory maintenance.

    """

    def __init__(self, topPath=".", verbose=False):
        """
             Organization of session directory is --
             <topPath>/<sha-hash>/<session_files>

             Parameters:
             :topPath: is the path to the directory containing the hash-id sub-directory.


        """
        self.__verbose = verbose
        self.__topSessionPath = topPath
        self.__uid = None

    def __str__(self):
        return "\n+SessionManager() Session top path: %s\nUnique identifier: %s\nSession path: %s\n" % (self.__topSessionPath, self.__uid, self.getPath())

    def __repr__(self):
        return self.__str__()

    def setId(self, uid):
        self.__uid = uid

    def getId(self):
        return self.__uid

    def assignId(self):
        # Need to convert to str (python2)/bytes (python3)
        tmp = repr(time.time()).encode("utf-8")
        self.__uid = hashlib.sha1(tmp).hexdigest()
        return self.__uid

    def getPath(self):
        try:
            pth = os.path.join(self.__topSessionPath, "sessions", self.__uid)
            if self.__verbose:
                sys.stderr.write("+SessionManager.getPath() path %s\n" % pth)
            if os.access(pth, os.F_OK):
                return pth
            else:
                return None
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def getTopPath(self):
        return self.__topSessionPath

    def getRelativePath(self):
        pth = None
        try:
            pth = os.path.join("/sessions", self.__uid)

        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return pth

    def makeSessionPath(self):
        """ If the path to the current session directory does not exist
            create it and return the session path.
        """
        try:
            pth = os.path.join(self.__topSessionPath, "sessions", self.__uid)
            if not os.access(pth, os.F_OK):
                os.makedirs(pth)
            return pth
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def remakeSessionPath(self):
        try:
            pth = os.path.join(self.__topSessionPath, "sessions", self.__uid)
            if os.access(pth, os.F_OK):
                shutil.rmtree(pth, True)
            os.makedirs(pth)
            return pth
        except:  # noqa: E722 pylint: disable=bare-except
            return None
