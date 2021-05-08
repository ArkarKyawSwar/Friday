"""
This is a simple voice assistant program named "Friday".
It can assist the user with Google Calendar, Notepad, and Spotify.
See guide.txt for more details.
"""
from __future__ import print_function
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
from httplib2 import URI
import speech_recognition as sr
import pyttsx3
import pytz
import subprocess
import json
import spotipy 
from spotipy.oauth2 import SpotifyOAuth

class InvalidSearchError(Exception):
    pass


WAKE_UP = "friday"

OPEN_CALENDAR = ["calendar", "do i have", "am i busy", "am i free", "do i have plans", "show me my plans", "how's my schedule", "what's my schedule"]
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
ORDINAL_DATES = ["st", "nd", "rd", "th"]
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

OPEN_NOTEPAD = ["make a note", "create a note", "write this down", "open notepad"]

PLAY_SPOTIFY = ["spotify track", "spotify album", "spotify artist", "spotify pause", "spotify play", "spotify next", "spotify previous"]


def speak(text: str):
    """
    :param text: String for Friday to speak
    """
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.say(text)
    engine.runAndWait()

def getAudio() -> str:
    """
    :return: String that the user said to Friday
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source = source)
        audio = recognizer.listen(source)
        speech = ""

        try: 
            speech = recognizer.recognize_google(audio)
            print(speech)
        except Exception as error:
            print(error)
    return speech.lower()


#Functions for google calender
def googleCalendarAuthentication():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service

def getEvents(service, date):
    # Call the Calendar API
    
    startDate = datetime.datetime.combine(date, datetime.datetime.min.time())
    endDate = datetime.datetime.combine(date, datetime.datetime.max.time())
    utc = pytz.UTC
    startDate = startDate.astimezone(utc)
    endDate = endDate.astimezone(utc)

    events_result = service.events().list(calendarId='primary', timeMin=startDate.isoformat(),
                                        timeMax = endDate.isoformat(), singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak("You have {} events.".format(len(events)))
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            startTime = str(start.split("T")[1].split("-")[0])
            startHour = int(startTime.split(":")[0])

            if startHour < 12: 
                startTime = startTime + "am"
            else:
                startTime = str(int(startTime.split(":")[0]) - 12)
                startTime = startTime + "pm"
            
            speak(event["summary"] + " at " + startTime)

def getDate(text: str) -> datetime.date:
    """
    :param text: String that the user said to Friday
    :return: Date that the user wants to access Google Calendar on
    """
    text = text.lower()
    today = datetime.date.today()

    if text.count("today") > 0:
        return today

    date = -1
    day = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day = DAYS.index(word) + 1
        elif word.isdigit():
            date = int(word)
        else:
            for i in ORDINAL_DATES:
                found = word.find(i)
                if found > 0:
                    try:
                        date = int(word[:found])
                    except:
                        pass

    if month < today.month and month != -1:
        year = year + 1

    if date < today.day and month == -1 and date != -1:
        month = month + 1

    if month == -1 and date == -1 and day != -1:
        currentDay = today.weekday() # 0-6
        difference = day - currentDay

        if difference < 0:
            difference += 7
            if text.count("next") >= 1:
                difference += 7
        return today + datetime.timedelta(difference)
    if month == -1 or date == -1:
        return None
    return datetime.date(month = month, day = date, year = year)

#Functions for Notepad
def note(text):
    """
    :param: Text to be written in Notepad
    """
    date_time = datetime.datetime.now()
    fileName = "note-on-" + str(date_time).replace(":", "-") + ".txt"
    with open(fileName, "w") as note:
        note.write(text)
    notepad = "C:\WINDOWS\system32\\notepad.exe"
    subprocess.Popen([notepad, fileName])

#Functions for Spotify
def createSpotifyOAuth() -> spotipy.SpotifyOAuth:
    """
    :return: SpotifyOAuth to authorize Spotify account
    """
    with open ("spotifycredentials.json", "r") as jFile:
        creds = json.load(jFile)

    return spotipy.SpotifyOAuth(
            client_id= creds["client_id"],
            client_secret= creds["client_secret"],
            redirect_uri=creds["redirect_uri"],
            scope=creds["scope"],
            username=creds["username"])

def authorizeSpotify() -> spotipy.Spotify:
    """
    :return: Spotify object to give Spotify commands with
    """
    oauth_obj = createSpotifyOAuth()
    token = oauth_obj.get_cached_token()
    access_token = token["access_token"]
    spotify_obj = spotipy.Spotify(auth = access_token)
    return spotify_obj

def getDeviceID(spotify: spotipy.Spotify) -> str:
    """
    :param: Spotify object to search the current(or desired) device to be played from
    :return: String of the current(or desired) device's ID
    """
    with open ("spotifycredentials.json", "r") as jFile:
        creds = json.load(jFile)

    devices = spotify.devices()
    deviceID = None
    for d in devices['devices']:
        d['name'] = d['name'].replace('’', '\'')
        if d['name'] == creds["device_name"]:
            deviceID = d['id']
            break
    return deviceID

def getAlbumURI(spotify: spotipy.Spotify, album_name: str) -> str:
    """
    :param spotify: Spotify object to search the album 
    :param ablum_name: Album name
    :return: Album's uri
    """
    album_name = album_name.replace(' ', '+')

    album_info = spotify.search(q=album_name, limit=1, type='album')

    if not album_info['albums']['items']:
        raise InvalidSearchError("There is no album with such name.")
    album_uri = album_info['albums']['items'][0]['uri']
    return album_uri

def getArtistURI(spotify: spotipy.Spotify, artist_name: str) -> str:
    """
    :param spotify: Spotify object to search the artist 
    :param artist_name: Artist name
    :return: Artist's uri
    """
    artist_name = artist_name.replace(' ', '+')

    artist_info = spotify.search(q=artist_name, limit=1, type='artist')

    if not artist_info['artists']['items']:
        raise InvalidSearchError("There is no artist with such name.")
    artist_uri = artist_info['artists']['items'][0]['uri']
    return artist_uri

def getTrackURI(spotify: spotipy.Spotify, track_name: str) -> str:
    """
    :param spotify: Spotify object to search the track 
    :param track_name: Track name
    :return: Track's uri
    """
    track_name = track_name.replace(' ', '+')

    track_info = spotify.search(q=track_name, limit=1, type='track')

    if not track_info['tracks']['items']:
        raise InvalidSearchError("There is no track with such name.")
    track_uri = track_info['tracks']['items'][0]['uri']
    return track_uri

def playAlbum(spotify=None, device_id=None, uri=None):
    spotify.start_playback(device_id=device_id, context_uri=uri)

def playArtist(spotify=None, device_id=None, uri=None):
    spotify.start_playback(device_id=device_id, context_uri=uri)

def playTrack(spotify=None, device_id=None, uri=None):
    spotify.start_playback(device_id=device_id, uris=[uri])
