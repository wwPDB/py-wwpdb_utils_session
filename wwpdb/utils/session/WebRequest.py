##
# File:    WebRequest.py
# Date:    18-Jan-2010  J. Westbrook
#
# Updated:
# 20-Apr-2010 Ported to seqmodule package
# 25-Jul-2010 Ported to ccmodule package
# 24-Aug-2010 Add dictionary update for content request object.
#
# 26-Feb-2012 jdw  add support location redirects in response object-
# 20-Feb-2013 jdw  This application neutral version moved to utils/rcsb.
#                  Make dictionary in ResponseContent inheritable.
# 06-Mar-2013 jdw  add setDictionary() method
# 07-Mar-2013 jdw  add optional maximum length parameter to response object dump() method.
# 22-Mar-2013 jdw  incorporate methods for handling binary content, jsonp, and datafile
#                  download data in response content class.
# 22-Mar-2013 jdw  restore method - getValueOrDefault(self,myKey,default='')
# 11-Oct-2013 zf   add getDictionary() method
# 22-Dec-2013 jdw  Add HTML template processing method - setHtmlFromTemplate()
# 27-Feb-2014 jdw  Add setReturnFormat() method -
# 13-Jul-2014 jdw  Adjust formating in print methods
##
"""
WebRequest provides containers and accessors for managing request parameter information.

This is an application neutral version shared by UI modules --

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import sys
import os
import traceback
import gzip
import mimetypes

try:
    from json import loads, dumps
except:  # noqa: E722 pylint: disable=bare-except
    from simplejson import loads, dumps

from wwpdb.utils.session.SessionManager import SessionManager
from datetime import datetime


def json_serializer_helper(obj):
    """ Helper function to handle = objects not serializable by default json code

        Current -  handling datetime objects and falling back to str()
    """

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    else:
        try:
            serial = str(obj)
            return serial
        except Exception as e:
            raise TypeError("Could not convert object to string %r %r " % (obj, str(e)))
    #
    raise TypeError("Type not serializable %r " % obj)


class WebRequest(object):

    """ Base container and accessors for input and output parameters and control information.
    """

    def __init__(self, paramDict=None, verbose=False):
        if paramDict is None:
            paramDict = {}
        self.__verbose = verbose
        #
        #  Input and storage model is dictionary of lists (e.g. dict[myKey] = [,,,])
        #  Single values are stored in the leading element of the list (e.g. dict[myKey][0])
        #
        self.__dict = paramDict
        self.__debug = False

    def __str__(self):
        try:
            sL = []
            sL.append("\n+WebRequest.printIt() WebRequest dictionary contents:\n")
            for k, vL in self.__dict.items():
                sL.append("  - Key: %-35s  value(s): %r\n" % (k, vL))
            sL.append("   --------------------------------------------\n")
            return "".join(sL)
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def __repr__(self):
        return self.__str__()

    def printIt(self, ofh=sys.stdout):
        try:
            ofh.write("\n +WebRequest.printIt() WebRequest dictionary contents:\n")

            for k in sorted(self.__dict.keys()):
                vL = self.__dict[k]
                ofh.write("  - Key: %-35s  value(s): %r\n" % (k, vL))
            ofh.write("   --------------------------------------------\n")
        except:  # noqa: E722 pylint: disable=bare-except
            pass

    def dump(self, format="text"):  # pylint: disable=redefined-builtin
        oL = []
        try:
            if format == "html":
                oL.append("<pre>\n")
            oL.append("\n+nWebRequest.dump() Request Dictionary Contents:\n")
            for k, vL in self.__dict.items():
                oL.append("  - Key: %-35s  value(s): %r\n" % (k, vL))
            oL.append("   --------------------------------------------\n")
            if format == "html":
                oL.append("</pre>\n")
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        return oL

    def getJSON(self):
        return dumps(self.__dict)

    def setJSON(self, JSONString):
        self.__dict = loads(JSONString)

    def getValue(self, myKey):
        return self._getStringValue(myKey)

    def getValueOrDefault(self, myKey, default=""):
        if not self.exists(myKey):
            return default
        v = self._getStringValue(myKey)
        if len(v) < 1:
            return default
        return v

    def getValueList(self, myKey):
        return self._getStringList(myKey)

    def getRawValue(self, myKey):
        return self._getRawValue(myKey)

    def getDictionary(self):
        return self.__dict

    #

    def setValue(self, myKey, aValue):
        self.__dict[myKey] = [aValue]

    def setValueList(self, myKey, valueList):
        self.__dict[myKey] = valueList

    def setDictionary(self, myDict, overWrite=False):
        for k, v in myDict.items():
            if overWrite or (not self.exists(k)):
                self.setValue(k, v)

    def exists(self, myKey):
        try:
            return myKey in self.__dict
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    #
    def _getRawValue(self, myKey):
        try:
            return self.__dict[myKey][0]
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def _getStringValue(self, myKey):
        try:
            return str(self.__dict[myKey][0]).strip()
        except:  # noqa: E722 pylint: disable=bare-except
            return ""

    def _getIntegerValue(self, myKey):
        try:
            return int(self.__dict[myKey][0])
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def _getDoubleValue(self, myKey):
        try:
            return float(self.__dict[myKey][0])
        except:  # noqa: E722 pylint: disable=bare-except
            return None

    def _getStringList(self, myKey):
        try:
            return self.__dict[myKey]
        except:  # noqa: E722 pylint: disable=bare-except
            return []


class InputRequest(WebRequest):
    def __init__(self, paramDict, verbose=False, log=sys.stderr):
        super(InputRequest, self).__init__(paramDict, verbose)
        self.__verbose = verbose
        self.__lfh = log
        self.__returnFormatDefault = ""

    def setDefaultReturnFormat(self, return_format="html"):
        self.__returnFormatDefault = return_format
        if not self.exists("return_format"):
            self.setValue("return_format", self.__returnFormatDefault)

    def getRequestPath(self):
        return self._getStringValue("request_path")

    def getReturnFormat(self):
        if not self.exists("return_format"):
            self.setValue("return_format", self.__returnFormatDefault)
        return self._getStringValue("return_format")

    def setReturnFormat(self, return_format="html"):
        return self.setValue("return_format", return_format)

    def getSessionId(self):
        return self._getStringValue("sessionid")

    def getSessionPath(self):
        return os.path.join(self._getStringValue("TopSessionPath"), "sessions")

    def getTopSessionPath(self):
        return self._getStringValue("TopSessionPath")

    def getSemaphore(self):
        return self._getStringValue("semaphore")

    def getSessionObj(self):
        if self.exists("TopSessionPath"):
            sObj = SessionManager(topPath=self._getStringValue("TopSessionPath"))
        else:
            sObj = SessionManager()
        sObj.setId(uid=self._getStringValue("sessionid"))
        return sObj

    def newSessionObj(self, forceNew=False):
        if self.exists("TopSessionPath"):
            sObj = SessionManager(topPath=self._getStringValue("TopSessionPath"))
        else:
            sObj = SessionManager()

        sessionId = self._getStringValue("sessionid")

        if forceNew:
            sObj.assignId()
            sObj.makeSessionPath()
            self.setValue("sessionid", sObj.getId())
        elif len(sessionId) > 0:
            sObj.setId(sessionId)
            sObj.makeSessionPath()
        else:
            sObj.assignId()
            sObj.makeSessionPath()
            self.setValue("sessionid", sObj.getId())

        return sObj


#


class ResponseContent(object):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        Manage content items to be transfered as part of the application response.

        """
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self._cD = {}
        self.__debug = False
        self.__returnFormat = ""
        self.__setup()

    def __setup(self):
        """ Default response content is set here.
        """
        self._cD["htmllinkcontent"] = ""
        self._cD["htmlcontent"] = ""
        self._cD["textcontent"] = ""
        self._cD["location"] = ""
        self._cD["datatype"] = None
        self._cD["encodingtype"] = None
        self._cD["datafilename"] = None
        self._cD["disposition"] = None

        #
        self._cD["datacontent"] = None
        self._cD["errorflag"] = False
        self._cD["statustext"] = ""
        # legacy setting --
        self._cD["errortext"] = ""
        if self.__reqObj is not None:
            self._cD["sessionid"] = self.__reqObj.getSessionId()
            self._cD["semaphore"] = self.__reqObj.getSemaphore()
            # Default comes from the input request object
            self.__returnFormat = self.__reqObj.getReturnFormat()
        else:
            self._cD["sessionid"] = ""
            self._cD["semaphore"] = ""
        #

    def setData(self, dataObj=None):
        self._cD["datacontent"] = dataObj

    def set(self, key, val, asJson=False):
        if asJson:
            try:
                self._cD[key] = dumps(val, default=json_serializer_helper)
            except Exception as e:
                self.__lfh.write("+set() failed %r\n" % str(e))
                traceback.print_exc(file=self.__lfh)
        else:
            self._cD[key] = val

    def setHtmlList(self, htmlList=None):
        if htmlList is None:
            htmlList = []
        self._cD["htmlcontent"] = "\n".join(htmlList)

    def appendHtmlList(self, htmlList=None):
        if htmlList is None:
            htmlList = []
        if len(self._cD["htmlcontent"]) > 0:
            self._cD["htmlcontent"] = "%s\n%s" % (self._cD["htmlcontent"], "\n".join(htmlList))
        else:
            self._cD["htmlcontent"] = "\n".join(htmlList)

    def setHtmlText(self, htmlText=""):
        self._cD["htmlcontent"] = htmlText

    def setHtmlTextFromTemplate(self, templateFilePath, webIncludePath, parameterDict=None, insertContext=False):
        pD = parameterDict if parameterDict is not None else {}
        self._cD["htmlcontent"] = self.__processTemplate(templateFilePath=templateFilePath, webIncludePath=webIncludePath, parameterDict=pD, insertContext=insertContext)

    def setHtmlLinkText(self, htmlText=""):
        self._cD["htmllinkcontent"] = htmlText

    def setText(self, text=""):
        self._cD["textcontent"] = text

    def setLocation(self, url=""):
        self._cD["location"] = url

    def addDictionaryItems(self, cD=None):
        if cD is None:
            cD = {}
        for k, v in cD.items():
            self._cD[k] = v

    def setTextFile(self, filePath):
        try:
            if os.path.exists(filePath):
                with open(filePath, "r") as fin:
                    self._cD["textcontent"] = fin.read()
        except Exception as e:
            self.__lfh.write("+setTextFile() File read failed %s %s\n" % (filePath, str(e)))
            traceback.print_exc(file=self.__lfh)

    def setTextFileO(self, filePath):
        with open(filePath, "r") as fin:
            self._cD["textcontent"] = fin.read()

    def getMimetypeAndEncoding(self, filename):
        mtype, encoding = mimetypes.guess_type(filename)
        # We'll ignore encoding, even though we shouldn't really
        if mtype is None:
            if filename.find(".cif.V") > 0:
                ret = ("text/plain", None)
            else:
                ret = ("application/octet-stream", None)
        else:
            ret = (mtype, encoding)
        return ret

    def setBinaryFile(self, filePath, attachmentFlag=False, serveCompressed=True):
        try:
            if os.path.exists(filePath):
                _dir, fn = os.path.split(filePath)
                if not serveCompressed and fn.endswith(".gz"):
                    with gzip.open(filePath, "rb") as fin:
                        self._cD["datacontent"] = fin.read()
                    self._cD["datafileName"] = fn[:-3]
                    contentType, encodingType = self.getMimetypeAndEncoding(filePath[:-3])
                else:
                    with open(filePath, "rb") as fin:
                        self._cD["datacontent"] = fin.read()
                    self._cD["datafileName"] = fn
                    contentType, encodingType = self.getMimetypeAndEncoding(filePath)
                #
                self._cD["datatype"] = contentType
                self._cD["encodingtype"] = encodingType
                if attachmentFlag:
                    self._cD["disposition"] = "attachment"
                else:
                    self._cD["disposition"] = "inline"
                    #
                    # strip compression file extension if disposition=inline.
                    if fn.endswith(".gz"):
                        self._cD["datafileName"] = fn[:-3]

                if self.__verbose:
                    self.__lfh.write("+ResponseContent.setBinaryFile() Serving %s as %s encoding %s att flag %r\n" % (filePath, contentType, encodingType, attachmentFlag))
        except Exception as e:
            self.__lfh.write("ResponseContent.setBinaryFile() File read failed %s error: %r\n" % (filePath, str(e)))
            traceback.print_exc(file=self.__lfh)

    def wrapFileAsJsonp(self, filePath, callBack=None):
        try:
            if os.path.exists(filePath):
                _dir, fn = os.path.split(filePath)
                (_rn, ext) = os.path.splitext(fn)
                #
                dd = {}
                with open(filePath, "r") as fin:
                    dd["data"] = fin.read()
                if ext.lower() != ".json":
                    self._cD["datacontent"] = callBack + "(" + dumps(dd) + ");"
                else:
                    self._cD["datacontent"] = callBack + "(" + dd["data"] + ");"
                #
                self._cD["datafileName"] = fn
                contentType = "application/x-javascript"
                encodingType = None
                #
                self._cD["datatype"] = contentType
                self._cD["encodingtype"] = encodingType
                self._cD["disposition"] = "inline"
                #
                if self.__debug:  # pragma: no cover
                    self.__lfh.write("+ResponseContent.wrapFileAsJsonp() Serving %s as %s\n" % (filePath, self._cD["datacontent"]))
        except Exception as e:
            self.__lfh.write("ResponseContent.wrapFileAsJsonp() File read failed %s err=%r\n" % (filePath, str(e)))
            traceback.print_exc(file=self.__lfh)

    def setStatus(self, statusMsg="", semaphore=""):
        self._cD["errorflag"] = False
        self._cD["statustext"] = statusMsg
        self._cD["semaphore"] = semaphore

    def isError(self):
        return self._cD["errorflag"]

    def setError(self, errMsg="", semaphore=""):
        self._cD["errorflag"] = True
        self._cD["statustext"] = errMsg
        # legacy setting -
        self._cD["errortext"] = errMsg
        self._cD["semaphore"] = semaphore

    def setStatusCode(self, aCode):
        self._cD["statuscode"] = aCode

    def setHtmlContentPath(self, aPath):
        self._cD["htmlcontentpath"] = aPath

    def dump(self, maxLength=130):
        retL = []
        retL.append("\n +ResponseContent.dump() - response content object\n")
        for k, v in self._cD.items():
            if v is None:
                continue
            elif isinstance(v, dict):
                retL.append("  - key = %-35s " % k)
                retL.append("  - dict : %s\n" % list(v.items()))
            elif v is not None and len(str(v).strip()) > 0:
                retL.append("  - key = %-35s " % k)
                retL.append(" value(1-%d): %s\n" % (maxLength, str(v)[:maxLength]))
        return retL

    def setReturnFormat(self, format):  # pylint: disable=redefined-builtin
        if format in ["html", "text", "json", "jsonText", "jsonData", "location", "binary", "jsonp"]:
            self.__returnFormat = format
            return True
        else:
            return False

    def get(self):
        """Repackage the response for Apache according to the input return_format='html|json|text|...'
        """
        rD = {}
        if self.__returnFormat == "html":
            if self._cD["errorflag"] is False:
                rD = self.__initHtmlResponse(self._cD["htmlcontent"])
            else:
                rD = self.__initHtmlResponse(self._cD["statustext"])
        elif self.__returnFormat == "text":
            if self._cD["errorflag"] is False:
                rD = self.__initTextResponse(self._cD["textcontent"])
            else:
                rD = self.__initHtmlResponse(self._cD["statustext"])
        elif self.__returnFormat == "json":
            rD = self.__initJsonResponse(self._cD)
        elif self.__returnFormat == "jsonText":
            rD = self.__initJsonResponseInTextArea(self._cD)
        elif self.__returnFormat == "jsonData":
            rD = self.__initJsonResponse(self._cD["datacontent"])
        elif self.__returnFormat == "location":
            rD = self.__initLocationResponse(self._cD["location"])
        elif self.__returnFormat == "binary":
            rD = self.__initBinaryResponse(self._cD)
        elif self.__returnFormat == "jsonp":
            rD = self.__initJsonpResponse(self._cD)
        else:
            pass
        #
        return rD

    def __initLocationResponse(self, url):
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "location"
        rspDict["RETURN_STRING"] = url
        return rspDict

    def __initBinaryResponse(self, myD=None):
        if myD is None:
            myD = {}
        rspDict = {}
        rspDict["CONTENT_TYPE"] = myD["datatype"]
        rspDict["RETURN_STRING"] = myD["datacontent"]
        try:
            rspDict["ENCODING"] = myD["encodingtype"]
            if myD["disposition"] is not None:
                rspDict["DISPOSITION"] = "%s; filename=%s" % (myD["disposition"], myD["datafileName"])
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return rspDict

    def __initJsonResponse(self, myD=None):
        if myD is None:
            myD = {}
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "application/json"
        rspDict["RETURN_STRING"] = dumps(myD)
        return rspDict

    def __initJsonpResponse(self, myD=None):
        if myD is None:
            myD = {}
        rspDict = {}
        rspDict["CONTENT_TYPE"] = myD["datatype"]
        rspDict["RETURN_STRING"] = myD["datacontent"]
        return rspDict

    def __initJsonResponseInTextArea(self, myD=None):
        if myD is None:
            myD = {}
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "text/html"
        # rspDict['CONTENT_TYPE']  = 'text/plain'
        rspDict["RETURN_STRING"] = "<textarea>" + dumps(myD) + "</textarea>"
        return rspDict

    def __initHtmlResponse(self, myHtml=""):
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "text/html"
        rspDict["RETURN_STRING"] = myHtml
        return rspDict

    def __initTextResponse(self, myText=""):
        rspDict = {}
        rspDict["CONTENT_TYPE"] = "text/plain"
        rspDict["RETURN_STRING"] = myText
        return rspDict

    def __processTemplate(self, templateFilePath="./alignment_template.html", webIncludePath=".", parameterDict=None, insertContext=False):
        """ Read the input HTML template data file and perform the key/value substitutions in the
            input parameter dictionary.

            if insertContext is set then paramDict is injected as a json object if <!--insert application_context=""-->

            Template HTML file path -  (e.g. /../../htdocs/<appName>/template.html)
            webTopPath = file system path for web includes files  (eg. /../../htdocs) which will
                         be prepended to embedded include path in the HTML template document
        """
        if parameterDict is None:
            parameterDict = {}
        try:
            ifh = open(templateFilePath, "r")
            sL = []
            for line in ifh.readlines():
                if str(line).strip().startswith("<!--#include") or (insertContext and str(line).strip().startswith("<!--#insert")):
                    fields = str(line).split('"')
                    tpth = os.path.join(webIncludePath, fields[1][1:])
                    try:
                        tfh = open(tpth, "r")
                        sL.append(tfh.read())
                        tfh.close()
                    except Exception as e:
                        if self.__verbose:
                            self.__lfh.write("+WebRequest.__processTemplate() failed to include %s fields=%r err=%r\n" % (tpth, fields, str(e)))
                else:
                    sL.append(line)
            ifh.close()
            sIn = "".join(sL)
            return sIn % parameterDict
        except Exception as e:
            if self.__verbose:
                self.__lfh.write("+WebRequest.__processTemplate() failed for %s %r\n" % (templateFilePath, str(e)))
                traceback.print_exc(file=self.__lfh)

        return ""


if __name__ == "__main__":  # pragma: no cover
    rC = ResponseContent()
