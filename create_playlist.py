# Before starting be sure to login Spotify and get your user id and OAuth code
# Save it to a secrets.py file!!

'''
1) Login into Youtube
2) Grab Liked Videos
3) Create a new playlist
4) Search for the song
5) Add song into new Spotify playlist
'''
#If you go to https://developer.spotify.com/console/post-playlists/ you can find a great reference for how to create a playlist using Spotify!

import json
import requests
import os #youtube api

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl

from secrets import spotify_user_id, spotify_token
from exceptions import ResponseException

class CreatePlaylist:

    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_youtube_client() #dont forget to add packages
        self.all_song_info= {}


    #1) Login into Youtube
    def get_youtube_client(self):
        # copy from youtube data api
        # disable OAuthlib HTTP verification when running locally (DO NOT LEAVE IT ENABLED WHILE IN PRODUCTION)
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        api_service_name = 'youtube'
        api_version = 'v3'
        client_secrets_file = 'client_secret.json'

        #get credentials and create API client
        scopes = ['https://www.googleapis.com/auth/youtube.readonly']
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_console()

        #from youtube Data API
        youtube_client = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

        return youtube_client

    #2) Grab Liked Videos & create a dict of important sonf info
    def get_liked_videos(self):
        #using youtube data api again!
        request = self.youtube_client.videos().list(
            part='snippet,contentDetails,statistics',
            myRating='like'
        )
        response = request.execute()

        #collect videos and important info
        #with this info we can loop and get each video item
        #then store each item in all songs information dict
        for item in response['items']:
            video_title = item['snippet']['title']
            youtube_url = 'htpps://www.youtube.com/watch?v={}'.format(item['id'])
            
            #use youtube_dl to collect the song & artist name
            #it provides us the lib with youtube url, and from this we can get songs and artists
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = video['track']
            artist = video['artist']

            #save all important info
            self.all_song_info[video_title]={
                'youtube_url':youtube_url,
                'song_name':song_name,
                'artist':artist,

                #add the uri, easy to get song to put into playlist
                'spotify_uri':self.get_spotify_uri(song_name,artist)
            }

    #3) Create a new playlist
    def create_playlist(self):
        #Add py requests lib, it allows us to make HTTP requests using Python
        #write the request body based on what you see in the spotify web-doc
        request_body = json.dumps({
            "name": "Youtube Liked Videos", #here you add the name of the playlist!
            "description": "Nice songs that I want to bingeeeeee" #if you want, you can add a description to it!
            "public": True #make it public... or not!
        })

        query = 'https://api.spotify.com/v1/users/{}/playlists'.format(spotify_user_id) #just copy+paste from the web-doc
        response = requests.post( 
            query,
            data=request_body,
            headers={
                "Content-type":"application/json",
                "Authorization":"Bearer {}".format(spotify_token)
            }
            
        )
        response_json = response.json()
        #once we send the request we want to make sure we saved the playlist ip!
        #in the future we can use this id to add specific songs to the playlist
        response_json = responde.json()

        #playlist id
        return response_json['id']

    #4) Search for the song
    def get_spotify_uri(self, song_name, artist):
        # take a look of how to search for a track using artist and song name https://developer.spotify.com/console/get-search-item/
        query = 'https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20'
            song_name,
            artist
        )
        
        response = requests.get(
            query,
            headers={
                'Content-type': "application/json",
                'Authorization': "Bearer {}".format(spotify_token)
            }
        )
        #send this info using the request lib
        response_json = response.json()
        #make sure to collect the url when sending the info, we need this for the playlist to know which specific song to add
        songs = response_json['tracks']['items']

        #only use the first song
        uri = songs[0]['uri']

        return uri

    #5) Add song into new Spotify playlist
    def add_song_to_playlist(self):
        #populate our songs dict
        self.get_liked_videos()

        #collect all of uri
        uris = []
        for song,info in self.all_song_info.items():
            uri.append(info['spotifu_uri'])
                    
        #create a new playlist
        playlist_id = self.create_playlist()

        #add all songs into new playlist
        request_data = json.dumps(uris)

        query = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(playlist_id)

        response = request.post(
            query,
            data=request_data,
            headers={
                'Content-type': 'application/json',
                'Authorization': 'Bearer {}'.format(self.spotify_token)
            }
        )
        # check for valid response status
        if response.status_code != 200:
            raise ResponseException(response.status_code)

        response_json = response.json()
        return response_json


if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()

