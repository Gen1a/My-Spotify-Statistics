import json
import requests
import base64
import datetime
import math
import os

import numpy as np # installed with matplotlib
from matplotlib.figure import Figure
from io import BytesIO # used to create memory buffer for matplotlib figures
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas 

from flask import Flask, g, jsonify, redirect, render_template, request, Response, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from urllib.parse import quote
from werkzeug.exceptions import HTTPException

import helpers
from filters import minutes, datetimeformat

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filters
app.jinja_env.filters["minutes"] = minutes
app.jinja_env.filters["datetimeformat"] = datetimeformat

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


#  Client Keys
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


# ------------- Spotify Base URLS -------------
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


# ------------- Server-side Parameters -------------
CLIENT_SIDE_URL = "https://my-spotify-statistics.herokuapp.com"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "user-follow-read user-library-read user-read-email user-read-private user-read-recently-played user-top-read playlist-read-private playlist-modify-public playlist-modify-private streaming"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()


# ------------- Dict of query parameters -------------
auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

# ------------- Flask User Authorization Routes -------------
@app.route("/auth")
def auth():
    # Auth Step 1.0: Requests user to authorize access
    # / route generates a request to Spotify Auth URL including the scope and the client ID
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    # Auth Step 1.1: Process Spotify response query
    # If user denies access request:
    if request.args.get('error') != None:
        return render_template("error.html", message="Access to Spotify Account needed to use this application.")
    # If user accepts access request:
    auth_token = request.args['code'] # Store query parameter 'code' which contains an authorization code that can be exchanged for an access token
    
    # Auth Step 2.0: Requests access and refresh tokens from Spotify
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
        #'client_id': CLIENT_ID, #if using non-base64-encoded way
        #'client_secret': CLIENT_SECRET, #if using non-base64-encoded way
    }

    # Syntax base64 encoded header: Authorization: Basic *<base64 encoded client_id:client_secret>*
    base64encoded = base64.b64encode(("{}:{}".format(CLIENT_ID, CLIENT_SECRET)).encode())
    headers = {"Authorization": "Basic {}".format(base64encoded.decode())}

    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Auth Step 2.1: Tokens are returned to our application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]
    refresh_token = response_data["refresh_token"]

    # Auth Step 3.0: Implement the access token in Authorization header to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}
    session["authorization_header"] = authorization_header

    return redirect(url_for("profile"))

# ------------- Flask Routes -------------
@app.route("/")
def index():
    """ Shows landing page """
    return render_template("index.html")


@app.route("/login")
def login():
    """ Shows login page """
    return render_template("login.html")


@app.route("/logout")
def logout():
    """ Logs user out """
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect(url_for("index"))


@app.route("/profile")
@helpers.login_required
def profile():
    """ Shows overview of user's Spotfy profile """
    # Get profile data
    my_profile_data = helpers.get_my_profile(session["authorization_header"])
    # Get playlists data
    my_playlists_data = helpers.get_my_playlists(session["authorization_header"])
    # Get saved tracks data
    saved_tracks_data = helpers.get_saved_tracks(session["authorization_header"])
    # Get followed artists data
    followed_artists_data = helpers.get_followed_artists(session["authorization_header"])
    # Get recently played data
    recently_played_data = helpers.recently_played_tracks(session["authorization_header"])
    # Get track popularity
    tracks = []
    for track in recently_played_data["items"]:
        track_id = track["track"]["id"]
        tracks.append(helpers.get_track(session["authorization_header"], track_id))

    return render_template("profile.html",
                            user=my_profile_data,
                            playlists=my_playlists_data,
                            saved_tracks =saved_tracks_data,
                            followed_artists=followed_artists_data,
                            recently_played=recently_played_data["items"],
                            tracks=tracks)


@app.route("/playlists")
@helpers.login_required
def playlists():
    """ Shows overview of user's Spotify playlists """
    # Get playlists data (return value = list > list > dictionary)
    all_playlists_data = helpers.get_all_my_playlists(session["authorization_header"])       
    return render_template("playlists.html", all_playlists=all_playlists_data)


@app.route("/playlists?playlist_id=<playlist_id>")
@helpers.login_required
def playlist_items(playlist_id):
    playlist_data = helpers.get_playlist_items(session["authorization_header"], playlist_id)
    playlist_name = helpers.get_playlist_name(session["authorization_header"], playlist_id)
    return render_template("playlists.html", playlist=playlist_data, name=playlist_name)


@app.route("/statistics")
@helpers.login_required
def statistics():
    return render_template("statistics.html")


@app.route("/statistics?type=<type>?time_range=<time_range>")
@helpers.login_required
def user_statistics(type, time_range):
    if type == "artists":
        top_artists_data = helpers.get_top_artists(session["authorization_header"], time_range)
        return render_template("statistics.html", top_artists=top_artists_data["items"], time_range=time_range)
    elif type == "tracks":
        top_tracks_data = helpers.get_my_top_tracks(session["authorization_header"], time_range)
        return render_template("statistics.html", top_tracks=top_tracks_data["items"], time_range=time_range)
    else:
        top_artists_data = helpers.get_top_artists(session["authorization_header"], time_range)
        # Define most popular genre from top artists
        genres_data = {}
        for item in top_artists_data["items"]:
            genres_list = item["genres"]
            for genre in genres_list:
                if genre in genres_data:
                    genres_data[genre] += 1
                else:
                    genres_data[genre] = 1
        # Returns a list of genres, sorted on the value
        sorted_genres = sorted(genres_data.items(), key=lambda x: x[1], reverse=True)
        return render_template("statistics.html", top_genres=sorted_genres, time_range=time_range)


@app.route("/track-analytics", methods=["GET", "POST"])
@helpers.login_required
def search_track_analytics():
    if request.method == "GET":
        return render_template("track-analytics.html")
    else:
        queries = request.form.get("search-query")
        if not queries:
            return render_template("error.html", message="No keywords entered. Please try again.")
        tracks_data = helpers.search_tracks(session["authorization_header"], queries)
        if tracks_data["tracks"]["total"] == 0:
            return render_template("track-analytics.html", error="Sorry, no tracks found for your query.")
        else:
            return render_template("track-analytics.html", tracks_data=tracks_data["tracks"]["items"], queries=queries)


@app.route("/track-analytics?track_id=<track_id>")
@helpers.login_required
def track_analytics(track_id):
    """ Route including usage of graphs created with matplotlib 
    # Main idea:
    # - Don't create static image files to prevent mass build-up of .jpg, .png files in directory
    # - Instead use BytesIO to hold binary stream of data in memory
    # - Follow by extracting bytes from object into plot file and embed in HTML directly
    """
    track_features = helpers.get_features(session["authorization_header"], track_id)
    track_info = helpers.get_track(session["authorization_header"], track_id)
    required_data = ["acousticness", "danceability", "energy", "instrumentalness", "liveness", "speechiness", "valence"]
    feature_data = {}
    for feature, data in track_features.items():
        if feature in required_data:
            feature_data[feature] = data
    # Sort data to match in polar axis bar chart
    labels = []
    label_data = []
    for key, value in feature_data.items():
        labels.append(key)
        label_data.append(value)
    # Generate figure without using pyplot (to prevent main thread error)
    fig = Figure()
    # Define number of bars (on polar axis)
    N = len(required_data)
    # Define x coordinates of the bars
    theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False)
    # Create an array object satisfying the specified requirements
    height = np.array(label_data)
    # Define colors of bar chart
    colors = ["#1DB954", "#39C269", "#56CB7F", "#72D394", "#8EDCAA", "#AAE5BF", "#C7EDD4"]
    # Add subplot to figure object
    ax = fig.add_subplot(111, projection='polar')
    ax.set_facecolor("#757575")
    # Set figure title and design
    title = "Audio Features"
    ax.set_title(title, fontfamily='sans-serif', fontsize='xx-large', fontweight='bold', pad=15.0, color='#ffffff')
    # Edit radius labels
    ax.set_rlim(0.0, 1)
    ax.set_rlabel_position(+15)
    ax.tick_params(axis='both', colors='#ffffff', pad=22, labelsize='large')
    # Add bar chart
    ax.bar(x=theta, height=height, width=0.8, bottom=0.0, alpha=0.7, tick_label=labels, color=colors, edgecolor="black")
    # Ensure labels don't go out of Figure view
    fig.tight_layout()
    # Save to temporary buffer
    buf = BytesIO()
    fig.savefig(buf, format='png', facecolor='#757575')
    plot_url_features = base64.b64encode(buf.getbuffer()).decode()
    # b64encode(): Encodes the bytes-like object using Base64 and returns the encoded bytes
    # getvalue(): Returns bytes containing the entire contents of the buffer
    # decode(): Decodes the contents of the binary input file and write the resulting binary data to the output file
    # Image can be shown with following syntax: data:[<mime type>][;charset=<charset>][;base64],<encoded data>
    # eg. <img src="data:image/png;base64,{}">'.format(plot_url)
    
    # Visualize track analysis data
    track_analysis = helpers.get_analysis(session["authorization_header"], track_id)
    segments = []
    loudness = []
    for segment in track_analysis["segments"]:
        segments.append(segment["start"])
        loudness.append(segment["loudness_start"])

    # Make a new figure to display track loudness
    fig2 = Figure(figsize=(15,4)) 
    # Create plots
    ax1 = fig2.subplots()
    ax1.plot(segments, loudness, color="#1DB954", linewidth=1.1)
    ax1.set_facecolor("#757575")
    # Configure x- and y-limit for the graph
    ax1.set_xlim(left=0.0, right=track_features["duration_ms"] / 1000)
    ax1.set_ylim(bottom=-60.0, top=0.0)
    # Configure ticks and labels
    ax1.set_xticks(np.linspace(0.0, track_features["duration_ms"] / 1000, endpoint=False))
    ax1.set_yticklabels([])
    ax1.tick_params(direction="inout", labelrotation=45.0, pad=-0.5)
    ax1.set(xlabel="Time (s)", ylabel="Loudness", title="Track loudness")
    # Draw grid lines
    ax1.grid()
    # Ensure xlabel doesn't go out of Figure view
    fig2.tight_layout()
    # Save to temporary buffer
    buf2 = BytesIO()
    fig2.savefig(buf2, format='png')
    plot_url_loudness = base64.b64encode(buf2.getbuffer()).decode()

    return render_template("track-analytics.html",
                           track_features=plot_url_features,
                           track_features_data=feature_data,
                           tempo=int(track_features["tempo"]),
                           key=track_features["key"],
                           track_loudness=plot_url_loudness,
                           track_info=track_info)


@app.route("/playlist-analytics")
@helpers.login_required
def search_playlist_analytics():
    """ Shows an overview of a user's playlists """
    my_playlists_data = helpers.get_all_my_playlists(session["authorization_header"])
    return render_template("playlist-analytics.html", playlists=my_playlists_data)


@app.route("/playlist-analytics?playlist_id=<playlist_id>")
@helpers.login_required
def playlist_analytics(playlist_id):
    """ 
    Shows an overview of the (average) audio features of a full playlist 
    """
    # Provide playlists overview
    my_playlists_data = helpers.get_all_my_playlists(session["authorization_header"])
    # Get playlist name
    playlist_name = helpers.get_playlist_name(session["authorization_header"], playlist_id)
    # Request a list of a playlist's items
    playlist_items = helpers.get_playlist_items(session["authorization_header"], playlist_id)
    # Create a list of a playlist's track id's
    tracks_ids = []
    for item in playlist_items:
        for subitem in item:
            tracks_ids.append(subitem["track"]["id"])
    ################
    # Create an overview of all track's audio features
    playlist_audio_features = {}
    required_features = ["danceability", "energy", "speechiness", "valence", "tempo"]
    for track_id in tracks_ids:
        track_audio_feature = helpers.get_features(session["authorization_header"], track_id)
        for feature, data in track_audio_feature.items():
            if feature in required_features:
                temp = playlist_audio_features.get(feature, 0.0) + data
                playlist_audio_features[feature] = temp
    # Calculate average for each audio feature
    for feature in required_features:
        temp = playlist_audio_features.get(feature)
        playlist_audio_features[feature] = temp / len(tracks_ids)
    # Get base64 data from matplotlib
    plot_url_features = helpers.get_playlist_audio_features(session["authorization_header"], tracks_ids)

    return render_template("playlist-analytics.html",
                        playlist_features_data=playlist_audio_features,
                        playlist_features=plot_url_features,
                        playlists=my_playlists_data,
                        playlist_name=playlist_name)
    

@app.route("/partyplanner")
@helpers.login_required
def partyplanner():
    return render_template("partyplanner.html")


@app.route("/request", methods=["GET", "POST"])
@helpers.login_required
def request_data():
    if request.method == "GET":
        query_type = request.args.get("type")
        if query_type == "artist":
            artist_name = request.args.get("query")
            artist_data = helpers.search_artists(session["authorization_header"], artist_name)
            return jsonify(artist_data)
        elif query_type == "generate-playlist":
            artist_ids = json.loads(request.args.get("query"))
            # Get top tracks for each artist
            top_tracks_container = {}
            # Get track ids (playlist analytics) and uris (playlist creation) for all top tracks
            tracks_ids = []
            tracks_uris = []
            for artist_id in artist_ids:
                top_tracks = helpers.get_top_tracks(session["authorization_header"], artist_id)
                for i in range(len(top_tracks["tracks"])):
                    tracks_ids.append(top_tracks["tracks"][i]["id"])
                    tracks_uris.append(top_tracks["tracks"][i]["uri"])
                top_tracks_container[artist_id] = top_tracks
            # Get base64 data from matplotlib
            plot_url_features = helpers.get_playlist_audio_features(session["authorization_header"], tracks_ids)
            # Calculate top genres for created playlist
            top_genres_container = {}
            for artist_id in artist_ids:
                artist_data = helpers.get_artist(session["authorization_header"], artist_id)
                for genre in artist_data["genres"]:
                    if genre in top_genres_container:
                        top_genres_container[genre] += 1
                    else:
                        top_genres_container[genre] = 1
            # Returns a list of genres, sorted on the value
            sorted_genres = sorted(top_genres_container.items(), key=lambda x: x[1], reverse=True)
            return jsonify(top_tracks=top_tracks_container,
                           top_genres=sorted_genres,
                           tracks_uris=tracks_uris,
                           url=plot_url_features)
    elif request.method == "POST":
        # Get post request payload
        payload = request.json
        # Get playlist name from payload
        playlist_name = payload['name']
        # Get playlist description from payload
        playlist_description = payload['description']
        if playlist_description == '':
            playlist_description =  'Party Playlist created by My Spotify Statistics.'
        # Get track uris from payload and convert from JSON string to list
        track_uris = json.loads(payload['uris'])
        # Create the Spotify playlist
        user_profile_data = helpers.get_my_profile(session["authorization_header"])
        user_id = user_profile_data["id"]
        new_playlist_object = helpers.create_playlist(session["authorization_header"],
                                                      user_id,
                                                      playlist_name,
                                                      playlist_description)
        # Get new playlist api endpoint from new playlist object
        new_playlist_href = new_playlist_object["tracks"]["href"]
        # Get new playlist external url
        new_playlist_url = new_playlist_object["external_urls"]["spotify"]
        print(new_playlist_url)
        # Slice amount of tracks (Spotify API accepts max 100 tracks / request)
        tracks_amount = len(track_uris)
        slicer = slice(0, 100)
        track_uris_body = {}
        for i in range(0, math.floor(tracks_amount / 100.0) + 1):
            slicer = slice((100 * i), ((100 * i) + 100), 1)
            track_uris_body["uris"] = track_uris[slicer]
            playlist_snapshot = requests.post(new_playlist_href,
                                          headers=session["authorization_header"],
                                          data=json.dumps(track_uris_body))

        return jsonify(new_playlist_url)


#@app.route("/test")
#def test():


# Error handler
@app.errorhandler(Exception)
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html", message=e)


if __name__ == "__main__":
    # Threaded option to enable multiple instances for multiple user access support
    app.run(debug=True, threaded=True)