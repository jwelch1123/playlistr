# Playlistr

This programs uses the Spotify API to assemble a playlist of track titles matching the message of your choice and saves it to your Spotify account. The message can either be automatically assembled or songs can be individually selected.

Try out the site: [Playlistr](https://playlistr-1e867cea68d7.herokuapp.com/)

## Operation:
There are a couple ways to use this program, the Dash App provides two interfaces: pick-and-choose which provides a search bar, search results, and a running list of tracks, and auto-solver which takes the message and tries to assembled a list of tracks matching the message. The playlistr.py program can be run on it's own as many of the functions the app uses are sourced from the program file. 

### Playlistr.py:
First, this program uses dotenv to get the ID and Secret provided by Spotify. Using the Python requests package these are sent to Spotify's API to receive an Access Token which is used to return search results. 

Your message is then passed to several functions which use a sliding and decreasing window to search for matching songs. So we might look for words 1->3, then 1->2, 1 alone, followed by 2->4, 2->3, 2 alone, etc. Whether a matching track is found or not a tuple of the start and end index are returned as a dictionary key along with None or the song information. 

After all combinations have been accessed for a match, the program uses the start and end indexes to create a chain of titles representing your message. For instance, we might have found matching tracks for the 1st word, 2nd-3rd, 4th to 6th, etc. These titles need to be joined without missing or repeated words. This can be thought of as a graph network with the nodes representing the junction (or space) between two words in the message, the edges are the track titles that connect the space before the first word in a track and the space after the last word in the track. I implement a recursive search (depth first) to find a path from the first to last nodes (words in the message). If a path isn't found the last word and an error message are displayed.

To add the playlist to a user's profile access is needed via the [PCKE method](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow). The user is prompted to follow a link and permit access to their username, and ability to edit playlists. They are redirected to a localhost link which is copied and pasted into the command line. 

Finally, the user provides a title and description for the playlist created via Spotify's API. Tracks are added to the playlist along with a cover image and the link is displayed to the user. 

### Dash App:
The user is prompted to sign into their spotify account using Spotify's [PCKE method](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow). The link they use is created using the APP ID and Secret from Spotify as well as a code verifier and challenge. After log-in the user is then redirected to the redirect url (which is stored as an environmental variable.) which is copied and pasted back into the command line. The change in url triggers a callback function which extracts the code parameter and sends it to Spotify's API to obtain the PCKE access token. The token is saved to a storage element and the callback function un-hides the rest of the app. Besides the message title and description, the user can choose to use the auto-solver or pick-and-choose which have separate tabs.

#### Pick and Choose (Dash App):
Since there can be errors in the auto-solver, the user can choose to search for tracks individually. The user types in a word or phrase and clicks search. The search results are displayed and the user can add a track to another table which also allows removal. The user can then choose to create the playlist which adds the playlist and selected tracks to their Spotify account and provides a link to view the playlist.

#### Auto-Solver:
This works almost identically to the playlistr.py main function. The user provides a message and the program tries to assemble a list of tracks that match the message (more details are provided above). The playlist is then added to their Spotify account and a link is provided for the user to view the playlist.

## Usage:

### Run Playlistr.py Locally:
1. Follow [this guide from Spotify](https://developer.spotify.com/documentation/web-api/tutorials/getting-started) to register your own app and obtain credentials. Add 'localhost:8080' as a redirect uri.
2. Download the repo and install the requirements file, `pip install requirements.txt` 
3. In the directory of `playlistr.py` create a `.env` file and add three lines for the client id, client secret, and redirect uri provided by/to Spotify for your app. 
    > client_id='abcdedcba'
    >
    > client_secret='secret'
    > 
    > redirect_uri='http://localhost:8080'

4. The program can be invoked from the command line. If it successfully creates the message, a link will be provided to allow access to your Spotify account. 
    - Permissions Used: View username, Create and Edit playlist. 
5. After allowing permissions the page will redirect to `localhost:8080`, and copy the complete URL back into the command line. 
6. Provide a playlist name and description.

### Run the Dash app Locally or on  Heroku:
1. Fork the repo to your own github account, and set up an account on Heroku. Create a new Heroku app and connect it to your forked repo.
2. Follow [this guide from Spotify](https://developer.spotify.com/documentation/web-api/tutorials/getting-started) to register your own app and obtain credentials. Add the Heroku app's url as a redirect uri (it can also be useful to add `http://127.0.0.1:8050/` to troubleshoot the app locally, make sure to update the `.env` file with this redirect uri as well.)
3. In the settings tab of your Heroku app, add the client id, secret, and redirect_uri (url of the app) as config vars. The redirect_uri should be the same as the one you provided to Spotify.
4. In the deploy tab of your Heroku app, enable automatic deploys from your forked repo.


## Known Issues:
- Commonly the tracks found can not be assembled into a phrase that matches yours. This is either due to words in your message not being found in the returned tracks or multiple tracks not lining up correctly. Rephrasing your message can help, the program will return the last word it was able to assemble but doesn't differentiate between these two failure modes.
- Very common short words such as "the", "a", "are" have a low chance of returning as a single-word track title. They are usually part of a multi-word track title which should factor into your decision on how to construct your message. 
- Searching through the Spotify API appears to return different track results compared to searching via the app. This may lead to tracks not being found by this program but can easily be identified by a search. Increasing the "search_rounds" of the "match_phrase" function may help.
- Occasionally the program will have issues with the PKCE token expiring. This can be fixed by refreshing the program and logging in again.
- The Dash app can fail to upload the playlist image to Spotify if the internet connection is slow.


## Acknowledgements
Default photo for playlist by <a href="https://unsplash.com/@namroud?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">Namroud Gorguis</a> on <a href="https://unsplash.com/photos/photo-of-black-and-brown-cassette-tape-FZWivbri0Xk?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">Unsplash</a>, edited and downscaled by me

Thanks to [novatorem](https://github.com/novatorem/novatorem/tree/main) for the dotenv usage example and inspiration to pass a playlist image. 

[Spotify's developer guide and API documentation](https://developer.spotify.com/documentation/web-api) was a great help in creating this project.
