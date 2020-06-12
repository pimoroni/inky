import urllib.request
import json
from datetime import datetime, timedelta

lastfm_public_key = "079a7d64ea52c358ad4f0afbe2f900b3"

def static_data(lastfm_username, json_field):
    # build URL
    url = "http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user=" + lastfm_username + "&api_key=" + lastfm_public_key + "&format=json"

    # download the raw json object and parse the json data
    data = urllib.request.urlopen(url).read().decode()
    obj = json.loads(data)

    # extract relevant data
    output = obj['user'][json_field]

    return output

def playcount(lastfm_username, period):
    # build URL
    url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=" + lastfm_username + "&api_key=" + lastfm_public_key

    # work out the time now
    start_time = None
    time_now = datetime.now()

    # if passed an appropriate time period argument, then set time period
    if period == "today":
        start_time = time_now.replace(hour=0, minute=0)

    if period == "this_month":
        start_time = time_now.replace(day=1, hour=0, minute=0)
    
    if period == "this_year":
        start_time = time_now.replace(month=1, day=1, hour=0, minute=0)
    
    if period == "this_week":
        start_time = time_now.replace(hour=0, minute=0)
        start_time = start_time - timedelta(days=start_time.weekday())

    if period == "last30days":
        start_time = time_now.replace(hour=0, minute=0)
        start_time = start_time - timedelta(days=30)
    
    if period == "last7days":
        start_time = time_now.replace(hour=0, minute=0)
        start_time = start_time - timedelta(days=7)

    if period == "last24hours":
        start_time = time_now - timedelta(hours=24)
    
    if period == "last_hour":
        start_time = time_now - timedelta(hours=1)

    # if start_time has been set then append it to the url
    if start_time is not None:
        start_timestamp = datetime.timestamp(start_time)

        # convert to integer
        start_timestamp = int(start_timestamp)

        url = url + "&from=" + str(start_timestamp)

    # add the specification that it should come back in JSON
    url = url + "&format=json"
    
    # download the raw json object and parse the json data
    data = urllib.request.urlopen(url).read().decode()
    obj = json.loads(data)

    # extract relevant data
    output = obj['recenttracks']['@attr']['total']

    return output

def lastplayed(lastfm_username):
    # build URL
    url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=" + lastfm_username + "&api_key=" + lastfm_public_key + "&format=json"

    # download the raw json object and parse the json data
    data = urllib.request.urlopen(url).read().decode()
    obj = json.loads(data)

    # extract relevant data
    lastplayed_trackname = obj['recenttracks']['track'][0]['name']
    lastplayed_artist = obj['recenttracks']['track'][0]['artist']['#text']
    lastplayed_album = obj['recenttracks']['track'][0]['album']['#text']
    lastplayed_image_url = obj['recenttracks']['track'][0]['image'][3]['#text']

    #output = lastplayed_trackname + " by " + lastplayed_artist + " from the album " + lastplayed_album

    return lastplayed_trackname, lastplayed_artist, lastplayed_album, lastplayed_image_url