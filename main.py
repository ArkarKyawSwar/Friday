from friday import *

#Google calender authentication
calendarService = googleCalendarAuthentication()

#Spotify authorization and selecting device to play from
spotify = authorizeSpotify()
device_id = getDeviceID(spotify)

while True:
    print("Listening")
    text = getAudio()
    if text.count(WAKE_UP) > 0:
        speak("i am listening")
        text = getAudio()

        
        if len(text) > 0:
            #Calendar
            for phrase in OPEN_CALENDAR:
                if phrase in text:
                    date = getDate(text)
                    if date:
                        getEvents(calendarService, getDate(text))
                    else:
                        speak("I'm not sure I understand.")
            
            #Notepad
            for phrase in OPEN_NOTEPAD:
                if phrase in text:
                    speak("What would you like me to take a note of?")
                    toWrite = getAudio()
                    note(toWrite)
                    speak("I've made the note you wanted.")

            #Spotify
            if "spotify" in text:
                while text != "spotify quit":
                    if PLAY_SPOTIFY[0] in text:
                        words = text.split()
                        track_name = ' '.join(words[2:])
                        uri = getTrackURI(spotify, track_name)
                        playTrack(spotify, device_id, uri)
                    
                    elif PLAY_SPOTIFY[1] in text:
                        words = text.split()
                        album_name = ' '.join(words[2:])
                        uri = getAlbumURI(spotify, album_name)
                        playAlbum(spotify, device_id, uri)

                    elif PLAY_SPOTIFY[2] in text:
                        words = text.split()
                        artist_name = ' '.join(words[2:])
                        uri = getArtistURI(spotify, artist_name)
                        playArtist(spotify, device_id, uri)
                    
                    elif PLAY_SPOTIFY[3] in text:
                        spotify.pause_playback(device_id)
                    
                    if PLAY_SPOTIFY[4] in text:
                        spotify.start_playback(device_id)
                    
                    elif PLAY_SPOTIFY[5] in text:
                        spotify.next_track(device_id)

                    elif PLAY_SPOTIFY[6] in text:
                        spotify.previous_track(device_id)
                    
                    print("Spotify listening")
                    text = getAudio()
        else:
            speak("I'm not sure I understand.")