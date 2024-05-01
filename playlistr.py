import os
import base64
import requests
import secrets
import hashlib
import re
from dotenv import load_dotenv, find_dotenv 
from nltk.stem import PorterStemmer

#GLOBAL VARIABLES
load_dotenv(find_dotenv())
redirect_uri = 'http://localhost:8080/'



def generate_code_verifier_and_challenge():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '')
    return code_verifier, code_challenge


def authorization_link(client_id, code_challenge, redirect_uri=redirect_uri):

    #redirect_uri = 'http://127.0.0.1:8050/'
    scope = 'playlist-modify-private%20playlist-modify-public%20ugc-image-upload'  # "Space"-separated list of scopes

    auth_url = "https://accounts.spotify.com/authorize?"\
                + f"client_id={client_id}"\
                + "&response_type=code"\
                + f"&redirect_uri={redirect_uri}"\
                + f"&scope={scope}"\
                + f"&code_challenge_method=S256&code_challenge={code_challenge}"
    
    return auth_url

def obtain_pkce_token(client_id, authorization_code, code_verifier, redirect_uri=redirect_uri):

    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    #redirect_uri = "http://127.0.0.1:8050/" # move this to a global variable
    data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    pkce_token_json = requests.post(token_url, headers=headers, data=data).json()
    return pkce_token_json


def grantaccess_tokenretreive(client_id):
    
    code_verifier, code_challenge = generate_code_verifier_and_challenge()

    auth_url = authorization_link(client_id, code_challenge)

    print(f"Please go to this URL and allow access, copy the page that opens:\n{auth_url}")
    authorization_code = input("Paste the url you were redirected to:\n")
    if authorization_code == "":
        raise ValueError("Error: No authorization code provided. Please try again.")
    authorization_code = re.sub("^.*code=","",authorization_code)
    
    pkce_token_json = obtain_pkce_token(client_id, authorization_code, code_verifier)
    
    
    try:
        pkce_token = pkce_token_json['access_token']
    except:
        ValueError("Error: Something went wrong with the token retieval: \n", pkce_token_json)


    return pkce_token  # This contains the access token and refresh token


def get_search_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_headers = {'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode()).decode()}
    auth_data = {'grant_type': 'client_credentials'}

    response = requests.post(auth_url, headers=auth_headers, data=auth_data)
    
    if (response.status_code == 200) & (response.json()['access_token'] != None):
        token = response.json()['access_token']
        return token
    else:
        ValueError("Error: Something went wrong", response.text)


def get_user_info(token):
    response = requests.get("https://api.spotify.com/v1/me", headers={"Authorization": f"Bearer {token}"})
    return response.json()


def get_text():
    query = input("Enter song name: ")
    return query


def return_song(response):
    if response.status_code != 200:
        print(response.text)
        raise ValueError(response.status_code)
    else:
        return response.json()

    
def match_phrase(url, headers, query, search_rounds=10, debug=False):
    response = requests.get(url, headers=headers)
    returned_songs = return_song(response) 
    

    stemmer = PorterStemmer()
    stem_stored = None

    if returned_songs["tracks"]["total"] == 0:
        print("no matching results for ", query)
        return None

    i = 0
    query_token = re.sub("[^a-zA-Z0-9 ]", "", query).strip().lower()
    query_stem = ' '.join([stemmer.stem(word) for word in query_token.split()])
    while i <= search_rounds:
            
        for track in returned_songs["tracks"]["items"]:
            track_token = re.sub("[^a-zA-z0-9 ]","", track["name"]).strip().lower()
            track_stem = ' '.join([stemmer.stem(word) for word in track_token.split()])

            if track_token == query_token:
                return track
            elif track_stem == query_stem:
                stem_stored = track
            elif i == search_rounds:
                return None

        try:
            returned_songs = return_song(requests.get(returned_songs["tracks"]["next"], headers=headers), query)            
        except:
            return None
        
        i += 1
    
    if stem_stored:
        print("No exact match found. Using stem match")
        print("Stem match found: ", stem_stored["name"])
        return stem_stored


def search_songs(search_words, token, spotify_search_limit, lookforward, debug=False):
    '''
    Ideally this should start with a range of 1 word and expand each pass. (cut off? to prevent full search)
    '''
    matching_tracks = {}
    for i in range(len(search_words)):

        end_idx = i+lookforward if i+lookforward < len(search_words) else len(search_words)

        while end_idx > i:
            search_phrase = " ".join(search_words[i:end_idx])

            url = "https://api.spotify.com/v1/search?q={"\
                +search_phrase\
                +"}&market=US&type=track&limit="\
                +str(spotify_search_limit)
            
            headers = {"Authorization": "Bearer "+token,}

            found_track = match_phrase(url, headers, search_phrase)

            try:
                matching_tracks[(i,end_idx)] = [search_phrase, \
                                            found_track["name"], \
                                            found_track['uri'], \
                                            found_track["artists"][0]["name"]
                                        ]
            except:
                matching_tracks[(i,end_idx)] = None
            if debug:
                print(f"at {i}, {end_idx}",matching_tracks[(i,end_idx)])
            end_idx -= 1
    
    return matching_tracks


def recursive_chain(possible_list, end_node, start_node = 0):
    edges_to_assess = [edge for edge in possible_list if edge[0] == start_node]
    if edges_to_assess == []:
        return [("terminated at", start_node)]
    for edge in edges_to_assess:
        if edge[1] == end_node:
            return [edge]
        next_step = recursive_chain(possible_list, end_node, start_node=edge[1])
        if next_step[0][0] == "terminated at":
            return next_step 
        try:
            next_step.insert(0,edge)
            return next_step
        except:
            pass


def create_playlist(user_id, name, description, token, public=False, collaborative=False):
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"}
    body = {"name": name, 
            "description": description, 
            "public": public, 
            "collaborative": collaborative
            }
    response = requests.post(url, headers=headers, json=body)
    

    if response.status_code == 201:
        return response.json()
    else:
        raise ValueError(f"Error: Failed to create playlist: {response.text}")


def playlist_img(playlist_id, token):
    endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/images"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "image/jpeg"}
    # read in a text file from the local dir
    with open("playlist_img.txt", "rb") as image_file:
        body = image_file.read()

    response = requests.put(endpoint, headers=headers, data=body)
    if  response.status_code != 202:
        raise ValueError(f"Error: Failed to add image to playlist: {response.text}")


def add_songs_to_playlist(uri_str_list, playlist_id, bearer_token):
    endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"}
    data = {"uris": uri_str_list,
            "position": 0}
    response = requests.post(endpoint, headers=headers, json=data)

    try: 
        response.json()["snapshot_id"]
        return 
    except KeyError:
        raise ValueError(f"Error: Failed to add songs to playlist: {response.text}")

 
# a main function to run the program
def main(query = None, spotify_search_limit=50, lookforward=5):
    
    
        
    #client_id, client_secret = get_app_credentials().values()
    client_id = os.getenv("client_id")
    client_secret = os.getenv("client_secret")
    token = get_search_token(client_id, client_secret)

    if query is None:
        query = get_text()
    search_words = query.split()
    
    print("Searching for matching songs...")
    matching_tracks = search_songs(search_words, token, spotify_search_limit, lookforward)


    # Adding for debuging, missing 13, only reaches 10,12
    Failing_phrase = {(0, 5): None, (0, 4): None, (0, 3): None, (0, 2): None, (0, 1): ['listen', 'Listen', 'spotify:track:2UWiWS7LRNyBZFAOV01WQz', 'Djo'], (1, 6): None, (1, 5): None, (1, 4): None, (1, 3): ['maybe you', 'Maybe You', 'spotify:track:1NIiYcJbjPRorMAw1XknHD', 'hølm'], (1, 2): ['maybe', 'Maybe', 'spotify:track:0xGSeBsG4V8Scc5YqpZQ66', 'Janis Joplin'], (2, 7): None, (2, 
                        6): None, (2, 5): ['you want to', 'You Want To', 'spotify:track:1hkPzjTARcarv6R7fM5o09', 'Fleeting Joys'], (2, 4): ['you want', 'You Want', 'spotify:track:6R34pagHDtRjcGX4nGzDEQ', 'Dream Sound Masters'], (2, 3): ['you', 'You', 'spotify:track:5Y77SQxEr1eiofPeUTPHxM', 'Lloyd'], (3, 8): None, (3, 7): None, (3, 6): ['want to go', 'Want to Go', 'spotify:track:3uo1bAsNUjVBieIBLiEFQl', 'MELOW MUSIC'], (3, 5): ['want to', 'Want To', 'spotify:track:3kqLybBT5LRSB9QCoR3ojK', 'Sugarland'], (3, 4): ['want', 'Want', 'spotify:track:3dEqPYFBUAOU0fqpudVnJW', 'Olamide'], (4, 9): None, (4, 8): None, (4, 7): None, (4, 6): None, (4, 5): None, 
                        (5, 10): None, (5, 9): ['go for a walk', 'Go for a Walk', 'spotify:track:3wLg8fgBK1D8gGG0D2aeOn', 'Lissie'], (5, 8): None, (5, 7): None, (5, 6): ['go', 'go', 'spotify:track:4VtRHZ4tBDHaWltVAytlLY', 'Cat Burns'], (6, 11): None, (6, 10): None, (6, 9): ['for a walk', 'For a Walk', 'spotify:track:3r9yRYUFBDn951SK9jeG1g', 'Balance And Composure'], (6, 8): None, (6, 7): None, (7, 12): ['a walk in the park', 'A Walk In The Park', 'spotify:track:16TdDKAsZodsJgP4v4ROeL', 'Laffey'], (7, 11): None, (7, 10): None, (7, 9): ['a walk', 'A Walk', 'spotify:track:0sQNqu37YQQSI3K0ueswyA', 'Tycho'], (7, 8): None, (8, 13): None, (8, 12): ['walk in the park', 'WALK IN THE PARK', 'spotify:track:0XOKietGW4PXK4hs4jyfpO', 'Jack Harlow'], (8, 11): None, (8, 10): ['walk in', 'Walk In', 'spotify:track:1hRwjAMRjUuWmjZ1NG6G1M', 'Rich Amiri'], (8, 9): ['walk', 'walk', 'spotify:track:725UfuWEXWg0C7PCqP8HIz', '310babii'], (9, 13): None, (9, 12): ['in the park', 'In The Park', 'spotify:track:2pvQe4EUSB0Wv6hHtnAIlv', 'TAKARAZI'], (9, 11): None, (9, 10): None, (10, 13): None, (10, 12): ['the park', 'The Park', 'spotify:track:5DTfoiBwW85XSWeUAknhqm', 'Haruomi Hosono'], (10, 11): None, (11, 13): None, (11, 12): ['park', 'Park', 'spotify:track:5hqh0JUxRShhqdaxu7wlz5', 'Isaiah Rashad'], (12, 13): None}
    # Same phrase, but contains 12,13 to complete the phrase
    success_path = { (0, 1): ['listen', 'listen!', 'spotify:track:12eAtj918bpsB4Vts8pCMu', 'hako'], (1, 3): ['maybe you', 'Maybe You', 'spotify:track:1NIiYcJbjPRorMAw1XknHD', 'hølm'],  (1, 2): ['maybe', 'Maybe', 'spotify:track:0xGSeBsG4V8Scc5YqpZQ66', 'Janis Joplin'], (2, 5): ['you want to', 'You Want To', 'spotify:track:4nYMwywqyNi2ZCEJB4O5Hh', 'Uptown J Slim'],  
                    (2, 3): ['you', 'You', 'spotify:track:5Y77SQxEr1eiofPeUTPHxM', 'Lloyd'], (3, 6): ['want to go', 'Want to Go', 'spotify:track:3uo1bAsNUjVBieIBLiEFQl', 'MELOW MUSIC'], (3, 5): ['want to', 'Want To', 'spotify:track:3kqLybBT5LRSB9QCoR3ojK', 'Sugarland'], (3, 4): ['want', 'Want', 'spotify:track:3dEqPYFBUAOU0fqpudVnJW', 'Olamide'],    
                    (4, 6): ['to go', 'To Go', 'spotify:track:0n5VlW5NVWjpUdkFAlKcHg', 'Home Video Variety Show'], (5, 9): ['go for a walk', 'Go for a Walk', 'spotify:track:52mVUR2Hiy22MUWjuEKuLZ', 'Relaxing Jazz Music'],   (5, 6): ['go', 'go', 'spotify:track:4VtRHZ4tBDHaWltVAytlLY', 'Cat Burns'], (6, 9): ['for a walk', 'For a Walk', 'spotify:track:3r9yRYUFBDn951SK9jeG1g', 'Balance And Composure'],   
                    (7, 12): ['a walk in the park', 'A Walk In The Park', 'spotify:track:16TdDKAsZodsJgP4v4ROeL', 'Laffey'], (7, 9): ['a walk', 'A Walk', 'spotify:track:0sQNqu37YQQSI3K0ueswyA', 'Tycho'],   (8, 12): ['walk in the park', 'WALK IN THE PARK', 'spotify:track:0XOKietGW4PXK4hs4jyfpO', 'Jack Harlow'], (8, 10): ['walk in', 'Walk In', 'spotify:track:1hRwjAMRjUuWmjZ1NG6G1M', 'Rich Amiri'], 
                    (8, 9): ['walk', 'walk', 'spotify:track:725UfuWEXWg0C7PCqP8HIz', '310babii'], (9, 12): ['in the park', 'In The Park', 'spotify:track:2pvQe4EUSB0Wv6hHtnAIlv', 'TAKARAZI'],    (10, 12): ['the park', 'The Park', 'spotify:track:5DTfoiBwW85XSWeUAknhqm', 'Haruomi Hosono'], (11, 12): ['park', 'Park', 'spotify:track:5hqh0JUxRShhqdaxu7wlz5', 'Isaiah Rashad'], 
                    (12, 13): ['sometime?', 'Sometime', 'spotify:track:0k7jQIz3bZBeeCwmBFZzOS', 'Yung Bae']}


    ''' Control failing vs working phrase'''
    #track_paths = [key for key in matching_tracks.keys() if matching_tracks[key] is not None]   
    track_paths = [key for key in success_path.keys() if success_path[key] is not None]
    #track_paths = [key for key in Failing_phrase.keys() if Failing_phrase[key] is not None]

    print("Assembling the message from titles...")
    identified_path = recursive_chain(possible_list=track_paths, end_node=len(search_words))
    identified_path.sort(key=lambda x: x[0])
    
    #print(identified_path)

    if identified_path[0][0] == "terminated at":
        raise ValueError(f"Unable to assemble the phrase. The longest path found ended at index {identified_path[0][1]}, the token not found was: \"{search_words[identified_path[0][1]]}\"")

    
    pkce_token = grantaccess_tokenretreive(client_id)

    user_id = get_user_info(pkce_token)['id']

    name = input("Enter playlist name: ")
    description = input("Enter playlist description: ")

    playlist_response = create_playlist(user_id, name, description, pkce_token)
    playlist_id = playlist_response['id']
    playlist_url = playlist_response['external_urls']['spotify']

    message_uris = [matching_tracks[edge][2] for edge in identified_path]
    #message_uris = [success_path[edge][2] for edge in identified_path]

    add_songs_to_playlist(message_uris, playlist_id, pkce_token)
    playlist_img(playlist_id, pkce_token)
    print("*"*50)
    print(f"Playlist created successfully!\n{playlist_url}")


if __name__ == "__main__":
    main(query="listen maybe you want to go for a walk in the park sometime?")
