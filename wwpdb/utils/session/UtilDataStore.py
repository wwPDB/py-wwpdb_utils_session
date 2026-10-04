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

import os.path
import sys
from typing import Any, Dict, List, Optional, TextIO

try:
    import cPickle as pickle  # type: ignore[import-not-found] # noqa: N813,S403
except ImportError:
    import pickle  # noqa: S403

from wwpdb.utils.session.WebRequest import InputRequest

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


class UtilDataStore:
    """Provide a storage interface for miscellaneous key,value data."""

    def __init__(
        self, reqObj: InputRequest, prefix: Optional[str] = None, verbose: bool = False, log: TextIO = sys.stderr
    ) -> None:
        self.__verbose = verbose
        self.__debug = True
        self.__lfh = log
        self.__reqObj = reqObj
        if prefix is not None:
            self.__filePrefix = prefix
        else:
            self.__filePrefix = "general"
        self.__filePath: Optional[str] = None
        self.__D: Dict[str, Any] = {}
        self.__setup()

    def __setup(self) -> None:
        #  self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        #
        # self.__pickleProtocol = pickle.HIGHEST_PROTOCOL
        self.__pickleProtocol = 0
        try:
            # A None session path raises TypeError here, which is caught and reported below
            self.__filePath = os.path.join(self.__sessionPath, self.__filePrefix + "-util-session.pic")  # type: ignore[arg-type]
            if self.__verbose:
                self.__lfh.write("\n+UtilDataStore.__setup() - data store path %s\n" % self.__filePath)
            self.deserialize()
        except Exception as e:  # noqa: BLE001
            if self.__debug:
                self.__lfh.write(
                    "\n+UtilDataStore.__setup() - Failed to open data store for session id %s data store prefix %s path %s err %s\n"
                    % (self.__sessionId, self.__filePrefix, self.__filePath, str(e))
                )

    def reset(self) -> None:
        self.__D = {}

    def getFilePath(self) -> Optional[str]:
        return self.__filePath

    def serialize(self) -> None:
        try:
            fb = open(self.__filePath, "wb")  # type: ignore[arg-type]
            pickle.dump(self.__D, fb, self.__pickleProtocol)
            fb.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

    def deserialize(self) -> bool:
        try:
            fb = open(self.__filePath, "rb")  # type: ignore[arg-type]
            self.__D = pickle.load(fb)  # noqa: S301
            fb.close()
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def get(self, key: str) -> Any:
        try:
            return self.__D[key]
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def set(self, key: str, value: Any) -> bool:
        try:
            self.__D[key] = value
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def append(self, key: str, value: Any) -> bool:
        try:
            if key not in self.__D:
                self.__D[key] = []
            self.__D[key].append(value)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def extend(self, key: str, valueList: List[Any]) -> bool:
        try:
            if key not in self.__D:
                self.__D[key] = []
            self.__D[key].extend(valueList)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def updateDict(self, key: str, subKey: str, value: Any) -> bool:
        try:
            if key not in self.__D:
                self.__D[key] = {}
            self.__D[key][subKey] = value
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getDictionary(self) -> Dict[str, Any]:
        return self.__D
