import os
import urllib.parse
from dotenv import load_dotenv, find_dotenv
import playlistr as pl
from dash import Dash, html, dcc, callback, Input, Output, State, no_update

load_dotenv(find_dotenv())
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
redirect_uri = os.getenv("redirect_uri")
spotify_search_limit = 50
lookforward = 5

code_verifier, code_challenge = pl.generate_code_verifier_and_challenge()

auth_link = pl.authorization_link(client_id, code_challenge)



app = Dash(__name__)
server = app.server

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="auth_code"),
    dcc.Interval(id="status_interval", interval=10000, n_intervals=0), # 10 seconds
    html.H1("Playlistr"),
    html.Br(), html.Br(),
    html.A(html.Button("Sign in with Spotify", id="sign_in", n_clicks=0), 
           href=auth_link,
           style={'display': 'inline-block'}),
    html.Br(), html.Br(),
    dcc.Textarea(id="message-input", placeholder="Enter a message", style={"width": "30%"}, disabled=True),
    html.Br(),
    html.Div(id="status", children=""),
    html.Br(),
    html.A(html.Button("Submit", id="submit", n_clicks=0, disabled=True),
           id="submit-button",
           style={'display': 'inline-block'}),
    html.Br(), html.Br(),
    html.Div(id="err_message", children="", style={"color": "red"}),
    ],
    style={}
    )



@app.callback(
        Output('auth_code', 'data'), 
        Input('url', 'search'))
def store_code(search):
    if search:
        params = urllib.parse.parse_qs(search[1:])
        return params.get('code', [''])[0]

@app.callback(
        [Output('message-input', 'disabled'),
         Output('submit', 'disabled'),
         Output('sign_in', 'disabled')],
        Input('auth_code', 'data'))
def enable_textarea(data):
    is_disabled = not data
    # text_area, submit, sign_in; might just remove the options.
    return is_disabled, is_disabled, not is_disabled

@app.callback(
        [Output('submit','children'),
         Output('submit-button','href'),
         Output('err_message','children', allow_duplicate=True)],
        Input('submit','n_clicks'),
        State('message-input', 'value'),
        State('auth_code', 'data'))
def submit_message(n_clicks, value, auth_code):
    # aborting if the button has already been clicked
    # or the message value is empty
    if n_clicks > 1 or not value:
        return no_update, no_update, no_update

    try:
        token = pl.get_search_token(client_id, client_secret)
        
        search_words = value.split()
        matching_tracks = pl.search_songs(search_words, token, spotify_search_limit, lookforward)
        track_paths = [key for key in matching_tracks.keys() if matching_tracks[key] is not None]
        identified_path = pl.recursive_chain(track_paths, len(search_words))
        message_uris = [matching_tracks[edge][2] for edge in identified_path]

        if identified_path[0][0] == "terminated at":
            return no_update, no_update, f"Unable to assemble the phrase. The longest path found ended at index {identified_path[0][1]}, the word not found was: \"{search_words[identified_path[0][1]]}\""

        pkce_token_json = pl.obtain_pkce_token(client_id, auth_code, code_verifier, redirect_uri)
        pkce_token = pkce_token_json['access_token']

        user_id = pl.get_user_info(pkce_token)['id']

        name = "A message for you"
        description = "A playlist generated from a message"

        playlist_response = pl.create_playlist(user_id, name, description, pkce_token)
        playlist_id = playlist_response['id']
        playlist_url = playlist_response['external_urls']['spotify']

        

        pl.add_songs_to_playlist(message_uris, playlist_id, pkce_token)
        pl.playlist_img(playlist_id, pkce_token)
    except:
        return no_update, no_update, "An error occurred while trying to generate the playlist. Please try again."

    return "Playlist Available", playlist_url, no_update

@app.callback(
    Output('err_message', 'children', allow_duplicate=True),
    Input('submit', 'n_clicks'))
def clear_error(n_clicks):
    if n_clicks:
        return ""

@app.callback(
    Output('status', 'children'),
    Input('status_interval', 'n_intervals'),
    State('submit', 'n_clicks'),
    State('err_message', 'children'),
    State('submit', 'children'))
def update_status(n_intervals, n_clicks, err, submit_text):
    if (n_clicks == 0) or (err) or (submit_text != "Submit"):
        return ""

    status_messages = ["Artist Collaboration underway", 
                       "Harmonizing syllables with cymbals", 
                       "Generating AI cover art", 
                       "Building custom text-to-playlist hardware...",
                       "Negotiating better streaming royalties for indie bands..."
                       "Refreshing the tickets page of your favorite band",
                       "Rolling 4d20+6 to determine the next song",
                       "Suppressing the self-awareness of Spotify's DJ",
                       "Recommending a song to your ex",
                       "Recommending a song to your ex's ex",
                       "Honestly you two might get along",
                       "Usually it doesn't take this long I swear",
                       "Jeez are you trying to send a book or something?",]

    return status_messages[n_intervals % len(status_messages)]

#TODO
 # venv and requirements
 # weird 

if __name__ == '__main__':
    app.run_server(debug=True)