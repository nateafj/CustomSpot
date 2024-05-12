import json

file = open('/Users/nathanielford/PycharmProjects/pythonProject1/playlists.json')

playlists = json.load(file)

print(playlists)

headers = {
            'Authorization': f"Bearer {session['access_token']}"
        }
        response = requests.get(API_BASE_URL + 'playlists/' + input_playlist_uri + '/tracks' +
                                f"?offset={str(offset)}", headers=headers)
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
























