##
# File:    UtilDataStore.py
# Date:    6-July-2012
#
# Updates:
#            7-July-2012 jdw make store path depend on entryId
#           07-Mar-2013  jdw make generic and move main project utils/rcsb
#           12-Jul-2013  jdw add append/extend methods for assigning list values
#            2-Mar-2014  jdw add  updateDict(self,key,subKey,value)
##
"""
Provide a storage interface for miscellaneous key,value data.

"""
import sys
import os.path

try:
    import cPickle as pickle
except ImportError:
    import pickle

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


class UtilDataStore(object):
    """  Provide a storage interface for miscellaneous key,value data.
    """

    def __init__(self, reqObj, prefix=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = True
        self.__lfh = log
        self.__reqObj = reqObj
        if prefix is not None:
            self.__filePrefix = prefix
        else:
            self.__filePrefix = "general"
        self.__filePath = None
        self.__D = {}
        self.__setup()

    def __setup(self):
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        #
        # self.__pickleProtocol = pickle.HIGHEST_PROTOCOL
        self.__pickleProtocol = 0
        try:
            self.__filePath = os.path.join(self.__sessionPath, self.__filePrefix + "-util-session.pic")
            if self.__verbose:
                self.__lfh.write("\n+UtilDataStore.__setup() - data store path %s\n" % self.__filePath)
            self.deserialize()
        except Exception as e:
            if self.__debug:
                self.__lfh.write(
                    "\n+UtilDataStore.__setup() - Failed to open data store for session id %s data store prefix %s path %s err %s\n"
                    % (self.__sessionId, self.__filePrefix, self.__filePath, str(e))
                )

    def reset(self):
        self.__D = {}

    def getFilePath(self):
        return self.__filePath

    def serialize(self):
        try:
            fb = open(self.__filePath, "wb")
            pickle.dump(self.__D, fb, self.__pickleProtocol)
            fb.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

    def deserialize(self):
        try:
            fb = open(self.__filePath, "rb")
            self.__D = pickle.load(fb)
            fb.close()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def get(self, key):
        try:
            return self.__D[key]
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def set(self, key, value):
        try:
            self.__D[key] = value
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def append(self, key, value):
        try:
            if key not in self.__D:
                self.__D[key] = []
            self.__D[key].append(value)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def extend(self, key, valueList):
        try:
            if key not in self.__D:
                self.__D[key] = []
            self.__D[key].extend(valueList)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def updateDict(self, key, subKey, value):
        try:
            if key not in self.__D:
                self.__D[key] = {}
            self.__D[key][subKey] = value
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getDictionary(self):
        return self.__D
