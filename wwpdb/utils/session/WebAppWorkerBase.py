##
# File:  WebAppWorkerBase.py
# Date:  28-Dec-2013
#
# Updates:
##
"""
Base class for supporting web application processing modules.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import ntpath
import os
import sys
import time
import traceback
import types
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, TextIO, cast

from wwpdb.utils.config.ConfigInfo import ConfigInfo

if TYPE_CHECKING:
    from wwpdb.utils.session.SessionManager import SessionManager
from wwpdb.utils.session.UtilDataStore import UtilDataStore
from wwpdb.utils.session.WebRequest import InputRequest, ResponseContent


class WebAppWorkerBase:
    def __init__(self, reqObj: Optional[InputRequest] = None, verbose: bool = False, log: TextIO = sys.stderr) -> None:
        """
        Base class supporting web application worker methods.

        Performs URL -> application mapping for this module.

        """

        self._verbose = verbose
        self.__debug = False
        self._lfh = log
        # cast() is for typing only - a None request object is not supported and fails below
        self._reqObj = cast("InputRequest", reqObj)
        self._sObj: Optional[SessionManager] = None
        self._sessionId: Optional[str] = None
        self._sessionPath: Optional[str] = None
        self._rltvSessionPath: Optional[str] = None
        self._siteId = self._reqObj.getValue("WWPDB_SITE_ID")
        self._cI = ConfigInfo(self._siteId)
        self._uds: Optional[UtilDataStore] = None
        # UtilDataStore prefix for general session data -- used by _getSession()
        self._udsPrefix: Optional[str] = None
        self.__appPathD: Dict[str, str] = {}

    def addService(self, url: str, opName: str) -> None:
        self.__appPathD[url] = opName

    def addServices(self, serviceDict: Dict[str, str]) -> None:
        for k, v in serviceDict.items():
            self.__appPathD[k] = v

    def doOp(self) -> ResponseContent:
        """Map operation to path and invoke operation.  Exceptions are caught within this method.

        :returns:

        Operation output is packaged in a ResponseContent() object.

        """
        try:
            inpReqPath = self._reqObj.getRequestPath()
            # first pull off the REST style URLS --
            #
            #  /service/review/report/D_XXXXXX
            #
            if inpReqPath.startswith("/service/review/report/d_"):
                rFields = inpReqPath.split("/")
                self._reqObj.setValue("idcode", rFields[4].upper())
                reqPath = "/service/review/report"
            else:
                reqPath = inpReqPath
            if reqPath not in self.__appPathD:
                # bail out if operation is unknown -
                rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                rC.setError(errMsg="Unknown operation")
            else:
                # An unknown method name raises AttributeError, which is caught below
                mth = getattr(self, self.__appPathD[reqPath])
                rC = mth()
            return rC
        except:  # noqa: E722 pylint: disable=bare-except
            if self._verbose:
                traceback.print_exc(file=self._lfh)
            rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            rC.setError(errMsg="Operation failure")
            return rC

    def _saveSessionParameter(
        self,
        param: Optional[str] = None,
        value: Any = None,
        pvD: Optional[Dict[str, Any]] = None,
        prefix: Optional[str] = None,
    ) -> bool:
        """Store the input (param,value) pair and/or the contents of parameter value
        dictionary (pvD) in the session parameter store.
        """
        try:
            # if self._uds is None:
            self._uds = UtilDataStore(reqObj=self._reqObj, prefix=prefix, verbose=self._verbose, log=self._lfh)
            if param is not None:
                self._uds.set(param, value)
                self._uds.serialize()
            if pvD is not None and len(pvD) > 0:
                for k, v in pvD.items():
                    self._uds.set(k, v)
                self._uds.serialize()
            return True
        except Exception as e:  # noqa: BLE001
            if self._verbose:
                self._lfh.write(
                    "+WebAppWorkerBase._saveSessionParameter() failed in session %s - %r\n" % (self._sessionId, str(e))
                )
        return False

    def _getSessionParameter(self, param: Optional[str] = None, prefix: Optional[str] = None) -> Any:
        """Recover session data for the input parameter or return an empty string."""
        try:
            self._uds = UtilDataStore(reqObj=self._reqObj, prefix=prefix, verbose=self._verbose, log=self._lfh)
            # cast() is for typing only - a None param is a missing key, for which get() returns an empty string
            return self._uds.get(cast("str", param))
        except Exception as e:  # noqa: BLE001
            if self._verbose:
                self._lfh.write(
                    "+WebAppWorkerBase._getSessionParameter() failed in session %s - %r\n" % (self._sessionId, str(e))
                )
        return ""

    def _getFileText(self, filePath: str) -> ResponseContent:
        self._reqObj.setReturnFormat(return_format="text")
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setTextFile(filePath)
        return rC

    def _newSessionOp(self) -> ResponseContent:
        if self.__debug:
            self._lfh.write("+WebAppWorkerBase.newSessionOp() starting\n")

        self._getSession(forceNew=True)
        self._reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        sId = self._reqObj.getSessionId()
        if len(sId):
            rC.setHtmlText("Session id %s created." % sId)
        else:
            rC.setError(errMsg="No session created")

        return rC

    def _verifySessionContext(self, apikyfn: Callable[[str], bool], overWrite: bool = True) -> bool:
        try:
            self._sObj = self._reqObj.getSessionObj()
            pth = self._sObj.getPath()
            if pth is None:
                return False
            self._sessionId = self._sObj.getId()
            self._sessionPath = self._sObj.getPath()
            self._rltvSessionPath = self._sObj.getRelativePath()
            uds = UtilDataStore(reqObj=self._reqObj, prefix=self._udsPrefix, verbose=self._verbose, log=self._lfh)
            dd = uds.getDictionary()
            if self.__debug:
                self._lfh.write(
                    "+WebAppWorkerBase._verifySessionContext() -  importing persisted general session parameters:\n"
                )
                for k, v in dd.items():
                    if isinstance(v, (dict, list)):
                        self._lfh.write(" %30s length=%d\n" % (k, len(v)))
                    else:
                        self._lfh.write(" %30s= %r\n" % (k, v))
            self._reqObj.setDictionary(dd, overWrite=overWrite)
            #
            # Now check for a valid key --
            #
            reqApiKey = self._reqObj.getValue("apikey")
            ok = apikyfn(reqApiKey)
            return ok
        except Exception as e:  # noqa: BLE001
            if self._verbose:
                self._lfh.write("+WebAppWorkerBase._verifySessionContext() - failed - %r\n" % str(e))
            if self._verbose:
                traceback.print_exc(file=self._lfh)
        return False

    def _getSession(self, forceNew: bool = False, useContext: bool = False, overWrite: bool = True) -> None:
        """Join existing session or create new session as required."""
        self._sObj = self._reqObj.newSessionObj(forceNew=forceNew)

        self._sessionId = self._sObj.getId()
        self._sessionPath = self._sObj.getPath()
        self._rltvSessionPath = self._sObj.getRelativePath()

        if self._verbose:
            self._lfh.write("+WebAppWorkerBase._getSession() - session   id  %s\n" % self._sessionId)
            self._lfh.write("+WebAppWorkerBase._getSession() - session path  %s\n" % self._sessionPath)

        if useContext:
            uds = UtilDataStore(reqObj=self._reqObj, prefix=self._udsPrefix, verbose=self._verbose, log=self._lfh)
            dd = uds.getDictionary()
            if self.__debug:
                self._lfh.write("+WebAppWorkerBase._getSession() -  importing persisted general session parameters:\n")
                for k, v in dd.items():
                    if isinstance(v, (dict, list)):
                        self._lfh.write(" %30s length=%d\n" % (k, len(v)))
                    else:
                        self._lfh.write(" %30s= %r\n" % (k, v))
            self._reqObj.setDictionary(dd, overWrite=overWrite)

    def _isFileUpload(self, fileTag: str = "file") -> bool:
        """Generic check for the existence of request paramenter of type "file"."""
        fs = self._reqObj.getRawValue(fileTag)
        if sys.version_info[0] < 3:  # noqa: UP036
            if (fs is None) or (isinstance(fs, types.StringType)):  # pylint: disable=no-member
                return False
        elif isinstance(fs, (bytes, str)):
            return False

        return True

    def _uploadFile(self, fileTag: str = "file") -> Optional[str]:
        """Copying uploaded file to the session directory.  Return file name or None."""
        try:
            fs = self._reqObj.getRawValue(fileTag)
            fNameInput = str(fs.filename)

            #
            # Need to deal with some platform issues -
            #
            if fNameInput.find("\\") != -1:
                # likely windows path -
                fName = ntpath.basename(fNameInput)
            else:
                fName = os.path.basename(fNameInput)

            #
            # Store upload file in session directory -
            #
            # cast() is for typing only - a None session path raises TypeError, which is caught below
            fPathAbs = os.path.join(cast("str", self._sessionPath), fName)
            if self._verbose:
                self._lfh.write(
                    "+WebAppWorkerBase._uploadFile() - starting upload of %r to path %r\n" % (fNameInput, fPathAbs)
                )

            ofh = open(fPathAbs, "wb")
            ofh.write(fs.file.read())
            ofh.close()

            if self._verbose:
                self._lfh.write(
                    "+WebAppWorkerBase._uploadFile() - uploaded completed for file tag %s file name %s\n"
                    % (fileTag, fName)
                )
            #
            #  Store the file path and name in request object -
            #
            self._reqObj.setValue("filePath", fPathAbs)
            self._reqObj.setValue("fileName", fName)
            return fName
        except Exception as e:  # noqa: BLE001
            if self._verbose:
                self._lfh.write(
                    "+WebAppWorkerBase._uploadFile() - Upload failed for file tag %s file name %s - %r\n"
                    % (fileTag, fs.filename, str(e))
                )
            if self.__debug:
                traceback.print_exc(file=self._lfh)
        return None

    def _setSemaphore(self) -> str:
        sVal = str(time.strftime("TMP_%Y%m%d%H%M%S", time.localtime()))
        self._reqObj.setValue("semaphore", sVal)
        return sVal

    def _openSemaphoreLog(self, semaphore: str = "TMP_") -> None:
        sessionId = self._reqObj.getSessionId()
        sessionPath = self._reqObj.getSessionPath()
        fPathAbs = os.path.join(sessionPath, sessionId, semaphore + ".log")
        self._lfh = open(fPathAbs, "w")

    def _closeSemaphoreLog(self, semaphore: str = "TMP_") -> None:  # noqa: ARG002 pylint: disable=unused-argument
        self._lfh.flush()
        self._lfh.close()

    def _postSemaphore(self, semaphore: str = "TMP_", value: str = "OK") -> str:
        sessionId = self._reqObj.getSessionId()
        sessionPath = self._reqObj.getSessionPath()
        fPathAbs = os.path.join(sessionPath, sessionId, semaphore)
        fp = open(fPathAbs, "w")
        fp.write("%s\n" % value)
        fp.close()
        return semaphore

    def _semaphoreExists(self, semaphore: str = "TMP_") -> bool:
        sessionId = self._reqObj.getSessionId()
        sessionPath = self._reqObj.getSessionPath()
        fPathAbs = os.path.join(sessionPath, sessionId, semaphore)
        if os.access(fPathAbs, os.F_OK):
            return True
        return False

    def _getSemaphore(self, semaphore: str = "TMP_") -> str:
        sessionId = self._reqObj.getSessionId()
        sessionPath = self._reqObj.getSessionPath()
        fPathAbs = os.path.join(sessionPath, sessionId, semaphore)
        if self._verbose:
            self._lfh.write("+ReviewDataWebApp.__getSemaphore() - checking %s in path %s\n" % (semaphore, fPathAbs))
        try:
            fp = open(fPathAbs)
            lines = fp.readlines()
            fp.close()
            sval = lines[0][:-1]
        except:  # noqa: E722 pylint: disable=bare-except
            sval = "FAIL"
        return sval
