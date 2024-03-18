song_phrase = "I'm a loser baby"
song_results = {
                "I'm": None,
                "a": None,
                "loser": [
                    "Loser",
                    "spotify:track:5PntSbMHC1ud6Vvl8x56qd",
                    "Beck"
                ],
                "baby": [
                    "Baby",
                    "spotify:track:6epn3r7S14KUqlReYr77hA",
                    "Justin Bieber"
                ],
                "I'm a": None,
                "a loser": None,
                "loser baby": [
                    "Loser Baby",
                    "spotify:track:6RNz5iOe7SzpAq4JV3Yn4w",
                    "La Bouquet"
                ],
                "I'm a loser": [
                    "I'm A Loser",
                    "spotify:track:65j5q8pfnFL8HiaN9h5mO1",
                    "The Beat Bugs"
                ],
                "a loser baby": None
            }


# a function to return a list of keys that when combined match the song phrase
def match_phrase(song_phrase, song_results):
    # get the list of words in the song phrase
    search_words = song_phrase.split()
    matching_tracks = {}
    # loop through the list of words and search for each word
    phrase_len = 1
    while phrase_len <= len(search_words):
        for i in range(len(search_words)):
            search_word = " ".join(search_words[i:i+phrase_len])
            print("Searching for: "+search_word)
            if search_word in song_results:
                matching_tracks[search_word] = song_results[search_word]
        phrase_len += 1
    return matching_tracks

# test the function
#print(match_phrase(song_phrase, song_results))

  
# a list with 10 elements, each a list of 2 elements with a random integer
idx_list = [
    [13,15],
    [11,12],
    [7,10],
    #[2,2],
    [2,4],
    [5,6],
    [0,1],
]


#print(sorted(idx_list, key=lambda x: (x[1] + 1,x[0])))


def knit_phrase(idx_list, song_phrase):
    # For each word in the song phrase, make sure that there is a match between the two elements of the sublist
    # If there is a match, return the word, otherwise return None
    search_words = song_phrase.split()
    
    expanded_set = [range(x[0],x[1]) for x in idx_list]

    range = [5,25]
    # given two numbers in range make a list of numbers between them


    print(expanded_set)

    if len(expanded_set) == len(search_words):
        return "correct number of entries"
    else:
        return "incorrect number of entries"

print(knit_phrase(idx_list, song_phrase))        