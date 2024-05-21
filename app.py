import os
import json
import urllib.parse
from dotenv import load_dotenv, find_dotenv
import playlistr as pl
from dash import Dash, html, dcc, callback, Input, Output, \
                    State, no_update, callback_context, MATCH, ALL
import dash_bootstrap_components as dbc

load_dotenv(find_dotenv())

# API Credentials and Redirect. 
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
redirect_uri = os.getenv("redirect_uri")

# PKCE Authorization Flow
code_verifier, code_challenge = pl.generate_code_verifier_and_challenge()
auth_link = pl.authorization_link(client_id, code_challenge, redirect_uri)

# Search Parameters
spotify_search_limit = 50
app_spotify_search_limit = 25
lookforward = 5

# Dash App
app = Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
server = app.server
app.title = "Playlistr"

# Layout
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="pkce_token"),
    dcc.Interval(id="status_interval", interval=7000, n_intervals=0), # 7 seconds
    html.H1("Playlistr", style={"textAlign": "center"}),
    html.Br(), html.Br(),
    html.P("Welcome to Playlistr! Playlistr is a tool that allows you to create Spotify playlists based on a message or a list of songs. You can either pick and choose songs to add to your playlist or let Playlistr automatically generate a playlist based on a message you provide."),
    html.P("Sign into Spotify to get started."),
    html.Br(),
    dbc.Button("Sign in with Spotify", id="sign_in", n_clicks=0, style={'display': 'inline-block'}, href=auth_link),
    html.Br(), html.Br(),
    html.Div(id = "hidden-div", style={'opacity':'0.3', 'pointerEvents':'none'},
        children=[
        dbc.Tabs(children=[
            dbc.Tab(id='tab-auto', label="Auto-Solver", children=[
                html.Br(),
                dcc.Input(id={'type':'message-title','index':2}, placeholder="Enter the message Title", style={"width": "30%"}),
                html.Br(), html.Br(),
                dcc.Input(id={'type':'message-description','index':2}, placeholder="Enter the message Description", style={"width": "30%"}),
                html.Br(), html.Br(),
                html.Br(),
                dbc.Textarea(id="message-input", placeholder="Enter a message", style={"width": "40%"}),
                html.Br(),
                html.Div(id="status", children=""),
                html.Br(),
                dbc.Button(children="Submit", id="submit", n_clicks=0, style={'display': 'inline-block'}),
                html.Br(), html.Br(),
                html.Div(id="err_message", children="", style={"color": "red"}),
            ]), # end of auto-solver tab
            dbc.Tab(id = 'tab-pick', label="Pick and Choose", children=[
                html.Br(),
                dcc.Input(id={'type':'message-title','index':1}, placeholder="Enter the message Title", style={"width": "30%"}),
                html.Br(), html.Br(),
                dcc.Input(id={'type':'message-description','index':1}, placeholder="Enter the message Description", style={"width": "30%"}),
                html.Br(), html.Br(),
                html.Br(),
                dbc.Table(id="selected-tracks-table", children=[
                    html.Thead(html.Tr([html.Th(""), 
                                        html.Th("Title", style={'color':'darkgrey'}), 
                                        html.Th("Artist",style={'color':'darkgrey'}), 
                                        html.Th("URI",style={"display":"none", 'color':'darkgrey'})])),
                    html.Tbody(id = 'selected-tracks', children=[])]),
                html.Br(),
                html.Div(
                    dbc.Button(children="Create Playlist", id="submit-pick", n_clicks=0, style={'display': 'inline-block'}, target="_blank"),
                    style={'textAlign':'right'}),
                html.Br(), html.Br(),
                html.Div([
                    dbc.Input(id="search", placeholder="Search for a song", style={"width": "30%", "display":"inline-block", "margin-right":"20px"}),
                    dbc.Button("Search", id="search-button", n_clicks=0, style={"display":"inline-block"})],
                    style={'width':'100%', 'textAlign':'center'}
                ),
                html.Br(), html.Br(),
                dbc.Table(id="search-results-table", children=[
                    html.Thead(html.Tr([html.Th(""), 
                                        html.Th("Title", style={'color':'darkgrey'}), 
                                        html.Th("Artist", style={'color':'darkgrey'}), 
                                        html.Th("URI", style={'color':'darkgrey', "display":"none"})])),
                    html.Tbody(id = "search-results-body", children=[])]),
                html.Br(),
                dcc.Store(id="next-page-uri"), # storing uri for the next page
                html.Div(dbc.Button("Next Page", id="next-page", style={'align':'right'}), style={'textAlign':'right'}),
            ]) # end of pick and choose tab
        ])# end of tabs
        ]), # end of hidding div
    html.Div([
        "Made by ", 
        html.A("James Welch", href="https://github.com/jwelch1123",  target="_blank", style={'color': 'grey'}),
        " · ",
        "View ", 
        html.A("Playlistr on GitHub", href="https://github.com/jwelch1123/playlistr",  target="_blank", style={'color': 'grey'})
        ], style={'textAlign': 'center', 'color': 'grey', 'fontSize': '0.8em', 'marginTop': '20px'}
        )


    ],
    style={'margin': 'auto',
           'marginTop': '1%',
           'maxWidth': '95%', 
           'maxHeight': '95%',
           'padding': '20px',
           'border':'1px solid #ccc',
           'borderRadius': '10px'
           }
)

# Callbacks
@app.callback(
        Output('pkce_token', 'data'), 
        Input('url', 'search'))
def get_code_store_pkce(search):
    """
    Retrieves the PKCE token from the given search parameter.

    Args:
        search (str): The search parameter (url) containing the code.

    Returns:
        str: The PKCE token to the store component.

    Raises:
        Exception: If an error occurs while obtaining the PKCE token.
    """
    if search:
        print("search: ", search)
        params = urllib.parse.parse_qs(search[1:])
        auth_code = params.get('code', [''])[0]
        print(client_id, auth_code, code_verifier, redirect_uri)

        try:
            pkce_token_json = pl.obtain_pkce_token(client_id, auth_code, code_verifier, redirect_uri)
            print("pkce_token_json: ", pkce_token_json)
            pkce_token = pkce_token_json['access_token']
        except:
            return no_update

        return pkce_token
    print("looked for url search but didnt find it")
    return no_update

@app.callback(
    Output('hidden-div', 'style'),
    Output('sign_in', 'style'),
    Output('sign_in', 'disabled'),
    Input('pkce_token', 'data'))
def show_hidden_div(data):
    """
    Show the hidden div when the PKCE token is available.

    Args:
        data (str): The PKCE token.

    Returns:
        dict: The style properties to be applied to the hidden div.
    """
    if data:
        return {'opacity':'1', 'pointerEvents':'auto'}, {'opacity':'0.5', 'pointerEvents':'none'}, True
    return {'opacity':'0.5', 'pointerEvents':'none'}, no_update, False

# auto-solver
@app.callback(
        [Output('submit','children'),
         Output('submit','href'),
         Output('submit', 'style'),
         Output('err_message','children')],
        Input('submit','n_clicks'),
        State('message-input', 'value'),
        State('pkce_token', 'data'),
        #State('message-title', 'value'),
        State({'type':'message-title','index':ALL},'value'),
        State({'type':'message-description','index':ALL},'value'),
        #State('message-description', 'value')
        )
def submit_message(n_clicks, value, pkce_token, title, description):
    """
    Callback function that is triggered when the 'submit' button is clicked.
    It takes the input values from the user interface and performs the necessary actions to generate a playlist.

    Args:
        n_clicks (int): The number of times the 'submit' button has been clicked.
        value (str): The value entered in the 'message-input' field.
        pkce_token (str): The PKCE token.
        title (str): The title of the playlist.
        description (str): The description of the playlist.

    Returns:
        children (str): The text to be displayed on the 'submit' button.
        href (str): The URL to be assigned to the 'submit' button.
        style (dict): The style properties to be applied to the 'submit' button.
        err_message (str): The error message to be displayed, if any.
    """
    print("submit message")
    if n_clicks > 1 or not value:
        return no_update, no_update, no_update, no_update

    try:
        token = pl.get_search_token(client_id, client_secret)
        
        search_words = value.split()
        matching_tracks = pl.search_songs(search_words, token, spotify_search_limit, lookforward)
        track_paths = [key for key in matching_tracks.keys() if matching_tracks[key] is not None]
        identified_path = pl.recursive_chain(track_paths, len(search_words))
        message_uris = [matching_tracks[edge][2] for edge in identified_path]

        if identified_path[0][0] == "terminated at":
            return no_update, no_update, no_update, f"Unable to assemble the phrase. The longest path found ended at index {identified_path[0][1]}, the word not found was: \"{search_words[identified_path[0][1]]}\""

        pkce_token = pkce_token

        user_id = pl.get_user_info(pkce_token)['id']

        name = title if title else "Playlistr Message"
        description = description if description else "Playlistr generated playlist, how cool is that?"

        playlist_response = pl.create_playlist(user_id, name, description, pkce_token)
        playlist_id = playlist_response['id']
        playlist_url = playlist_response['external_urls']['spotify']

        

        pl.add_songs_to_playlist(message_uris, playlist_id, pkce_token)
        pl.playlist_img(playlist_id, pkce_token)
    except Exception as e:
        print("*"*50)
        print(e)
        return no_update, no_update, no_update, "An error occurred while trying to generate the playlist. Please refresh & try again."

    return "Playlist Available", playlist_url, {'display':'inline-block', "color":"green"}, no_update

@app.callback(
    Output('status', 'children'),
    Input('status_interval', 'n_intervals'),
    State('submit', 'n_clicks'),
    State('err_message', 'children'),
    State('submit', 'children'))
def update_status(n_intervals, n_clicks, err, submit_text):
    """
    Update the status message based on the number of intervals and user inputs.

    Args:
        n_intervals (int): The number of interval component.
        n_clicks (int): The number of clicks on the submit button.
        err (str): The error message.
        submit_text (str): The text on the submit button.

    Returns:
        status (str): The updated status message, replaced with a empty string if the conditions are not met.
    """
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

    return "Working on: " + status_messages[n_intervals % len(status_messages)]

# pick and choose
@app.callback(
        Output('search-results-body', 'children'),
        Output('next-page-uri', 'data'),
        Input('search-button', 'n_clicks'),
        Input('next-page', 'n_clicks'),
        State('next-page-uri', 'data'),
        State('search', 'value'))
def search_song(n_clicks, next_n_clicks, next_page_uri, search):
    """
    Perform a song search based on the user's input and update the search results table.

    Args:
        n_clicks (int): The number of times the search button has been clicked.
        next_n_clicks (int): The number of times the next page button has been clicked.
        next_page_uri (str): The URI of the next page of search results.
        search (str): The user's search query.

    Returns:
        table_rows (list): A list of HTML table rows representing the search results.
        next_page_uri (str): The updated URI of the next page of search results.
    """
    print("searching song")
    if (n_clicks == 0) or (next_n_clicks == 0) or (search == '') \
        or (search is None): # this is a little finiky, but it works if you update the search but hit next page it loads next page not the search
        print("triggered no clicks or no search")
        print(n_clicks, next_n_clicks, search, next_page_uri)
        return no_update, no_update
        
    token = pl.get_search_token(client_id, client_secret)

    ctx = callback_context.triggered[0]['prop_id'].split('.')[0]
    if ctx == "search-button":
        search_results = pl.search_songs_app(search, token, app_spotify_search_limit)
    elif ctx == "next-page":
        search_results = pl.next_page(next_page_uri, token)
    

    # if the list is empty, return a message saying that no results were found
    if search_results["tracks"]["total"] == 0:
        return html.Tr([html.Td("No results found")]), no_update

    next_page_uri = search_results["tracks"]["next"]

    table_rows = []
    for idx, track in enumerate(search_results['tracks']['items']):
        if track is not None:
            table_rows.append(html.Tr(
                [html.Td(dbc.Button("Add", id={'type':'add-song','index':idx}, n_clicks=0)), 
                    html.Td(track["name"]), 
                    html.Td(track['artists'][0]['name']), 
                    html.Td(track['uri'], style={"display":"none"})])
                )
    
    return table_rows, next_page_uri

@app.callback(
    Output('selected-tracks', 'children'),
    Input({'type':'add-song','index':ALL}, 'n_clicks'),
    Input({'type':'remove-song','index':ALL}, 'n_clicks'),
    State('selected-tracks', 'children'),
    State('search-results-body', 'children'))
def select_song(n_clicks_add, n_clicks_remove, selected_tracks, search_results):
    """
    Callback function for selecting and removing songs in a playlist.

    Args:
        n_clicks_add (list): List of integers representing the number of times each 'add-song' button was clicked.
        n_clicks_remove (list): List of integers representing the number of times each 'remove-song' button was clicked.
        selected_tracks (list): List of selected tracks in the playlist.
        search_results (list): List of search results for songs.

    Returns:
        row (list): Updated list of selected tracks in the playlist.
    """
    print("selecting song")
    ctx = callback_context
    if (not ctx.triggered):
        print("no context triggered")
        return no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_prop = json.loads(button_id)
    button_idx = button_prop['index']

    if button_prop['type'] == 'add-song':
        if (sum(n_clicks_add) == 0):
            print("no add song click")
            return no_update
        print("adding song")
        song_info = search_results[button_idx]
        selected_track_len = len(selected_tracks)
        selected_tracks.append(html.Tr([
            html.Td(dbc.Button("Remove", id={'type':'remove-song','index':selected_track_len}, n_clicks=0)),
            html.Td(song_info['props']['children'][1]['props']['children']), # Song name
            html.Td(song_info['props']['children'][2]['props']['children']), # Artist name
            html.Td(song_info['props']['children'][3]['props']['children'], style={"display":"none"}), # URI
            ]))
        return selected_tracks
    
    elif button_prop['type'] == 'remove-song':
        if (sum(n_clicks_remove) == 0):
            print("no remove song click")
            return no_update
        print("removing song")

        selected_tracks.pop(button_idx)
        table_rows = []
        for idx, track in enumerate(selected_tracks):
            track = track['props']['children']
            table_rows.append(html.Tr(
                [html.Td(track[0]['props']['children']), # song name
                 html.Td(track[1]['props']['children']), # artist name
                 html.Td(track[2]['props']['children'], style={"display":"none"}), # uri
                 html.Td(html.Button("Remove", id={'type':'remove-song','index':idx}, n_clicks=0))])
                )
        return table_rows

    else:
        return no_update

@app.callback(
        Output('submit-pick', 'href'),
        Output('submit-pick', 'style'),
        Output('submit-pick', 'children'),
        Input('submit-pick', 'n_clicks'),
        State('selected-tracks', 'children'),
        State('pkce_token', 'data'),
        #State('message-title', 'value'),
        #State('message-description', 'value')
        State({'type':'message-title','index':ALL},'value'),
        State({'type':'message-description','index':ALL},'value')
        )
def submit_create_playlist(n_clicks, selected_tracks, pkce_token, title, description):
    """
    Submits the selected tracks to create a playlist.

    Args:
        n_clicks (int): The number of times the submit button has been clicked.
        selected_tracks (list): The list of selected tracks.
        pkce_token (str): The PKCE token.
        title (str): The title of the playlist.
        description (str): The description of the playlist.

    Returns:
        playlist_url (str): The URL of the created playlist.
        style (dict): The style properties to be applied to the submit button.
        text (str): The text to be displayed on the submit button.
    """
    if (n_clicks == 0) or (len(selected_tracks) == 0):
        print("fired no clicks or no tracks")
        return "", {'display': 'inline-block'}, "Create Playlist"

    print("running the playlist creation")
    print(n_clicks, selected_tracks, pkce_token,  title, description)

    user_id = pl.get_user_info(pkce_token)['id']
    name = title if title else "Playlistr Message"
    description = description if description else "Playlistr generated playlist, how cool is that?"
    pkce_token = pkce_token
    

    playlist_response = pl.create_playlist(user_id, name, description, pkce_token)
    playlist_id = playlist_response['id']
    playlist_url = playlist_response['external_urls']['spotify']

    message_uris = [track['props']['children'][2]['props']['children'] for track in selected_tracks]

    print("got uri list: ", message_uris)
    

    pl.add_songs_to_playlist(message_uris, playlist_id, pkce_token)
    pl.playlist_img(playlist_id, pkce_token)
    print("made playlist and updating link")

    return playlist_url, {'display':'inline-block', "color":"green"}, "Playlist Available, click to view"

# Do Things
if __name__ == '__main__':
    app.run_server(debug=True)