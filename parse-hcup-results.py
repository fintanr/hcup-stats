#!/usr/bin/python
#
# Extract data from the Wikipedia Heineken Cup Pool Stages
# and create a tidy data set for use in R
#
# A lot of this code handles corner cases and deals with variants
# in the wikipedia pages, and it hasn't been refactored
#

import re
import sys
import unicodedata
from urllib2 import urlopen
from bs4 import BeautifulSoup

infile = "input-pages.txt"
urlbase = "http://en.wikipedia.org/w/index.php?title"

urls = {}
ourData = []

headers = "season,poolId,matchDate,matchTime,homeTeam,awayTeam,matchReferee"
headers = "%s,matchAttendance,matchScore,homeTries,homePenaltyTries" % headers
headers = "%s,homeTriesTimes,homeConversions,awayTries,awayPenaltyTries" % headers
headers = "%s,awayTriesTimes,awayConversons,homePenalties,homePeanaltiesTimes,homeDrops" % headers
headers = "%s,homeDropTimes,awayPenalties,awayPenaltiesTimes" % headers
headers = "%s,awayDrops,awayDropsTimes" % headers

ourData.append(headers)

def getTries(inString):
    myString = unicodedata.normalize('NFKD', inString).encode('ascii', 'ignore')
    tries = re.split("'", myString)

    penaltyTryCount = 0
    theseTries = []

    for thistry in tries:
        thisTime = re.match("(.*)\s(\d+)", thistry)
        if ( thisTime ):
            theseTries.append(thisTime.group(2))

            penaltyMatch = re.match(".*penalty try.*", thistry, re.IGNORECASE)
            if ( penaltyMatch ):
                penaltyTryCount += 1

    return (penaltyTryCount, theseTries)

def getConversions(inString):
    myString = unicodedata.normalize('NFKD', inString).encode('ascii', 'ignore')

    # this is a little risky, but seems to get every case
    # there are a number of commented out values, but our regex elimiates
    # these
    cons = re.split("\)", myString)

    totalConversions = 0

    for con in cons:
        thisConCount = re.match(".*\[\[.*\|.*\]\]\s\((\d+)\/\d+", con)
        if ( thisConCount ):
            totalConversions += int(thisConCount.group(1))

    return totalConversions

def getPenOrDrop(inString):
    myString = unicodedata.normalize('NFKD', inString).encode('ascii', 'ignore')
    pens = re.split("'", myString)
    thesePenalties = []

    for pen in pens:
        penMatch = re.match(".*\s(\d+)(,|)", pen)
        if ( penMatch ):
           thesePenalties.append(penMatch.group(1))

    return thesePenalties

def getMatchScore(inString):
    myString = unicodedata.normalize('NFKD', inString).encode('ascii', 'ignore')

    matchScore = re.sub("&ndash;", "-", myString)
    return myString

def getReferee(inString):
    myString = unicodedata.normalize('NFKD', inString).encode('ascii', 'ignore')
    ref = "NA"
    # 2012/ 13 match
    refMatch = re.match(".*\[\[(.*)\]\](\s+|<).*", myString)

    if ( refMatch ):
        subTest = re.match(".*\|(.*)", refMatch.group(1))
        if ( subTest ):
            ref = subTest.group(1)
        else:
            ref = refMatch.group(1)
    else:
    # 2010 / 11 format, e.g. 
    # John Lacey ([[Irish Rugby Football Union|Ireland]])
        refMatch = re.match("(.*)\s\(\[\[.*\]\]\)", myString)

        if ( refMatch ):
            ref = refMatch.group(1)

    return ref

def getTeamName(inString):
    myString = unicodedata.normalize('NFKD', inString).encode('ascii', 'ignore')

    # teamMatch has a couple of possible formats, work through them
    # all until we get the correct match and then extract the team name

    team = "Not Found"
    teamMatch = re.match(".*\[\[(.*)\]\].*", myString)
    if ( teamMatch ):
        filterMatch = re.match(".*\|(.*)", teamMatch.group(1))

        if ( filterMatch ):
            team = filterMatch.group(1)
        else:
            team = teamMatch.group(1)
    else:
        # 2010 / 11 formatting for team names
        teamMatch = re.match("\s+{{.*}}\s+(.*)", myString)
        if ( teamMatch ):
            team = teamMatch.group(1)
        else:
            teamMatch = re.match("(.*)\s{{.*}}", myString)
            if ( teamMatch ):
                team = teamMatch.group(1)

    # tidy up the whitespace around the name
    team = re.sub("^\s+","", re.sub("\s+$", "", team))
    return team

def buildTidyData(season, poolId, inData):

    matchDate = re.sub("\s+$", "", inData.get('date'))
    matchTime = re.sub("^\s+", "", re.sub("\s+$", "", inData.get('time')))
    matchScore = re.sub("&ndash;", "-", inData.get('score'))
    #matchScore = unicodedata.normalize('NFKD', matchScore).encode('utf8', 'ignore')
    #matchScore = getMatchScore(inData.get('score'))
    matchAttendance = inData.get('attendance')
    matchAttendance = re.sub(",", "", matchAttendance)

    homeTeam = getTeamName(inData.get('home'))
    awayTeam = getTeamName(inData.get('away'))

    matchReferee = getReferee(inData.get('referee'))

    # default scoring data
    homePenaltyTries = 0
    homeTries = []
    homeTriesTimes = ""
    homeConversions = 0
    awayPenaltyTries = 0
    awayTries = []
    awayTriesTimes = ""
    awayConversions = 0
    homePenalties = []
    homePenaltiesTimes = ""
    awayPenalties = []
    awayPenaltiesTimes = ""
    homeDrops = []
    homeDropsTimes = ""
    awayDrops = []
    awayDropsTimes = ""

    if 'try1' in inData.keys():
        (homePenaltyTries, homeTries) = getTries(inData.get('try1'))
        homeTriesTimes = extractTimes(homeTries)
        if 'con1' in inData.keys():
            homeConversions = getConversions(inData.get('con1'))

    if 'try2' in inData.keys():
        (awayPenaltyTries, awayTries) = getTries(inData.get('try2'))
        awayTriesTimes = extractTimes(awayTries)
        if 'con2' in inData.keys():
            awayConversions = getConversions(inData.get('con2'))

    if 'pen1' in inData.keys():
       homePenalties = getPenOrDrop(inData.get('pen1'))
       homePenaltiesTimes = extractTimes(homePenalties)

    if 'pen2' in inData.keys():
       awayPenalties = getPenOrDrop(inData.get('pen2'))
       awayPenaltiesTimes = extractTimes(awayPenalties)

    if 'drop1' in inData.keys():
       homeDrops = getPenOrDrop(inData.get('drop1'))
       homeDropsTimes = extractTimes(homeDrops)

    if 'drop2' in inData.keys():
       awayDrops = getPenOrDrop(inData.get('drop2'))
       awayDropsTimes = extractTimes(awayDrops)

    part1 = "%s,%s,%s,%s" % (season.decode('utf-8'), poolId, matchDate, matchTime )
    part2 = "%s,%s,%s,%s,%s" % ( homeTeam, awayTeam, matchReferee, matchAttendance, matchScore)
    part3 = "%s,%s,%s,%s" % ( len(homeTries), homePenaltyTries, homeTriesTimes, homeConversions)
    part4 = "%s,%s,%s,%s" % ( len(awayTries), awayPenaltyTries, awayTriesTimes, awayConversions)
    part5 = "%s,%s,%s,%s" % ( len(homePenalties), homePenaltiesTimes, len(homeDrops), homeDropsTimes)
    part6 = "%s,%s,%s,%s" % ( len(awayPenalties), awayPenaltiesTimes, len(awayDrops), awayDropsTimes)
    outString = "%s,%s,%s,%s,%s,%s" % ( part1, part2, part3, part4, part5, part6)
    ourData.append(outString)

def loadUrls(inFile):
    for s in (line.strip() for line in open(inFile)):
        thisUrl = s.split('/', 4)[4]
        season = thisUrl.split('_',4)[0]
        # okay this is a horrible hack, if we use urllib2 unquote
        # we end up with a "long" str so just sub out the values
        # instead
        season = re.sub("%E2%80%93","-", season)
        fullUrl = "%s=%s&action=edit" % (urlbase, thisUrl)
        urls[season] = fullUrl

    return urls

def extractTimes(timeList):
    pipedTimes = ""
    for j in timeList:
        pipedTimes = "%s|%s" % ( pipedTimes, j)

    pipedTimes = re.sub("^\|","", pipedTimes)
    return(pipedTimes)

def extractSeasonData(urls):

    for season, url in urls.iteritems():
        print "Extracting Data for Season: %s:" % season

        u = urlopen(url)
        r = u.read()

        soup = BeautifulSoup(r)

        textarea = soup.find_all('textarea')[0].contents
        splitarea = re.split("\n",textarea[0])
        text = iter(splitarea)

        # this is rather horrible, but depending on the season we need to parse
        # the data in different ways... so...
        if ( season in ['2006-07', '2007-08', '2008-09', '2009-10']): 
            parseZeroNineSeasonData(season, text)
        else:
            parseSeasonData(season, text)

        # we need to add functions for 2006-07 and 2007-08
        #  2005 - 06 is missing too much data to be useful

def parseZeroNineSeasonData(season, text):
    gameCounter = 0


    for line in text:
        pool = re.match("==(=|)Pool\s+(\d+)(|=)==", line)
        if ( pool ):
            while ( gameCounter < 12 ):
                poolId = pool.group(2)
                line = next(text)
                foundMatch = re.match("\{\{rugbybox(|\s+\|)", line)

                localData = {}
                while ( foundMatch ):
                    line = next(text)
                    # and another horrible hack, if a line starts with a <!- 
                    # skip it and go to the next
                    if ( re.match("<!-", line ) ):
                        line = next(text)

                    # in the 09 - 10 season lines end with referee = <blah> }}
                    foundEnd = re.match("(\||)referee(\s+|)=(.*)(}}|)", line)
                    if ( foundEnd ):
                        foundMatch = None
                        refBasic = foundEnd.group(3)
                        localData['referee'] = refBasic
                        buildTidyData(season, poolId, localData)
                        gameCounter += 1
                    else:
                        # we have some blank referee values, we need to deal
                        # with these

                        # add these values into our structure
                        # we take the re.split as a list and do some processing
                        # here for corner casee
                        myList = re.split("=", line)
                        if ( len(myList) > 2 ):
                            # we have gotten one of these odd elments with
                            # extra strings after the date
                            myTmp = re.split("<", myList[1])
                            thisKey = myList[0]
                            thisVal = myTmp[0]
                        else:
                            thisKey = myList[0]
                            if ( len(myList) < 2 ):
                                thisVal = "NA"
                            else:
                                thisVal = myList[1]

                        thisValCheck = re.match("(.*)\s+\|", thisVal)
                        if ( thisValCheck ):
                            thisVal = thisValCheck.group(1)

                        # homescore and awayscore are all one bundle in some of the
                        # earlier pages, so we need to split them out
                        thisKey = re.match("(\||)(\s+|)(.*)(\s+|)(\||)", thisKey)
                        thisKey = re.sub("\s+", "", thisKey.group(3))

                        if ( ( thisKey == 'homescore' ) or ( thisKey == 'awayscore' ) ):
                            ( keySuffix, tries, conversions, penalties,
                                    dropgoals ) = parseZeroNineScores(thisKey, thisVal)

                            tryName = "try%s" % keySuffix
                            conName = "con%s" % keySuffix
                            penName = "pen%s" % keySuffix
                            dropName = "drop%s" % keySuffix

                            if ( tries is not None ):
                                localData[tryName] = tries
                            if ( conversions is not None ):
                                localData[conName] = conversions
                            if ( penalties is not None ):
                                localData[penName] = penalties
                            if ( dropgoals is not None ):
                                localData[dropName] = dropgoals

                        else:
                            if ( thisKey == "date" ):
                                thisDateCheck = re.match("(.*)<br />(.*)", thisVal)
                                if ( thisDateCheck ):
                                    thisVal = thisDateCheck.group(1)
                                    localData['time'] = thisDateCheck.group(2)

                        if ( thisKey == "score"):
                            thisVal = unicodedata.normalize('NFKD', thisVal).encode('utf8')
                            thisVal = re.sub("&ndash;", "-", thisVal)
                            thisScoreSplit = re.match("(\s+|)(\d+)(\s+|)(-|\\xe2\\x80\\x93)(\s+|)(\d+)(\s+|)", 
                                    thisVal)
                            thisVal = "%s-%s" % (thisScoreSplit.group(2), thisScoreSplit.group(6))

                        localData[thisKey] = thisVal

            gameCounter = 0
            pool = None

def parseZeroNineScores(key, val):
    # okay so these strings are bit all over the place, we need to 
    # firstly see if we tries in the string, if we do, lets try to

    if ( key == 'homescore' ):
        keySuffix = "1"
    else:
        keySuffix = "2"

    tryName = "try%s" % keySuffix
    conName = "con%s" % keySuffix
    penName = "pen%s" % keySuffix
    dropName = "drop%s" % keySuffix

    triesString = None
    penaltiesString = None
    conversionsString = None
    dropGoalsString = None

    # this is absolutely horrible, but it allows us to carve up 
    # the away and home scores details

    # clear out the trailing | for the 07-08 season
    val = re.sub("\|$", "", val)
    tries = re.match("(\s+|)'''(Tries|Try):'''(.*)", val)
    if ( tries ):
        # next see if we there were any conversions, if so extract those
        # of course there is another exception here, so lets try a few
        # combinations
        conversions = re.match("(.*)'''Con:'''(.*)", tries.group(3))
        if ( conversions ):
            # split out penalties, and then drop goals
            triesString = conversions.group(1)
            penalties = re.match("(.*)'''Pen:'''(.*)", conversions.group(2))
            if ( penalties ):
                # final check for drop goals
                conversionsString = penalties.group(1)
                dropgoals = re.match("(.*)'''Drop:'''(.*)", penalties.group(2))
                if ( dropgoals ):
                    penaltiesString = dropgoals.group(1)
                    dropGoalString = dropgoals.group(2)
                else:
                    penaltiesString = penalties.group(2)
        else:
            penalties = re.match("(.*)'''Pen:'''(.*)", tries.group(3))
            if ( penalties ):
                triesString = penalties.group(1)
                dropgoals = re.match("(.*)'''Drop:'''(.*)", penalties.group(2))
                if ( dropgoals ):
                    penaltiesString = dropgoals.group(1)
                    dropGoalsString = dropgoals.group(2)
                else:
                    penaltiesString = penalties.group(2)
            else:
                triesString = tries.group(2)
    else:
        # check for penalties, drop goals and so forth
        penalties = re.match("(\s+|)'''Pen:'''(.*)", val)
        if ( penalties ):
            # check for drop goals
            dropgoals = re.match("(.*)'''Drop:'''(.*)", penalties.group(2))
            if ( dropgoals ):
                penaltiesString = dropgoals.group(1)
                dropGoalsString = dropgoals.group(2)
            else:
                penaltiesString = penalties.group(1)
        else:
            # check for drop goals (and then penalties, just in case
            dropgoals = re.match("(\s+|)'''Drop:'''(.*)", val)
            if ( dropgoals ):
                penalties = re.match("(.*)'''Pen:'''(.*)", val)
                if ( penalties ):
                    dropGoalsString = penalties.group(1)
                    penaltiesString = penalties.group(2)
                else:
                    dropGoalsString = dropgoals.group(1)

    return(keySuffix, triesString, conversionsString, penaltiesString,
            dropGoalsString)


def parseSeasonData(season, text):

    gameCounter = 0
    for line in text:
        pool = re.match("===Pool\s+(\d+)===", line)
        if ( pool ):
            # okay we have a pool, so we a pool, we have 12 games too
            # extract data about
            while ( gameCounter < 12 ):

                poolId = pool.group(1)
                line = next(text)
                foundMatch = re.match("\{\{rugbybox", line)

                localData = {}
                while ( foundMatch ):
                    line = next(text)
                    # okay we now need to extract out each line, until we hit a }}
                    foundEnd = re.match("\}\}", line)
                    if ( foundEnd ):
                        foundMatch = None
                        buildTidyData(season, poolId, localData)
                        gameCounter += 1
                    else:
                        # add these values into our structure
                        # we take the re.split as a list and do some processing
                        # here for corner casee
                        myList = re.split("=", line)
                        if ( len(myList) > 2 ):
                            # we have gotten one of these odd elments with
                            # extra strings after the date
                            myTmp = re.split("<", myList[1])
                            thisKey = myList[0]
                            thisVal = myTmp[0]
                        else:
                            thisKey = myList[0]
                            thisVal = myList[1]

                        thisKey = re.match("^(\||\s+\|)(.*)\s+", thisKey)
                        thisKey = re.sub("\s+", "", thisKey.group(2))

                        # some years don't have a time aspect, its included
                        # in the date... .
                        if ( thisKey == "date" ):
                            thisDateCheck = re.match("(.*)<br />(.*)", thisVal)
                            if ( thisDateCheck ):
                                thisVal = thisDateCheck.group(1)
                                localData['time'] = thisDateCheck.group(2)

                        # scores are in a few different formats, and they get
                        # really messed up in unicode and are unusable in R
                        # we do some procesing here to avoid this
                        #
                        # to be clear this is a horrible hack...
                        #
                        if ( thisKey == "score"):
                            thisVal = unicodedata.normalize('NFKD', thisVal).encode('utf8')
                            thisVal = re.sub("&ndash;", "-", thisVal)
                            thisScoreSplit = re.match("(\s+|)(\d+)(\s+|)(-|\\xe2\\x80\\x93)(\s+|)(\d+)(\s+|)", 
                                    thisVal)
                            thisVal = "%s-%s" % (thisScoreSplit.group(2), thisScoreSplit.group(6))

                        localData[thisKey] = thisVal

            gameCounter = 0
            pool = None


urls = loadUrls(infile)
extractSeasonData(urls)

f = open("tidydata.csv", "w")
for line in ourData:
    print >>f, line.encode('utf8')
f.close()
