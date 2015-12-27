#!/usr/bin/python2.4

'''Post a message to twitter'''

__author__ = 'ericbudd@gmail.com'



import tweepy
import csv
import inputapi
from datetime import datetime


USAGE = '''Usage: tweet [options] message

  This script posts a message to Twitter.

  Options:

    -h --help : print this help
    --consumer-key : the twitter consumer key
    --consumer-secret : the twitter consumer secret
    --access-key : the twitter access token key
    --access-secret : the twitter access token secret
    --encoding : the character set encoding used in input strings, e.g. "utf-8". [optional]

  Documentation:

  If either of the command line flags are not present, the environment
  variables TWEETUSERNAME and TWEETPASSWORD will then be checked for your
  consumer_key or consumer_secret, respectively.

  If neither the command line flags nor the enviroment variables are
  present, the .tweetrc file, if it exists, can be used to set the
  default consumer_key and consumer_secret.  The file should contain the
  following three lines, replacing *consumer_key* with your consumer key, and
  *consumer_secret* with your consumer secret:

  A skeletal .tweetrc file:

    [Tweet]
    consumer_key: *consumer_key*
    consumer_secret: *consumer_password*
    access_key: *access_key*
    access_secret: *access_password*

'''

api = 0

timelineOut = csv.writer(open('timelineOut.csv','w'))
linksOut = csv.writer(open('linksOut.csv','w'))

class bunch:
    def __init__(self, **kwds):
      self.__dict__.update(kwds)

def isoparse(s):
    try:
        return datetime(int(s[0:4]),int(s[6:7]),int(s[9:10]),
                        int(s[11:13]), int(s[14:16]), int(s[17:19]))
    except:
        return None


def setAuth():
  auth = tweepy.OAuthHandler(inputapi.consumer_key, inputapi.consumer_secret)
  auth.set_access_token(inputapi.access_token, inputapi.access_token_secret)

  api = tweepy.API(auth)

  return api

def inputFilterFile():
  filter = csv.reader(open('filterTerms.csv'))

  #listFilter = []

  listFilter = next(filter)
  print("list" + str(listFilter))

  #print (listFilter[len(listFilter)-1], len(listFilter))

  #for i in range(len(listFilter)):
  #    print listFilter[i]

  return listFilter

def getStatuses(api):
  #for use with max_id
  lastID = None
  statuses = []

  for page in range(1,2):
      print (page)
      '''
      statuses = api.GetHomeTimeline(
                    count=10,
                    since_id=None,
                    max_id=lastID,
                    trim_user=False,
                    exclude_replies=False,
                    contributor_details=False,
                    include_entities=True)
      '''
      tempStatuses = api.list_timeline(
                    list_id=None,
                    count=200,
                    since_id=None,
                    max_id=lastID,
                    slug="mega-list",
                    owner_id=None,
                    owner_screen_name="ericmbudd",
                    include_entities=True)

      for s in range(0,len(tempStatuses)):
         statuses.append(tempStatuses[s])

      lastID = tempStatuses.max_id    #  statuses[len(statuses) -1].id


  print ([(s.text,s.user.screen_name) for s in statuses])

  return statuses

def filterTimeline(listFilter, statuses, timelineSummary):
  timeline = bunch(date=0, screenName=0, text=0, filteredText=0, filteredTerm=0, linkContained = 0)

  print (len(listFilter))

  # cycle through each status update pulled from twitter to filter
  for s in statuses:

      # clean text: lowercase, convert to bytes for searching, replace line breaks with space
      asciiText = s.text.encode('UTF-8', 'ignore')
      asciiTextLower = asciiText.lower()
      textString = str(asciiTextLower, encoding='UTF-8')
      textBytes = bytes(textString,encoding='utf-8')
      timeline.text = textString.replace('\n', ' ')

      # accumulator for total length of tweets
      timelineSummary.allTweetsTotalCharacters += len(textBytes)

      # put into data structure
      timeline.date = s.created_at
      timeline.screenName = s.user.screen_name

      # set up booleans for output
      timeline.filteredTerm = 'false'
      timeline.linkContained = 'false'
      timeline.filteredText = ''

      for i in range(len(listFilter)):
          asciiFilter = listFilter[i]

          # convert to unicode
          try:
            asciiFilter = asciiFilter.encode('ascii', 'ignore')

          # handle unicode conversion errors
          except UnicodeDecodeError:
            continue

          # clean filter terms text
          asciiFilter = asciiFilter.strip()
          asciiFilterLower = asciiFilter.lower()
          filterString =str(asciiFilterLower, encoding='UTF-8')
          filterByte = bytes(filterString,encoding='utf-8')

          # check to see if filtered word is in string. -1 = not found, 0 = a hack because b' exists in 0 position
          if textBytes.find(filterByte) != -1 and textBytes.find(filterByte) != 0:
             # print(filterByte)
             # print(textBytes)
              timeline.filteredText = str(filterByte,encoding='utf-8')
              print (timeline.filteredText)
              timeline.filteredTerm = 'true'
              timelineSummary.filteredTweetCount += 1
              # accumulator for total length of filtered tweets
              timelineSummary.filteredTweetsTotalCharacters += len(textBytes)

              # break because additional keywords may be counted as filtered terms after first term
              # future enhancement - don't count additional keywords, but add semi-colon separated?r
              break


      #broken in python 3? need to con
      if asciiTextLower.find(bytes('http://',encoding='utf8')) != -1:
          timeline.linkContained = 'true'

      #newText2 = newText.encode( "utf-8" )
      dataOut = timeline.date, timeline.screenName ,timeline.text,timeline.filteredText,timeline.filteredTerm, timeline.linkContained
      timelineOut.writerow(dataOut)

      if timeline.linkContained == 'true':
          linksOut.writerow(dataOut)

  return timelineSummary


def summaryStats(statuses, timelineSummary):
  maxTime = statuses[0].created_at
  minTime = statuses[len(statuses)-1].created_at
  tweetCount = len(statuses)
  timeDelta = maxTime - minTime
  TPM = round (60 * tweetCount / timeDelta.total_seconds(),3)
  fTPM = round (60 * ( tweetCount - timelineSummary.filteredTweetCount ) / timeDelta.total_seconds(),3)
  ATTCPT = round(timelineSummary.allTweetsTotalCharacters / tweetCount,3)
  FTTCPT = round(timelineSummary.filteredTweetsTotalCharacters / timelineSummary.filteredTweetCount,3)



  print (" ")
  print (timeDelta, timeDelta.total_seconds(), tweetCount, timelineSummary.filteredTweetCount, TPM, fTPM, ATTCPT, FTTCPT)

def main():
  startTime = datetime.now()
  api = setAuth()
  timelineSummary = bunch( filteredTweetCount = 0, allTweetsTotalCharacters = 0, filteredTweetsTotalCharacters = 0 )

  listFilter = inputFilterFile()
  statuses = getStatuses(api)

  timelineSummary = filterTimeline(listFilter, statuses, timelineSummary)

  summaryStats(statuses, timelineSummary)

  endTime = datetime.now()

  runTime = endTime - startTime

  print(runTime.total_seconds() )

  #print [s.favorited for s in statuses]


#   except UnicodeDecodeError:
 #    print "Your message could not be encoded.  Perhaps it contains non-ASCII characters? "
 #    print "Try explicitly specifying the encoding with the --encoding flag"
 #    sys.exit(2)
  #print "%s just posted: %s" % (status.user.name, status.text)

if __name__ == "__main__":
  main()
