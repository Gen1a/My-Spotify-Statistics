# My Spotify Statistics
<<<<<<< HEAD
![Banner](static/images/Banner.png)
=======
>>>>>>> d20f8162f0ce5c840a1c42496f1e1093e2866573
My first own side-project (and final project for HarvardX CS50) where I, try to, dive straight into the world of Web Programming. I decided to make a web application which interacts with the Spotify Web API and enables you to analyse your **Spotify 'footprint'**, look up **analysis for any track or own playlist**. As an added bonus I included a tool which automatically **creates a unique playlist** in your Spotify account, based on the top 10 tracks of the artists you like to include in the playlist.

*Note: this web application is built responsively, although viewing it on PC is recommended for UX due to high usage of tables*

## Features

- **Profile Overview**
  - Your display name, user-id, followers, followed, artists, subscription, saved tracks, recently played tracks...
- **Playlist Overview**
  - Total tracks, owner...
- **Track and Playlist Analytics**
  - Danceability, Energy, Speechiness, Acousticness, Valence, Tempo...
- **User Statistics**
  - Top Tracks, Top Artists, Top Genres (on short, middle and long term)
- **Party Planner**
  - Creates a playlist based on the top tracks of of your party guests's top artists
- **Running Tool (under development)**
  - Creates a playlist in 1 or more specific genre(s) based on your required beats per minute (bpm) running cadence
  
## User Authentication
Authentication is done through [User Authentication with OAuth2.0](https://oauth.net/articles/authentication/) with the Authorization Code Flow.
![Authorization Code Flow](https://developer.spotify.com/assets/AuthG_AuthoriztionCode.png)
*Note: handling of refresh tokens for extended sessions (> 60mins) has **not yet been implemented**. Due to the nature of this web application this will not result in any problems for users trying out the app for short periods of time.*
  
  ## Technologies & Frameworks
  - Python (Flask, Matplotlib)
  - HTML, CSS (Bootstrap)
<<<<<<< HEAD
  - Javascript (mostly jQuery)
=======
  - Javascript (jQuery)
>>>>>>> d20f8162f0ce5c840a1c42496f1e1093e2866573
