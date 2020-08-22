import os
import requests
import json
import urllib.parse
from flask import redirect, render_template, request, session
from functools import wraps

import numpy as np # installed with matplotlib
from matplotlib.figure import Figure
from io import BytesIO # used to create memory buffer for matplotlib figures
import base64


# ------------- Spotify Base URLS -------------
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# ------------- Flask's 'Login required' decorator -------------
def login_required(f):
    """
    Decorate routes to require login:
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function():
        if session.get("authorization_header") is None:
            return redirect("/login")
        return f()
    return decorated_function


# ------------- Audio Features Analysis --------------
def get_playlist_audio_features(auth_header, tracks_ids):
    # Create an overview of all track's audio features
    playlist_audio_features = {}
    required_features = ["danceability", "energy", "speechiness", "valence", "tempo"]
    for track_id in tracks_ids:
        track_audio_feature = get_features(auth_header, track_id)
        for feature, data in track_audio_feature.items():
            if feature in required_features:
                temp = playlist_audio_features.get(feature, 0.0) + data
                playlist_audio_features[feature] = temp
    # Calculate average for each audio feature
    for feature in required_features:
        temp = playlist_audio_features.get(feature)
        playlist_audio_features[feature] = temp / len(tracks_ids)
    # Sort data to match in polar axis bar chart
    labels = []
    label_data = []
    for key, value in playlist_audio_features.items():
        if key != "tempo":
            labels.append(key)
            label_data.append(value)
    # Generate bar chart on polar axis with matplotlib
    # Generate figure without using pyplot (to prevent main thread error)
    fig = Figure()
    # Define number of bars (on polar axis)
    N = len(required_features) - 1
    # Define x coordinates of the bars
    theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False)
    # Create an array object satisfying the specified requirements
    height = np.array(label_data)
    # Define colors of bar chart
    colors = ["#1DB954", "#39C269", "#56CB7F", "#72D394"]
    # Add subplot to figure object
    ax = fig.add_subplot(111, projection='polar')
    ax.set_facecolor("#757575")
    title = "Audio Features"
    ax.set_title(title, fontfamily='sans-serif', fontsize='xx-large', fontweight='bold', pad=15.0, color='#ffffff')
    # Edit radius labels
    ax.set_rlim(0.0, 1)
    ax.set_rlabel_position(+45)
    ax.tick_params(axis='both', colors='#ffffff', pad=22, labelsize='large')
    # Add bar chart
    ax.bar(x=theta, height=height, width=0.8, bottom=0.0, alpha=0.7, tick_label=labels, color=colors)
    # Ensure labels don't go out of Figure view
    fig.tight_layout()
    # Save to temporary buffer
    buf = BytesIO()
    fig.savefig(buf, format='png', facecolor='#757575')
    plot_url_features = base64.b64encode(buf.getbuffer()).decode()
    features_container = {
        "base64" : plot_url_features,
        "data" : playlist_audio_features}
    return features_container


# ------------- User Requests -------------
# Define Profile API endpoint
MY_PROFILE_ENDPOINT = "{}/me".format(SPOTIFY_API_URL)
SAVED_TRACKS_ENDPOINT = "{}/tracks".format(MY_PROFILE_ENDPOINT)
FOLLOWED_ARTISTS_ENDPOINT = "{}/following?type=artist".format(MY_PROFILE_ENDPOINT)
TOP_ENDPOINT = "{}/top".format(MY_PROFILE_ENDPOINT)

def get_my_profile(auth_header):
    profile_response = requests.get(MY_PROFILE_ENDPOINT, headers=auth_header)
    my_profile_data = json.loads(profile_response.text)
    return my_profile_data


def get_saved_tracks(auth_header):
    saved_tracks_response = requests.get(SAVED_TRACKS_ENDPOINT, headers=auth_header)
    saved_tracks_data = json.loads(saved_tracks_response.text)
    return saved_tracks_data


def get_followed_artists(auth_header):
    followed_artists_response = requests.get(FOLLOWED_ARTISTS_ENDPOINT, headers=auth_header)
    followed_artists_data = json.loads(followed_artists_response.text)
    return followed_artists_data


def get_top_artists(auth_header, time_range):
    """ Gets top 50 artists over a predefined time range"""
    TOP_ARTISTS_ENDPOINT = "{}/artists?time_range={}&limit=50".format(TOP_ENDPOINT, time_range)
    top_artists_response = requests.get(TOP_ARTISTS_ENDPOINT, headers=auth_header)
    top_artists_data = json.loads(top_artists_response.text)
    return top_artists_data


def get_my_top_tracks(auth_header, time_range):
    """ Gets top 50 tracks over a predefined time range"""
    TOP_TRACKS_ENDPOINT = "{}/tracks?time_range={}&limit=50".format(TOP_ENDPOINT, time_range)
    top_tracks_response = requests.get(TOP_TRACKS_ENDPOINT, headers=auth_header)
    top_tracks_data = json.loads(top_tracks_response.text)
    return top_tracks_data

# ------------- Playlist Requests -------------
# Define Playlists API endpoint
MY_PLAYLISTS_ENDPOINT = "{}/me/playlists".format(SPOTIFY_API_URL)

def create_playlist(auth_header, user_id, playlist_name, playlist_description):
    CREATE_PLAYLIST_ENDPOINT = "{}/users/{}/playlists".format(SPOTIFY_API_URL, user_id)
    header = {}
    header.update(auth_header)
    header["Content-Type"] = "application/json"
    data = {
        "name" : playlist_name,
        "description" : playlist_description
    }
    new_playlist_response = requests.post(CREATE_PLAYLIST_ENDPOINT, headers=header, data=json.dumps(data))
    new_playlist_data = json.loads(new_playlist_response.text)
    return new_playlist_data


#def add_playlist_items(auth_header, track_uris):



def get_my_playlists(auth_header):
    my_playlists_response = requests.get(MY_PLAYLISTS_ENDPOINT, headers=auth_header)
    my_playlists_data = json.loads(my_playlists_response.text)
    return my_playlists_data


def get_all_my_playlists(auth_header):
    # Define All Playlists API endpoint
    ALL_MY_PLAYLISTS_ENDPOINT = "{}/me/playlists?limit=50".format(SPOTIFY_API_URL)
    all_playlists_response = requests.get(ALL_MY_PLAYLISTS_ENDPOINT, headers=auth_header)
    all_playlists_data = json.loads(all_playlists_response.text)
    all_playlist_container = [all_playlists_data["items"]]
    while all_playlists_data["next"] != None:
        temp_response = requests.get(all_playlists_data["next"], headers=auth_header)
        all_playlists_data = json.loads(temp_response.text)
        all_playlist_container.append(all_playlists_data["items"])
    return all_playlist_container


def get_playlist_items(auth_header, playlist_id):
    # Define Playlist API endpoint
    PLAYLIST_ENDPOINT = "{}/playlists/{}/tracks".format(SPOTIFY_API_URL, playlist_id)
    # Define access fields
    #FIELDS = "name,tracks.next,tracks.items(track(artists(name), duration_ms, name, popularity)), tracks.total"
    #PLAYLIST_FIELDS_ENDPOINT = "{}?fields={}".format(PLAYLIST_ENDPOINT, FIELDS)
    playlist_response = requests.get(PLAYLIST_ENDPOINT, headers=auth_header)
    playlist_data = json.loads(playlist_response.text)
    playlist_container = [playlist_data["items"]]
    while playlist_data["next"] != None:
        temp_response = requests.get(playlist_data["next"], headers=auth_header)
        playlist_data = json.loads(temp_response.text)
        playlist_container.append(playlist_data["items"])
    return playlist_container


def get_playlist_name(auth_header, playlist_id):
    PLAYLIST_ENDPOINT = "{}/playlists/{}".format(SPOTIFY_API_URL, playlist_id)
    FIELDS = "name"
    PLAYLIST_FIELDS_ENDPOINT = "{}?fields={}".format(PLAYLIST_ENDPOINT, FIELDS)
    playlist_response = requests.get(PLAYLIST_ENDPOINT, headers=auth_header)
    playlist_data = json.loads(playlist_response.text)
    return playlist_data["name"]


# ------------- Player Requests -------------
# Define recently played tracks API endpoint
RECENTLY_PLAYED_ENDPOINT = "{}/me/player/recently-played".format(SPOTIFY_API_URL)

def recently_played_tracks(auth_header):
    recently_played_response = requests.get(RECENTLY_PLAYED_ENDPOINT, headers=auth_header)
    recently_played_data = json.loads(recently_played_response.text)
    return recently_played_data


# ------------- Track Requests -------------
# Define Tracks API endpoint
TRACKS_ENDPOINT = "{}/tracks".format(SPOTIFY_API_URL)
FEATURES_ENDPOINT = "{}/audio-features".format(SPOTIFY_API_URL)
ANALYSIS_ENDPOINT = "{}/audio-analysis".format(SPOTIFY_API_URL)

def get_track(auth_header, track_id):
    TRACK_ENDPOINT = "{}/{}".format(TRACKS_ENDPOINT, track_id)
    track_response = requests.get(TRACK_ENDPOINT, headers=auth_header)
    track_data = json.loads(track_response.text)
    return track_data


def get_features(auth_header, track_id):
    TRACK_FEATURES_ENDPOINT = "{}/{}".format(FEATURES_ENDPOINT, track_id)
    features_response = requests.get(TRACK_FEATURES_ENDPOINT, headers=auth_header)
    features_data = json.loads(features_response.text)
    return features_data


def get_analysis(auth_header, track_id):
    TRACK_ANALYSIS_ENDPOINT = "{}/{}".format(ANALYSIS_ENDPOINT, track_id)
    analysis_response = requests.get(TRACK_ANALYSIS_ENDPOINT, headers=auth_header)
    analysis_data = json.loads(analysis_response.text)
    return analysis_data


# ------------- Artist Requests -------------
# Define Artist API endpoint
ARTISTS_ENDPOINT = "{}/artists".format(SPOTIFY_API_URL)

def get_top_tracks(auth_header, artist_id):
    # Define endpoint specific country (from token)
    ARTIST_TOP_TRACKS_ENDPOINT = "{}/{}/top-tracks?country=from_token".format(ARTISTS_ENDPOINT, artist_id)
    artists_top_tracks_response = requests.get(ARTIST_TOP_TRACKS_ENDPOINT, headers=auth_header)
    artists_top_tracks_data = json.loads(artists_top_tracks_response.text)
    return artists_top_tracks_data


def get_artist(auth_header, artist_id):
    # Define endpoint for specific artist
    ARTIST_ENDPOINT = "{}/{}".format(ARTISTS_ENDPOINT, artist_id)
    artist_response = requests.get(ARTIST_ENDPOINT, headers=auth_header)
    artist_data = json.loads(artist_response.text)
    return artist_data


# ------------- Search Requests -------------
# Define Search API endpoint
SEARCH_ENDPOINT = "{}/search".format(SPOTIFY_API_URL)

def search_tracks(auth_header, queries):
    keywords = queries.replace(" ", "%20")
    # Search query with limit 30
    SEARCH_TRACK_ENDPOINT = "{}?q={}&type=track&limit=30".format(SEARCH_ENDPOINT, keywords)
    tracks_response = requests.get(SEARCH_TRACK_ENDPOINT, headers=auth_header)
    tracks_data = json.loads(tracks_response.text)
    return tracks_data


def search_artists(auth_header, queries):
    keywords = queries.replace(" ", "%20")
    # Search query with limit 30
    SEARCH_ARTIST_ENDPOINT = "{}?q={}&type=artist&limit=30".format(SEARCH_ENDPOINT, keywords)
    artists_response = requests.get(SEARCH_ARTIST_ENDPOINT, headers=auth_header)
    artists_data = json.loads(artists_response.text)
    return artists_data
