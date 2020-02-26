##
# File:  FileUtils.py
# Date:  4-July-2014  J. Westbrook
#
# Update:
#  6-July-2014  jdw add download anchors
#  5- Jan-2015  jdw revise to support access to remote validation server files within the
#                   production context -
# 29- Nov-2016  ep  Add dict-check-report-next to list
# 13- Feb-2016  ep  Add '3DEM Files' to default list for FileUtils.
# 28-Sept-2017  zf  Modified renderFileList() & __renderContentTypeFileList()
##
"""
Manage the presentation of project files for download.


"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os.path
import os
import glob

from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo


class FileUtils(object):
    """
    Manage the presentation of project files for download.

    """

    def __init__(self, entryId, reqObj=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__debug = True
        # Reassign siteId for the following special case --
        self.__entryId = entryId
        siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        # This is for viewing the entries from the standalone validation server from annotation --
        if siteId in ["WWPDB_DEPLOY_PRODUCTION_RU", "WWPDB_DEPLOY_VALSRV_RU", "WWPDB_DEPLOY_TEST", "WWPDB_DEPLOY_INTERNAL_RU"] and entryId.startswith("D_90"):
            siteId = "WWPDB_DEPLOY_VALSRV_RU"
        #
        self.__setup(siteId=siteId)

    def __setup(self, siteId=None):
        if siteId is not None:
            self.__siteId = siteId
        else:
            self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        #
        self.__lfh.write("+FileUtils.__setup() starting with entryId %r adjusted WWPDB_SITE_ID %r\n" % (self.__entryId, self.__siteId))
        #
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        self.__cleanup = False
        self.__currentHeaderFilePath = None
        self.__cI = ConfigInfo(self.__siteId)
        self.__cD = self.__cI.get("CONTENT_TYPE_DICTIONARY")
        self.__msL = self.__cI.get("CONTENT_MILESTONE_LIST")
        #
        self.__rDList = ["Primary Data Files", "Chemical Assignment Files", "Sequence Assignment Files", "Annotation Task Files", "Check reports", "Message Files", "3DEM Files"]
        self.__rD = {
            "Primary Data Files": [
                "model",
                "structure-factors",
                "nmr-restraints",
                "nmr-chemical-shifts",
                "nmr-data-str",
                "nmr-data-nef",
                "nmr-peaks",
                "em-volume",
                "em-mask",
                "img-emdb",
            ],
            "Chemical Assignment Files": [
                "chem-comp-link",
                "chem-comp-assign",
                "chem-comp-assign-final",
                "chem-comp-assign-details",
                "chem-comp-depositor-info",
                "prd-search",
                "component-image",
                "component-definition",
                "auxiliary-file",
            ],
            "Sequence Assignment Files": [
                "seqdb-match",
                "blast-match",
                "seq-assign",
                "seq-data-stats",
                "seq-align-data",
                "polymer-linkage-distances",
                "polymer-linkage-report",
                "sequence-fasta",
                "partial-seq-annotate",
            ],
            "Annotation Task Files": [
                "assembly-report",
                "assembly-assign",
                "interface-assign",
                "assembly-model",
                "assembly-model-xyz",
                "site-assign",
                "map-2fofc",
                "map-fofc",
                "secondary-structure-topology",
                "map-header-data",
                "fsc",
            ],
            "Check reports": [
                "validation-report-depositor",
                "geometry-check-report",
                "polymer-linkage-report",
                "dict-check-report",
                "dict-check-report-r4",
                "dict-check-report-next",
                "format-check-report",
                "misc-check-report",
                "special-position-report",
                "merge-xyz-report",
                "nmr-cs-check-report",
                "nmr-cs-xyz-check-report",
                "validation-report",
                "validation-report-full",
                "validation-report-slider",
                "validation-data",
                "validation-report-2fo-map-coef",
                "validation-report-fo-map-coef",
                "sf-convert-report",
                "dcc-report",
                "mapfix-report",
                "fsc-report",
                "em2em-report",
            ],
            "Message Files": ["messages-from-depositor", "messages-to-depositor", "notes-from-annotator", "correspondence-to-depositor"],
            "3DEM Files": [
                "em-volume",
                "em-mask-volume",
                "em-additional-volume",
                "em-half-volume",
                "em-volume-header",
                "em-model-emd",
                "em2em-report",
                "img-emdb",
                "img-emdb-report",
                "layer-lines",
                "auxiliary-file",
            ],
        }

    def renderFileList(self, fileSource="archive", rDList=None, titlePrefix="", titleSuffix="", displayImageFlag=False):
        """
        """
        if rDList is None:
            rDList = self.__rDList

        htmlList = []
        nTot = 0
        if fileSource in ["archive", "deposit", "wf-archive"]:
            for ky in rDList:
                if ky not in self.__rD:
                    continue
                ctList = self.__rD[ky]
                title = titlePrefix + ky + titleSuffix
                fList = []
                fList.extend(ctList)
                for ct in ctList:
                    for ms in self.__msL:
                        mt = ct + "-" + ms
                        fList.append(mt)
                nF, oL = self.__renderContentTypeFileList(
                    self.__entryId, fileSource=fileSource, wfInstanceId=None, contentTypeList=fList, title=title, displayImageFlag=displayImageFlag
                )
                if nF > 0:
                    htmlList.extend(oL)
                    nTot += nF

        if fileSource in ["archive", "wf-archive"]:
            nF, oL = self.__renderLogFileList(self.__entryId, fileSource="archive", title="Archive Log Files")
            if nF > 0:
                htmlList.extend(oL)
                nTot += nF

        if fileSource in ["deposit"]:
            nF, oL = self.__renderLogFileList(self.__entryId, fileSource="deposit", title="Deposit Log Files")
            if nF > 0:
                htmlList.extend(oL)
                nTot += nF

        #
        if fileSource in ["wf-instance", "instance"]:
            iTopPath = self.__pI.getInstanceTopPath(self.__entryId)
            fPattern = os.path.join(iTopPath, "*")
            wfInstancePathList = filter(os.path.isdir, glob.glob(fPattern))
            for wfInstancePath in wfInstancePathList:
                (_pth, wfInstId) = os.path.split(wfInstancePath)
                title = "Files in " + wfInstId
                nF, oL = self.__renderWfInstanceFileList(self.__entryId, wfInstancePath, title=title)
                if nF > 0:
                    htmlList.extend(oL)
                    nTot += nF
        #
        return nTot, htmlList

    def __renderContentTypeFileList(self, entryId, fileSource="archive", wfInstanceId=None, contentTypeList=None, title=None, displayImageFlag=False):
        if contentTypeList is None:
            contentTypeList = ["model"]
        if self.__verbose:
            self.__lfh.write(
                "+FileUtils.renderContentTypeFileList() entryId %r fileSource %r wfInstanceId %r contentTypeList %r \n" % (entryId, fileSource, wfInstanceId, contentTypeList)
            )
        de = DataExchange(
            reqObj=self.__reqObj, depDataSetId=entryId, wfInstanceId=wfInstanceId, fileSource=fileSource, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh
        )
        tupL = de.getContentTypeFileList(fileSource=fileSource, contentTypeList=contentTypeList)
        #
        rTupL = []
        for tup in tupL:
            href, fN = self.__makeDownloadHref(tup[0])
            if tup[2] > 1:
                sz = "%d" % int(tup[2])
            else:
                sz = "%.3f" % tup[2]
            rTup = (href, tup[1], sz)
            rTupL.append(rTup)
            if displayImageFlag and fN.startswith(entryId + "_img-emdb"):
                imgFile = os.path.join(self.__sessionPath, fN)
                if os.access(imgFile, os.F_OK):
                    os.remove(imgFile)
                #
                os.symlink(tup[0], imgFile)
                imgHtml = '<img src="/sessions/' + self.__sessionId + "/" + fN + '" border="0" alt="Image" width="400" height="400">'
                rTupL.append(("displayImage", imgHtml, ""))
            #
        #
        if title is None:
            cS = ",".join(contentTypeList)
            title = "File Source %s (%s)" % (fileSource, cS)
        nF, htmlList = self.__renderFileList(rTupL, title)

        return nF, htmlList

    def __renderWfInstanceFileList(self, entryId, wfPath, title=None):
        if self.__verbose:
            self.__lfh.write("+FileUtils.renderWfInstanceFileList() wfPath %s\n" % wfPath)

        wfPattern = os.path.join(wfPath, "*")
        de = DataExchange(reqObj=self.__reqObj, depDataSetId=entryId, wfInstanceId=None, fileSource=None, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        tupL = de.getMiscFileList(fPatternList=[wfPattern], sortFlag=True)
        #
        rTupL = []
        for tup in tupL:
            href, _fN = self.__makeDownloadHref(tup[0])
            if tup[2] > 1:
                sz = "%d" % int(tup[2])
            else:
                sz = "%.3f" % tup[2]
            rTup = (href, tup[1], sz)
            rTupL.append(rTup)

        if title is None:
            title = "Workflow instance files for %s" % entryId
        nF, htmlList = self.__renderFileList(rTupL, title)

        return nF, htmlList

    def __renderLogFileList(self, entryId, fileSource="archive", title=None):
        if self.__verbose:
            self.__lfh.write("+FileUtils.renderLogFileList() entryId %r fileSource %r\n" % (entryId, fileSource))
        de = DataExchange(reqObj=self.__reqObj, depDataSetId=entryId, wfInstanceId=None, fileSource=fileSource, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        tupL = de.getLogFileList(entryId, fileSource=fileSource)
        #
        rTupL = []
        for tup in tupL:
            href, _fN = self.__makeDownloadHref(tup[0])
            if tup[2] > 1:
                sz = "%d" % int(tup[2])
            else:
                sz = "%.3f" % tup[2]
            rTup = (href, tup[1], sz)
            rTupL.append(rTup)

        if title is None:
            title = "Log Files in Source %s" % fileSource
        nF, htmlList = self.__renderFileList(rTupL, title)

        return nF, htmlList

    def __renderFileList(self, fileTupleList, title, embeddedTitle=True):
        #
        oL = []
        if len(fileTupleList) > 0:
            if embeddedTitle:
                oL.append('<table class="table table-bordered table-striped table-condensed">')
                oL.append('<tr><th class="width50">%s</th><th class="width30">Modification Time</th><th class="width20">Size (KBytes)</th></tr>' % title)
            else:
                oL.append("<h4>%s</h4>" % title)
                oL.append('<table class="table table-bordered table-striped table-condensed">')
                oL.append('<tr><th class="width50">Files</th><th class="width30">Modification Time</th><th class="width20">Size (KBytes)</th></tr>')
            for tup in fileTupleList:
                oL.append("<tr>")
                if tup[0] == "displayImage":
                    oL.append('<td align="center" colspan="3">%s</td>' % tup[1])
                else:
                    oL.append("<td>%s</td>" % tup[0])
                    oL.append("<td>%s</td>" % tup[1])
                    oL.append("<td>%s</td>" % tup[2])
                #
                oL.append("</tr>")
            #
            oL.append("</table>")
        #
        return len(fileTupleList), oL

    def __makeDownloadHref(self, filePath):
        _dP, fN = os.path.split(filePath)
        tS = "/service/review_v2/download_file?sessionid=" + self.__sessionId + "&file_path=" + filePath
        href = "<a class='my-file-downloadable' href='" + tS + "'>" + fN + "</a>"
        return href, fN
