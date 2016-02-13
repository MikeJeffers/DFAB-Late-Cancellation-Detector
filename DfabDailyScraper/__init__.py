import urllib2
import string
import copy
import time
import os
import threading
from Tkinter import *

##################GLOBALS############################

#Authors note: 
#Updated 2015_2_18_1:24pm


MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']

# TODO this list is incomplete and unordered...
EQUIP = ['1.equipmentappointments-e.vacuumformer(max1hr)',
         '1.equipmentappointments-h.plaster3dprinter(queue)',
         '1.equipmentappointments-i.plastic3dprinter(queue)',
         '1.equipmentappointments-b.lasersystem1(max1hr)',
         '1.equipmentappointments-c.lasersystem2(max1hr)',
         '1.equipmentappointments-d.3-axiscncrouter(max3hrs)',
         '1.equipmentappointments-f.abbirb-4400(max6hrs)',
         '1.equipmentappointments-g.abbirb-6640(max6hrs)',
         '2.officeappointments-1.p.zachali',
         '2.officeappointments-2.mikejeffers',
         '3.afterappointments-cncrouter',
         '3.afterappointments-lasersystem1',
         '3.afterappointments-lasersystem2',
         '3.afterappointments-roboticcell(large)',
         '4.dfabschedule-a.ofoperation',
         '4.dfabschedule-b.openingshift',
         '4.dfabschedule-c.mid-shift',
         '4.dfabschedule-d.closingshift']

RE_EQUIP = ['1e.VacuumFormer',
         '1h.Plaster3DPrinter',
         '1i.Plastic3DPrinter',
         '1b.Laser1',
         '1c.Laser2',
         '1d.3-axis CNC',
         '1f.ABB IRB-4400',
         '1g.ABB IRB-6640',
         '2a.OH: Zach Ali',
         '2b.OH: Mike Jeffers',
         '3.3-axis CNC',
         '3.Laser1',
         '3.Laser2',
         '3.Robots',
         '4.a.ofoperation',
         '4.b.openingshift',
         '4.c.mid-shift',
         '4.d.closingshift']

DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


# global list vars for UI threading reports
LOG_TEXT = []
SUSPECTS = set()  # the usual

QUIT_FLAG = False


##############UI CLASS####################

class userInterface(object):
    def __init__(self, logList=[]):
        self.root = Tk()
        self.width = 800
        self.height = 900
        self.root.bind("<Button-1>", self.mousePressed)
        self.root.bind("<Key>", self.keyPressed)
        self.canvas = Canvas(self.root, width=self.width, height=self.height)
        self.canvas.pack()
        self.titleFont = ('helvetica', 18)
        self.contentFont = ('helvetica', 9)
        self.helpFont = ('helvetica', 7)
        self.count = 0
        self.mod = self.width / 8
        self.LOG = logList
        self.LOGstr = ""
        self.suspectReport = ""
        self.background = "#%02x%02x%02x" % (222, 222, 222)
        self.red = "#%02x%02x%02x" % (245, 15, 5)
        self.green = "#%02x%02x%02x" % (15, 245, 15)
        self.cyan = "#%02x%02x%02x" % (0, 245, 196)
        self.gray = "#%02x%02x%02x" % (190, 190, 190)

    def mousePressed(self, event):
        (x, y, x2, y2) = (self.width - self.mod, 0, self.width, self.mod / 2)
        if(event.x > x and event.x < x2):
            if(event.y > y and event.y < y2):
                self.quitSelf()
        self.redrawAll()


    def keyPressed(self, event):
        self.redrawAll()


    ###########################P0#################

    def drawTitle(self):
        self.canvas.create_text(self.width / 2, self.mod * 0.1, text="DFAB RESERVATION DATA \n CANCELLATION DETECTION", anchor='n', font=self.titleFont)

    def drawHelp(self):
        helpText = """
        Welcome to the Reservation System Automated Late Cancellation Detection Application 
                Making infractions EASY and FUN! 
        Upon opening, the software will scrape data from today's reservation on set intervals.
        The Software actively uses files in a directory: DO NOT MODIFY THESE FILES NOR THEIR LOCATION/PATH!
        A report text file with details for each day will be generated, as well as displayed on this UI.
        """
        self.canvas.create_text(self.mod * 0.1, self.mod, text=helpText, anchor='nw', font=self.helpFont)

    def drawLog(self):
        self.canvas.create_text(self.mod * 0.1, self.mod * 2.5, text=self.LOGstr, anchor='nw', font=self.helpFont)

    def drawReport(self):
        self.canvas.create_text(self.width - (self.mod * 0.1), self.mod * 2.5, text=self.suspectReport, anchor='ne', font=self.helpFont)

    def drawActive(self):
        dots = "."*self.count
        self.canvas.create_text(self.mod, self.mod * 2.2, text="APPLICATION ACTIVE" + dots, anchor='nw', font=self.contentFont)

    def drawShutdown(self):
        dots = "."*self.count
        self.canvas.create_text(self.mod, self.mod * 2.2, text="CLOSING APPLICATION" + dots, anchor='nw', font=self.contentFont)

    def drawQuit(self):
        (x, y, x2, y2) = (self.width - self.mod, 5, self.width, self.mod / 2)
        self.canvas.create_rectangle(x, y, x2, y2, fill=self.green)
        self.canvas.create_text((x + x2) / 2, (y + y2) / 2, text="QUIT", font=self.titleFont)

    def drawBackground(self):
        self.canvas.create_rectangle(-5, -5, self.width + 5, self.height + 5, fill=self.background)

    def redrawAll(self):
        self.canvas.delete(ALL)
        self.drawBackground()
        self.drawTitle()
        self.drawHelp()
        self.drawLog()
        if QUIT_FLAG:
            self.drawShutdown()
        else:
            self.drawActive()
        self.drawReport()
        self.drawQuit()

    def quitSelf(self):
        global QUIT_FLAG
        QUIT_FLAG = True
        print "QUIT FLAG RAISED"
        print "Killing threads..."


    def getLog(self):
        self.LOG = limitLen(copy.deepcopy(LOG_TEXT))
        self.LOGstr = ""
        for s in self.LOG:
            self.LOGstr += s + "\n"

    def getSuspects(self):
        suspects = limitLen(copy.deepcopy(SUSPECTS))
        self.suspectReport = ""
        for s in suspects:
            self.suspectReport += s + "\n"

    def counter(self):
        self.count += 1
        if(self.count > 10):
            self.count = 0

    def timerFired(self):
        self.redrawAll()
        delay = 100
        self.counter()
        self.getLog()
        self.getSuspects()
        self.canvas.after(delay, self.timerFired)

    def run(self):
        self.timerFired()
        self.root.mainloop()


##################ENTRY DICT REFORMATTING#########################
def reFormatContent(entryList):
    for d in entryList:
        for key in d:
            for i in xrange(len(EQUIP)):
                if(d[key] == EQUIP[i]):
                    d[key] = d[key].replace(EQUIP[i], RE_EQUIP[i])
            d[key] = str(d[key])
            d[key] = d[key].replace('hours', '')
            d[key] = d[key].replace('30minutes', '0.5')
            d[key] = d[key].replace('days', '')
            if(key.find("time") != -1):
                for i in xrange(len(DAYS)):
                    d[key] = d[key].replace(DAYS[i], "(" + str(i) + ')*')
            for i in xrange(len(MONTHS)):
                d[key] = d[key].replace(MONTHS[i], "/%02d/" % (i + 1))
    entryList = swapDateFormat(entryList)
    return entryList

def swapDateFormat(entryList):
    for d in entryList:
        for key in d:
            if(key.find("time") != -1):
                i = d[key].find('*')
                if(i != -1):
                    s = d[key]
                    timeStr = s[:i + 1]
                    date = s[i + 1:]
                    spliStr = date.split('/')
                    year = spliStr[2]
                    month = spliStr[1]
                    day = spliStr[0]
                    d[key] = timeStr + year + "_" + month + "_" + day
    return entryList
##################//ENTRY DICT REFORMATTING#########################


################FOR FILE I/O#########################
def extractIDs(content):
    if(content == None):
        return []
    idList = []
    for line in content.split("\n"):
        if(line.find("URLFAILED") != -1 or "!!!" in line):
            continue
        # NOTE: exact formatting depends on the dictToString() Function!!
        start = line.find("#")  # TODO Check these with current writing protocols
        end = line.find(";")
        if(start != -1 and end != -1):
            idList.append(line[start + 1:end])
    return idList

def findTimeStamp(content):
    for line in content.split("\n"):
        if("!!!TIMESTAMP=" in line):
            start = line.find("=")
            return line[start + 1:]
    return ""

def dictToString(entryList):
    s = ""
    for d in entryList:
        idString = ""
        otherKeys = ""
        for key in d:
            if(key == "ID"):
                # This MUST match the ExtractIDs() function
                idString = str(key) + "#" + str(d[key]) + ";"
            elif(key in["description", "repeatenddate", "repeattype", "repeatday"]):
                continue
            else:
                otherKeys += str(key) + "<" + str(d[key]) + ">;"
        s += idString + otherKeys
        s += "\n"
    return s

def fileStringToDict(contents):
    if(contents == None):
        return []
    dictList = []
    for line in contents.splitlines():
        d = {}
        for sub in line.split(";"):
            if(sub.find("ID#") != -1):
                d["ID"] = sub[sub.find("#") + 1:]
            else:
                index = sub.find("<")
                if(index != -1):
                    titleKey = sub[:index]
                    data = sub[index + 1:].replace(">", "")
                    d[titleKey] = data
        dictList.append(d)
    return dictList

def readFile(dateStamp, timeStr):
    try:
        pathStr = "C:\\_DFAB_SCRAPE_LOG\\" + str(dateStamp) + "\\" + str(timeStr) + "entryFile.txt"
        fileObj = open(pathStr, "rt")
        return fileObj.read()
    except:
        return None

def writeFile(contents, dateStamp, timeStr):
    try:
        dirStr = "C:\\_DFAB_SCRAPE_LOG\\" + str(dateStamp) + "\\"
        pathStr = dirStr + str(timeStr) + "entryFile.txt"
        if not os.path.exists(dirStr):
            os.makedirs(dirStr)
        if not os.path.exists(pathStr):
            fileObj = open(pathStr, "a+")
            fileObj.write(contents)
            LOG_TEXT.append("SCRAPE FILE SUCCESSFULLY WRITTEN")
        else:
            LOG_TEXT.append("FILE ALREADY EXISTS, ABORTING WRITE COMMAND")
    except:
        LOG_TEXT.append("WRITE FILE FAILURE!!!")


def writeReportFile(contents, dateStamp):
    try:
        dirStr = "C:\\_DFAB_SCRAPE_LOG\\" + str(dateStamp) + "REPORT\\"
        pathStr = dirStr + str(dateStamp) + "_REPORT.txt"
        if not os.path.exists(dirStr):
            os.makedirs(dirStr)
        fileObj = open(pathStr, "w")
        fileObj.write(contents)
        LOG_TEXT.append("REPORT FILE SUCCESSFULLY WRITTEN")
    except:
        LOG_TEXT.append("WRITE FILE FAILURE!!!")


def getFilesforToday(dateStamp):
    try:
        dirStr = "C:\\_DFAB_SCRAPE_LOG\\" + str(dateStamp) + "\\"
        listOfFiles = []
        for filepath in os.listdir(dirStr):
            if(os.path.isfile(dirStr + filepath)):
                fileObj = open(dirStr + filepath, "rt")
                listOfFiles.append(fileObj.read())
        LOG_TEXT.append("FILE RETRIVAL SUCCESS")
        return listOfFiles
    except:
        LOG_TEXT.append("FILE RETRIVAL FAILURE!!!")
        return []

##################//FileIO########################


def getEntriesOnPage(pageRaw):
    currentEntryIDs = []
    match = '<a href="view_entry.php?id='
    strList = pageRaw.split(match)
    walkPartial = strList[1:]
    for s in walkPartial:
        sub = s.split("&amp;")
        currentEntryIDs.append(int(sub[0]))
    return currentEntryIDs

######## HTML SCRAPING HELPERS ##############
def getIDfromUrl(urlStr):
    index = urlStr.find("=")
    idStr = ""
    if(index != -1):
        idStr = urlStr[index + 1:]
    return idStr

def parseHTMLofEntry(entry):
    startIndex = entry.find('<table id="entry">')
    entry = entry[startIndex:]
    endIndex = entry.find('</table>')
    entry = entry[:endIndex]
    entry = entry.lower()
    entry = entry.replace("</tr>", '')
    entry = entry.replace('\n', '')
    entry = entry.replace(' ', '')
    return entry

def getEntryAsDict(entry, idStr):
    titles = []
    contents = []
    entryDict = {"ID": idStr}
    for s in entry.split("<tr>"):
        i = 0
        for sub in s.split("<td>"):
            if(i == 1):
                title = sub.replace("</td>", '').replace(":", '')
                titles.append(title)
            elif(i == 2):
                contents.append(sub.replace("</td>", ''))
            i += 1
    if(len(contents) == len(titles)):
        for i in xrange(len(titles)):
            if titles[i] not in entryDict:
                entryDict[titles[i]] = contents[i]
            else:
                entryDict[titles[i]] += contents[i]
    return entryDict


def scrapeUrl(url):
    request = urllib2.Request(url)
    try:
        page = opener.open(request)
        raw = page.read()
        LOG_TEXT.append("URL Success for " + url.split("?")[1])
    except:
        raw = ""
        LOG_TEXT.append("URL Request Failure!!!")
    return raw

######## Misc Helpers ##############


def findToday(raw):
    # <h2 id="dwm">Monday 03 November 2014</h2>
    targetStr = '<h2 id="dwm">'
    startIndex = raw.find(targetStr)
    raw = raw[startIndex + len(targetStr):]
    endIndex = raw.find('</h2>')
    raw = raw[:endIndex]
    raw = raw.lower()
    raw = raw.replace('\n', '')
    raw = raw.replace(' ', '')
    for i in xrange(len(DAYS)):
        raw = raw.replace(DAYS[i], "(" + str(i) + ')*')
    for i in xrange(len(MONTHS)):
        raw = raw.replace(MONTHS[i], "/%02d/" % (i + 1))
    index = raw.find("*")
    date = raw[index + 1:]
    splitStr = date.split('/')
    splitStr.reverse()
    outStr = ""
    for s in splitStr:
        outStr += s + "_"
    outStr = outStr[:len(outStr) - 1]
    return outStr


def getCurrentDay():
    todayURL = "http://cmu-dfab.org/reservations/day.php?area=1&room=1"
    raw = scrapeUrl(todayURL)
    return findToday(raw)


def scrapeTime():
    global opener
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    todayURL = "http://cmu-dfab.org/reservations/day.php?area=1&room=1"
    raw = scrapeUrl(todayURL)
    dateStamp = findToday(raw)
    dayTest = getCurrentDay()  # from scrape
    dayCheck = time.strftime("%Y_%m_%d")  # from Server
    if (dayTest==dayCheck):
        timeStr = time.strftime("%M_%H_")
        idsToCheck = getEntriesOnPage(raw)
        entryDictList = []
        for x in idsToCheck:
            url = "http://cmu-dfab.org/reservations/view_entry.php?id=%d" % (x)
            entryRaw = scrapeUrl(url)
            entryDictList.append(getEntryAsDict(parseHTMLofEntry(entryRaw), x))
        entryDictList = reFormatContent(entryDictList)
        outToFile = dictToString(entryDictList)
        # TimeStamp tag to end of file for later bookkeeping and parsing
        outToFile += "!!!TIMESTAMP=" + timeStr + "\n"
        writeFile(outToFile, dateStamp, timeStr)


def crossReference(dayToCheck):
    listOfLogs = getFilesforToday(dayToCheck)
    listOfTimeStamps = []
    listOfTimeValues = []
    uniqueIDMaster = set()  # clear master, set of all unique IDS of entries across all files
    uniqueEntryMaster = []  # list of all unique entryDicts
    listOfListOfIDS = []  # 2D list of all IDs per entry
    listOfListOfDicts = []
    for log in listOfLogs:
        listOfListOfDicts.append(fileStringToDict(log))
        listOfTimeStamps.append(findTimeStamp(log))
        listOfTimeValues.append(convertTimeStamp(findTimeStamp(log)))


    for listOfDicts in listOfListOfDicts:
        subListOfIDs = set()
        for d in listOfDicts:
            for key in d:
                if (key == 'ID'):
                    subListOfIDs.add(d[key])
                    if d[key] not in uniqueIDMaster:
                        uniqueIDMaster.add(d[key])
                        uniqueEntryMaster.append(d)
        listOfListOfIDS.append(list(subListOfIDs))

    dictByTimeStamp = dict()
    if(len(listOfListOfIDS) == len(listOfTimeStamps)):
        for i in xrange(len(listOfTimeStamps)):
            dictByTimeStamp[listOfTimeStamps[i]] = listOfListOfIDS[i]

    flaggedIDs = set()
    flaggedEntries = []
    reportData = ""
    listOfTimeValues = sorted(listOfTimeValues)
    for ID in uniqueIDMaster:
        subList = []
        for key in dictByTimeStamp:
            if(ID in dictByTimeStamp[key]):
                subList.append(convertTimeStamp(key))
        subList = sorted(subList)
        for d in uniqueEntryMaster:
            if(d['ID'] == ID):
                startTime = getStartTime(d)
                lastRecord = max(subList)
                indexNext = listOfTimeValues.index(lastRecord) + 1
                if(indexNext < len(listOfTimeValues)):
                    nextRecord = listOfTimeValues[indexNext]
                    cTime = int(time.strftime("%H%M"))
                    if(lastRecord < cTime and lastRecord > startTime - 200 and getDay(d) == dayToCheck):
                        flaggedIDs.add(ID)
                        flaggedEntries.append(d)
                        toPrint = dayToCheck + " " + getAuthor(d) + " cancelled reservation for " + toAMPM(startTime) + " between " + toAMPM(lastRecord) + "-" + toAMPM(nextRecord)
                        reportData += toPrint + "\n"
                        SUSPECTS.add(toPrint)
    content = dictToString(flaggedEntries) + "\n" + reportData
    writeReportFile(content, dayToCheck)

def getDay(d):
    if('starttime' in d):
        theDate = d['starttime'].split("*")[1]
        return theDate
    return ""

def getStartTime(d):
    if('starttime' in d):
        theTime = d['starttime'].split("-(")[0]
        return convertAMPM(theTime)
    return ""

def getAuthor(d):
    if('createdby' in d):
        theAuthor = d['createdby']
        return theAuthor
    return ""

def getEndTime(d):
    if('endtime' in d):
        theTime = d['endtime'].split("-(")[0]
        return convertAMPM(theTime)
    return ""

def convertAMPM(timeStr):
    hhmm = timeStr.split(":")[:2]
    if(timeStr.find("pm") != -1 and int(hhmm[0]) < 12):
        hhmm[0] = int(hhmm[0]) + 12
    return int(hhmm[0]) * 100 + int(hhmm[1])

def toAMPM(timeInt):
    timeStr = str(timeInt)
    if(len(timeStr) < 4):
        timeStr = "0" + timeStr
    hh = timeStr[:2]
    ampm = "am"
    if(int(hh) > 12 and int(hh) < 24):
        hh = str(int(hh) - 12)
        ampm = "pm"
    elif(int(hh) == 12):
        ampm = "pm"
    elif(int(hh) >= 24):
        hh = str(int(hh) - 12)
    mm = timeStr[2:]
    timeStr = hh + ":" + mm + ampm
    return timeStr

def convertTimeStamp(tStamp):
    tUnit = []
    for s in tStamp.split("_"):
        if(s != ""):
            tUnit.append(int(s))
    tUnit.reverse()
    tVal = tUnit[0] * 100 + tUnit[1]
    return tVal

def getIndexofMax(L):
    maxValue = -10000000
    maxIndex = 0
    for i in xrange(len(L)):
        if(L[i] > maxValue):
            maxIndex = i
            maxValue = L[i]
    return maxIndex

def limitLen(L):
    lim = 35
    if (len(L) > lim):
        d = len(L) - lim
        return L[d:]
    else:
        return L


def main():
    global LOG_TEXT
    global SUSPECTS
    LOG_TEXT = []
    SUSPECTS = set()
    UI = userInterface(logList=LOG_TEXT)
    t = threading.Thread(target=UI.run)
    t.daemon = True
    t.start()
    #Sleep loop parameters(seconds)
    waitTime = 300 #total time of sleep between runs
    refreshRate = 5 #open one eye every X seconds to check thread status
    
    while True:
        if(QUIT_FLAG):
            print "Program Terminated"
            break
        
        scrapeTime()
        # check if time is near midnight--Avoids writing entries from previous day to current
        # Also verify that current day from scrape==time by computer clock
        timeCheck = int(time.strftime("%H%M"))
        dayTest = getCurrentDay()  # from scrape
        dayCheck = time.strftime("%Y_%m_%d")  # from Server
        if(timeCheck < 2330 and timeCheck > 0030 and dayTest == dayCheck):
            currentDay = dayTest
            crossReference(currentDay)
            #print "#Suspects: " + str(len(SUSPECTS))
            LOG_TEXT.append("Cross-reference Cycle Complete at " + toAMPM(int(time.strftime("%H%M"))))
        else:
            # Suspects to display on UI get cleared daily between 11:30pm and 12:30am
            # Nothing else happens here
            SUSPECTS.clear()
        #Then sleep
        for x in xrange(int(waitTime/refreshRate)):
            time.sleep(refreshRate)
            if(QUIT_FLAG):
                print "... No Survivors"
                break


######################################
if __name__ == "__main__":
    main()
