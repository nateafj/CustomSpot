import os
import json
import urllib.parse, requests
from datetime import datetime
from flask import Flask, redirect, request, jsonify, session

app = Flask(__name__)

app.secret_key = '3glob4-4w4f5h-5gets-h6ht6'

CLIENT_ID = os.getenv('CID')
CLIENT_SECRET = os.getenv('CSEC')
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

# INITIALIZE GLOBAL ARRAYS
playlist_uris = []
playlist_names_and_tracktotals = []
track_uris = []
duplicate_track_uris = []
playlist_objects = []
saved_tracks = []
not_in_saved = []
detected_playlists = []


@app.route('/')
def index():
    return "CustomSpot App <a href='/login'>login</a>"


@app.route('/login')
def login():
    scope = 'user-read-private user-read-email playlist-read-private user-library-read user-library-modify'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)


@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']
        print(session['access_token'])
        return redirect('/playlists')


@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    offset = 0
    limit = 50
    print('yo!')
    headers = {
        'Authorization': f"Bearer {session['access_token']}",
    }
    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    print(response.headers)
    playlists = response.json()
    print(playlists.keys())
    print(playlists)
    # initialize an enhanced loop to comb through the playlist uri's we shouldn't need any duplicate verification
    # because playlists should never have the same id but refreshing causes duplicates to enter the array
    playlist_return_limit = 50
    playlist_counter = 0
    print(playlists['total'])
    # PLAYLISTS TOTAL OVER RETURN LIMIT START
    for item in playlists['items']:
        print(item)
        if str(item) == 'None':
            continue
        current_playlist_object = {}
        # checking the type of uri to ensure we don't grab user uri's
        if item['owner']['display_name'] != 'n8' and item['description'] != 'Curated with AI':
            print('____________________________')
            print("playlist not owned by _name_ or made by AI")
            print(item['owner']['display_name'])
            continue
        current_playlist_object["name"] = item['name']
        current_playlist_object["uri"] = item['uri'].split(':')[-1]
        current_playlist_object["total"] = item['tracks']['total']
        current_playlist_object['snapshot_id'] = item['snapshot_id']
        current_playlist_object['songs'] = []
        print(current_playlist_object)
        playlist_uri = item['uri'].split(':')[-1]
        if playlist_uri in playlist_uris:
            continue
        # To prevent the duplicates ids from being added from refreshing
        playlist_objects.append(current_playlist_object)
        playlist_uris.append(playlist_uri)
        playlist_counter += 1
        print('playlists added:' + str(playlist_counter))
    while len(playlists['items']) > 0:
        offset += limit
        response = requests.get(API_BASE_URL + 'me/playlists' + f'?offset={offset}', headers=headers)
        playlists = response.json()
        for item in playlists['items']:
            if str(item) == 'None':
                continue
            current_playlist_object = {}
            # checking the type of uri to ensure we don't grab user uri's
            if item['owner']['display_name'] != 'n8' and item['description'] != 'Curated with AI':
                print("playlist not owned by _name_")
                print(item['owner']['display_name'])
                print('____________________________')
                continue
            current_playlist_object["name"] = item['name']
            current_playlist_object["uri"] = item['uri'].split(':')[-1]
            current_playlist_object["total"] = item['tracks']['total']
            current_playlist_object['songs'] = []
            print(current_playlist_object)
            playlist_uri = item['uri'].split(':')[-1]
            if playlist_uri in playlist_uris:
                continue
            # to prevent the duplicates ids from being added from refreshing
            playlist_objects.append(current_playlist_object)
            playlist_uris.append(playlist_uri)
            playlist_counter += 1
            print('playlists added:' + str(playlist_counter))
            print('____________________________')
    # PLAYLISTS TOTAL OVER RETURN LIMIT END
    return playlist_objects


@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return "CustomSpot App <a href='/playlists'>playlists</a><a href='/tracks'>tracks</a>"


@app.route('/tracks')
def get_track():
    limit = 100
    track_counter = 0
    duplicate_counter = 0
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    for uri in playlist_uris:
        offset = 0
        response = requests.get(API_BASE_URL + 'playlists/' + uri + '/tracks' + "?offset=0",
                                headers=headers)
        tracks = response.json()
        print(tracks.keys())
        print('there are: ' + str(tracks['total']) + ' songs in the playlist ')
        for item in tracks['items']:
            if item['track']['type'] == 'track':
                print(item['track']['name'])
                track_uri = item['track']['uri'].split(':')[-1]
                if track_uri in track_uris:
                    duplicate_track_uris.append(track_uri)
                    duplicate_counter += 1
                    continue
                track_uris.append(track_uri)
                track_counter += 1
        print('songs added:' + str(track_counter))
        while len(tracks['items']) > 0:
            offset += limit
            print(offset)
            response = requests.get(API_BASE_URL + 'playlists/' + uri + '/tracks' + f"?offset={str(offset)}",
                                    headers=headers)
            tracks = response.json()
            print('current page of tracks has ' + str(len(tracks['items'])) + ' songs')
            for paginated_page_item in tracks['items']:
                # checking the type of uri to ensure we don't grab user uri's
                if paginated_page_item['track']['type'] == 'track':
                    track_uri = paginated_page_item['track']['uri'].split(':')[-1]
                    if track_uri in track_uris:
                        duplicate_track_uris.append(track_uri)
                        duplicate_counter += 1
                        continue
                    track_uris.append(track_uri)
                    track_counter += 1
                    print('songs added: ' + str(track_counter))

    print(str(duplicate_counter) + ' duplicate tracks: ' + str(duplicate_track_uris))
    print('total songs: ' + str(track_counter))
    return track_uris


@app.route('/users-tracks')
def get_users_saved_tracks():
    count = 0
    limit = 50
    offset = 0
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    saved_tracksDump = requests.get(API_BASE_URL + 'me/tracks' + f"?limit={str(limit)}", headers=headers)
    saved_tracksJson = saved_tracksDump.json()
    for item in saved_tracksJson['items']:
        track_object = {"name": item['track']['name'], 'uri': item['track']['uri'].split(':')[-1]}
        saved_tracks.append(item['track']['uri'].split(':')[-1])
        print(track_object)
        count += 1
    while len(saved_tracksJson['items']) > 0:
        headers = {
            'Authorization': f"Bearer {session['access_token']}"
        }
        offset += limit
        saved_tracksDump = requests.get(API_BASE_URL + 'me/tracks' + f"?offset={str(offset)}&limit={str(limit)}",
                                        headers=headers)
        saved_tracksJson = saved_tracksDump.json()
        for item in saved_tracksJson['items']:
            track_object = {"name": item['track']['name'], 'uri': item['track']['uri'].split(':')[-1]}
            saved_tracks.append(item['track']['uri'].split(':')[-1])
            print(track_object)
            count += 1
        print(count)
    return saved_tracks


@app.route('/compare')
def compare_tracks():
    count = 0
    for track in track_uris:
        if track not in saved_tracks:
            print(track)
            not_in_saved.append(track)
            count += 1
    print(count)
    return not_in_saved


@app.route('/add-songs')
def add_songs():
    increment = 50
    sindex = 0
    count = 0
    eindex = 50

    print('not saved : ' + str(len(not_in_saved)))

    while eindex != len(not_in_saved) + 1:
        post_tracks = {'ids': []}
        for track in not_in_saved[sindex:eindex]:
            post_tracks['ids'].append(track)
            count += 1
        if eindex == len(not_in_saved):
            eindex += 1
            break
        #     send post request with 'post_tracks' as the body
        headers = {
            'Authorization': f"Bearer {session['access_token']}"
        }
        data = json.dumps(post_tracks).encode('utf-8')
        res = requests.put(API_BASE_URL + 'me/tracks', data=data, headers=headers)
        print(res.status_code)
        if eindex == len(not_in_saved) + 1:
            break
        print(post_tracks)
        sindex += increment
        eindex += increment
        if eindex > len(not_in_saved):
            eindex = len(not_in_saved)
    print(count)
    return post_tracks


@app.route('/info_dump')
def info_dump():
    limit = 100
    offset = 0
    track_counter = 0
    newCounter = 0
    duplicate_counter = 0
    tracklist = []

    print('what would you like to do')
    print('1: get playlist info')
    print('2: get track info')

    x = input()
    if x == '1':
        print("playlist info")
        input_playlist_uri = input()
        headers = {
            'Authorization': f"Bearer {session['access_token']}"
        }
        response = requests.get(API_BASE_URL + 'playlists/' + input_playlist_uri + '/tracks', headers=headers)
        tracks = response.json()

        print(tracks.keys())
        # pseudo try catch block
        if 'error' in request.args:
            return jsonify({"error": request.args['error']})
        if len(tracks['items']) == int(tracks['total']):
            print("PASS: the number of tracks found and and the number reported match")
            print('there are: ' + str(len(tracks['items'])) + ' songs in the playlist')
            print('amount of items in the  actual response: ' + str(len(tracks['items'])))
            print('The total key reports: ' + str(tracks['total']))
        else:
            print('ERROR: the number tracks found and number reported dont match')
            print('amount of items in the  actual response: ' + str(len(tracks['items'])))
            print('The total key reports: ' + str(tracks['total']))

        #         # if len(tracks['items']) == 0:
        #         #     continue
        for item in tracks['items']:
            if item['track']['type'] == 'track':
                track_uri = item['track']['uri'].split(':')[-1]
                if track_uri in tracklist:
                    duplicate_counter += 1
                    # continue
                tracklist.append(track_uri)
                track_counter += 1
        print('songs added:' + str(track_counter))
        while len(tracks['items']) > 0:
            offset += limit
            print('offset is: ' + str(offset))
            response = requests.get(
                API_BASE_URL + 'playlists/' + input_playlist_uri + '/tracks' + f"?offset={str(offset)}",
                headers=headers)
            tracks = response.json()
            for paginatedItem in tracks['items']:
                #              checking the type of uri to ensure we don't grab user uri's
                if paginatedItem['track']['type'] == 'track':
                    track_uri = paginatedItem['track']['uri'].split(':')[-1]
                    if track_uri in tracklist:
                        duplicate_counter += 1
                        # continue
                    tracklist.append(track_uri)
                    newCounter += 1
                    print('paginated songs added:' + str(newCounter))
        total = track_counter + newCounter
        print('total songs reported: ' + str(total))
        print('total # of duplicates found: ' + str(duplicate_counter))

        return tracklist
    return "ello govna!"


@app.route('/playlist_builder')
def build_playlist():
    limit = 100
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    for playlist in playlist_objects:
        track_counter = 0
        offset = 0
        response = requests.get(API_BASE_URL + 'playlists/' + playlist['uri'] + '/tracks' + "?offset=0",
                                headers=headers)
        playlist_tracks = response.json()
        print(playlist['name'])
        for item in playlist_tracks['items']:
            dupe = 0
            track_object = {}
            if item['track']['type'] == 'track':
                print(item['track']['name'])
                track_object['name'] = item['track']['name']
                track_object['uri'] = item['track']['uri'].split(':')[-1]
                for song in playlist.get('songs', []):
                    if track_object['uri'] == song['uri']:
                        dupe = 1
                if dupe == 1:
                    continue
                playlist['songs'].append(track_object)
                track_counter += 1
        while len(playlist_tracks['items']) > 0:
            offset += limit
            response = requests.get(
                API_BASE_URL + 'playlists/' + playlist['uri'] + '/tracks' + f"?offset={str(offset)}",
                headers=headers)
            playlist_tracks = response.json()
            for paginated_page_track in playlist_tracks['items']:
                dupe = 0
                track_object = {}
                if paginated_page_track['track']['type'] == 'track':
                    print(paginated_page_track['track']['name'])
                    track_object['name'] = paginated_page_track['track']['name']
                    track_object['uri'] = paginated_page_track['track']['uri'].split(':')[-1]
                    for song in playlist.get('songs', []):
                        if track_object['uri'] == song['uri']:
                            dupe = 1
                    if dupe == 1:
                        continue
                    playlist['songs'].append(track_object)
                    track_counter += 1
        print('total songs actually added ' + str(track_counter))
    return playlist_objects


@app.route('/find_ps_song')
def find_ps_song():
    target_track_uri = input('what song would you like to remove?')
    print(target_track_uri)
    for playlist in playlist_objects:
        current_playlist = {}
        for song in playlist.get('songs', []):
            if target_track_uri == song['uri']:
                current_playlist['name'] = playlist['name']
                current_playlist['uri'] = playlist['uri']
                current_playlist['snapshot_id'] = playlist['snapshot_id']
                detected_playlists.append(current_playlist)
                print('here!')
    return detected_playlists

# @app.route('/remove_songs')
# def remove_songs():
#     headers = {
#
#     }
#     for playlist in detected_playlists:
#
#


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
