##
# File:  WebDownloadUtils.py
# Date:  22-Mar-2013   J. Westbrook
#
# Updates:
#   06-Mar-2014 jdw -- explicitly set return format in the response object.
#
#
##
"""
Utilities to manage  web application download requests for archive and workflow data files -.

   URL parameters or keys in the request object.

        'data_set_id'
        'file_source'
        'content_type'
        'format'

   optional
          'wf_instance'
          'version'
          'part'
          'compress'

    response corresponds to  -

      for success -
        self.__reqObj.setReturnFormat(return_format="binary")

      and for failure  -

        self.__reqObj.setReturnFormat(return_format="text|html|json")

"""

import sys
import os
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.session.WebRequest import ResponseContent

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.09"


class WebDownloadUtils(object):
    """
     This class encapsulates handling download requests for workflow data files -

    """

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):

        self.__reqObj = reqObj
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__debug = False
        #
        self.__sessionObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sessionObj.getPath()
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")

        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        #
        if self.__verbose:
            self.__lfh.write("+WebDownloadUtils.__setup() - session id   %s\n" % (self.__sessionObj.getId()))
            self.__lfh.write("+WebDownloadUtils.__setup() - session path %s\n" % (self.__sessionPath))

    def makeDownloadResponse(self):
        """  Return a response object correponding to a download action for data file described by the
             parameter content in the request object.
        """
        if self.__verbose:
            self.__lfh.write("+WebDownloadUtils.makeResponse() starting with session path %s\n" % self.__sessionPath)
        filePath = self.__getDownloadFileInfo()

        if self.__verbose:
            self.__lfh.write("+WebDownloadUtils.makeResponse() target file path is %s\n" % filePath)
        return self.__makeResponseContentObject(filePath=filePath)

    def __getDownloadFileInfo(self):
        """ Extract target file details and return file path or None.

        """
        retPath = None
        #
        dataSetId = self.__reqObj.getValue("data_set_id")
        if len(dataSetId) < 1:
            return retPath

        fileSource = self.__reqObj.getValueOrDefault("file_source", default="archive")
        if fileSource not in ["archive", "wf-archive", "wf-instance", "session", "wf-session"]:
            return retPath

        wfInstanceId = self.__reqObj.getValueOrDefault("wf_instance", default=None)

        contentType = self.__reqObj.getValue("content_type")
        if len(contentType) < 1:
            return retPath

        formatType = self.__reqObj.getValueOrDefault("format", default="pdbx")
        versionId = self.__reqObj.getValueOrDefault("version", default="latest")
        partNumber = self.__reqObj.getValueOrDefault("part", "1")
        #

        retPath = self.__pI.getFilePath(
            dataSetId, wfInstanceId=wfInstanceId, contentType=contentType, formatType=formatType, fileSource=fileSource, versionId=versionId, partNumber=partNumber
        )
        return retPath

    def __makeResponseContentObject(self, filePath, attachmentFlag=True, compressFlag=False):
        """  Create a response content object for the input file

        """
        if self.__verbose:
            self.__lfh.write("+WebDownloadUtils.__makeResponseContentObject() starting with file path %s\n" % filePath)
        #
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        if filePath is not None and os.access(filePath, os.F_OK):
            rC.setReturnFormat("binary")
            rC.setBinaryFile(filePath, attachmentFlag=attachmentFlag, serveCompressed=compressFlag)
        else:
            rC.setReturnFormat("json")
            rC.setError(errMsg="Download failure for %s" % filePath)

        return rC
