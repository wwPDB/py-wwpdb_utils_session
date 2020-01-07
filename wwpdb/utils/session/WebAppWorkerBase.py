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

import os
import sys
import time
import types
import traceback
import ntpath

#
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.session.UtilDataStore import UtilDataStore
from wwpdb.utils.session.WebRequest import ResponseContent

#


class WebAppWorkerBase(object):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
         Base class supporting web application worker methods.

         Performs URL -> application mapping for this module.

        """

        self._verbose = verbose
        self.__debug = False
        self._lfh = log
        self._reqObj = reqObj
        self._sObj = None
        self._sessionId = None
        self._sessionPath = None
        self._rltvSessionPath = None
        #
        self._siteId = self._reqObj.getValue("WWPDB_SITE_ID")
        self._cI = ConfigInfo(self._siteId)
        #
        self._uds = None
        # UtilDataStore prefix for general session data -- used by _getSession()
        self._udsPrefix = None
        #
        self.__appPathD = {}

    def addService(self, url, opName):
        self.__appPathD[url] = opName

    def addServices(self, serviceDict):
        for k, v in serviceDict.items():
            self.__appPathD[k] = v

    def doOp(self):
        """Map operation to path and invoke operation.  Exceptions are caught within this method.

            :returns:

            Operation output is packaged in a ResponseContent() object.

        """
        #
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
            #
            if reqPath not in self.__appPathD:
                # bail out if operation is unknown -
                rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
                rC.setError(errMsg="Unknown operation")
            else:
                mth = getattr(self, self.__appPathD[reqPath], None)
                rC = mth()
            return rC
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__debug:
                traceback.print_exc(file=self._lfh)
            rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
            rC.setError(errMsg="Operation failure")
            return rC

    #
    def _saveSessionParameter(self, param=None, value=None, pvD=None, prefix=None):
        """ Store the input (param,value) pair and/or the contents of parameter value
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
        except Exception as e:
            if self._verbose:
                self._lfh.write("+WebAppWorkerBase._saveSessionParameter() failed in session %s - %r\n" % (self._sessionId, str(e)))
        return False

    def _getSessionParameter(self, param=None, prefix=None):
        """ Recover session data for the input parameter or return an empty string.
        """
        try:
            self._uds = UtilDataStore(reqObj=self._reqObj, prefix=prefix, verbose=self._verbose, log=self._lfh)
            return self._uds.get(param)
        except Exception as e:
            if self._verbose:
                self._lfh.write("+WebAppWorkerBase._getSessionParameter() failed in session %s - %r\n" % (self._sessionId, str(e)))
        return ""

    def _getFileText(self, filePath):
        self._reqObj.setReturnFormat(return_format="text")
        rC = ResponseContent(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        rC.setTextFile(filePath)
        return rC

    def _newSessionOp(self):
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

    def _verifySessionContext(self, apikyfn, overWrite=True):
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
                self._lfh.write("+WebAppWorkerBase._verifySessionContext() -  importing persisted general session parameters:\n")
                for k, v in dd.items():
                    if isinstance(v, list) or isinstance(v, dict):
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
        except Exception as e:
            if self._verbose:
                self._lfh.write("+WebAppWorkerBase._verifySessionContext() - failed - %r\n" % str(e))
            if self._verbose:
                traceback.print_exc(file=self._lfh)
        return False

    def _getSession(self, forceNew=False, useContext=False, overWrite=True):
        """ Join existing session or create new session as required.
        """
        #
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
                    if isinstance(v, list) or isinstance(v, dict):
                        self._lfh.write(" %30s length=%d\n" % (k, len(v)))
                    else:
                        self._lfh.write(" %30s= %r\n" % (k, v))
            self._reqObj.setDictionary(dd, overWrite=overWrite)

    def _isFileUpload(self, fileTag="file"):
        """ Generic check for the existence of request paramenter of type "file".
        """
        fs = self._reqObj.getRawValue(fileTag)
        if sys.version_info[0] < 3:
            if (fs is None) or (isinstance(fs, types.StringType)):  # pylint: disable=no-member
                return False
        else:
            if (fs is None) or (isinstance(fs, str)) or (isinstance(fs, bytes)):
                return False

        return True

    def _uploadFile(self, fileTag="file"):
        """  Copying uploaded file to the session directory.  Return file name or None.
        """
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
            fPathAbs = os.path.join(self._sessionPath, fName)
            if self._verbose:
                self._lfh.write("+WebAppWorkerBase._uploadFile() - starting upload of %r to path %r\n" % (fNameInput, fPathAbs))

            ofh = open(fPathAbs, "wb")
            ofh.write(fs.file.read())
            ofh.close()

            #
            if self._verbose:
                self._lfh.write("+WebAppWorkerBase._uploadFile() - uploaded completed for file tag %s file name %s\n" % (fileTag, fName))
            #
            #  Store the file path and name in request object -
            #
            self._reqObj.setValue("filePath", fPathAbs)
            self._reqObj.setValue("fileName", fName)
            return fName
        except Exception as e:
            if self._verbose:
                self._lfh.write("+WebAppWorkerBase._uploadFile() - Upload failed for file tag %s file name %s - %r\n" % (fileTag, fs.filename, str(e)))
            if self.__debug:
                traceback.print_exc(file=self._lfh)
        return None

    def _setSemaphore(self):
        sVal = str(time.strftime("TMP_%Y%m%d%H%M%S", time.localtime()))
        self._reqObj.setValue("semaphore", sVal)
        return sVal

    def _openSemaphoreLog(self, semaphore="TMP_"):
        sessionId = self._reqObj.getSessionId()
        sessionPath = self._reqObj.getSessionPath()
        fPathAbs = os.path.join(sessionPath, sessionId, semaphore + ".log")
        self._lfh = open(fPathAbs, "w")

    def _closeSemaphoreLog(self, semaphore="TMP_"):  # pylint: disable=unused-argument
        self._lfh.flush()
        self._lfh.close()

    def _postSemaphore(self, semaphore="TMP_", value="OK"):
        sessionId = self._reqObj.getSessionId()
        sessionPath = self._reqObj.getSessionPath()
        fPathAbs = os.path.join(sessionPath, sessionId, semaphore)
        fp = open(fPathAbs, "w")
        fp.write("%s\n" % value)
        fp.close()
        return semaphore

    def _semaphoreExists(self, semaphore="TMP_"):
        sessionId = self._reqObj.getSessionId()
        sessionPath = self._reqObj.getSessionPath()
        fPathAbs = os.path.join(sessionPath, sessionId, semaphore)
        if os.access(fPathAbs, os.F_OK):
            return True
        else:
            return False

    def _getSemaphore(self, semaphore="TMP_"):
        sessionId = self._reqObj.getSessionId()
        sessionPath = self._reqObj.getSessionPath()
        fPathAbs = os.path.join(sessionPath, sessionId, semaphore)
        if self._verbose:
            self._lfh.write("+ReviewDataWebApp.__getSemaphore() - checking %s in path %s\n" % (semaphore, fPathAbs))
        try:
            fp = open(fPathAbs, "r")
            lines = fp.readlines()
            fp.close()
            sval = lines[0][:-1]
        except:  # noqa: E722 pylint: disable=bare-except
            sval = "FAIL"
        return sval
