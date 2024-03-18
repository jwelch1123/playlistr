import json
import base64
import requests

#implement dotenv for credentials

def get_credentials():
    #get client id and secret from credentials.json
    with open('credentials.json') as f:
        credentials = json.load(f)
    return credentials
    

def get_token(credentials):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_headers = {'Authorization': 'Basic ' + base64.b64encode((credentials["client_id"] + ':' + credentials["client_secret"]).encode()).decode()}
    auth_data = {'grant_type': 'client_credentials'}

    response = requests.post(auth_url, headers=auth_headers, data=auth_data)

    
    if response.status_code == 200:
        token = response.json()['access_token']
    else:
        print("Error: Something went wrong")
        print(response.text)
        token = None
    return token


def get_text():
    query = input("Enter song name: ")
    return query


def return_song(response, query):
    if response.status_code != 200:
        print("Error: Something went wrong")
        print(response.text)
    else:
        data = response.json()
        if data["tracks"]["total"] == 0:
            print(f"No song found for '{query}'")
        else:
            return data
    

def match_phrase(url, headers, query):
    
    # get the first song from the search results
    response = requests.get(url, headers=headers)
    returned_songs = return_song(response, query)
    i = 0
    search_rounds = 10

    while i <= search_rounds:
        for track in returned_songs["tracks"]["items"]:
            if track["name"].lower().strip() == query.lower().strip():
                return track
        returned_songs = return_song(requests.get(returned_songs["tracks"]["next"], headers=headers), query)            
        i += 1


def hierarch_match_phrase(url, headers, query, ngram_length, limit):
    #TODO: implement this function
    pass


# a main function to run the program
def main():
    #serch_phrase = get_text()
    #serch_phrase = "Sometimes I feel bad at being myself"
    serch_phrase = "I'm a loser baby"

    limit = "10"
    ngram = 3
    token = get_token(get_credentials())
    search_words = serch_phrase.split()
    matching_tracks = {}

    if token == None:
        print("Error: Something went wrong retrieving token, check credentials and try again.")
        return

    # loop through the list of words and search for each word
    phrase_len = 1
    while phrase_len <= ngram:
        for i in range(len(search_words)):
            search_word = " ".join(search_words[i:i+phrase_len])
            print("Searching for: "+search_word)
            url = "https://api.spotify.com/v1/search?q={"\
                    +search_word\
                    +"}&market=US&type=track&limit="\
                    +limit
            
            headers = {"Authorization": "Bearer "+token,}
            
            # call the match_phrase function
            found_track = match_phrase(url, headers, search_word)

            try:
                song_name   = found_track["name"]
                song_uri    = found_track['uri']
                artist_name = found_track["artists"][0]["name"]
                matching_tracks[search_word] = [song_name, song_uri, artist_name]
                print("saving song info to matching_tracks")
            except:
                matching_tracks[search_word] = None

        phrase_len += 1
    
    print(json.dumps(matching_tracks, indent=4))
    

# call the main function derp
main()
