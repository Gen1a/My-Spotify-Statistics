# CS50 Final Project Ideas

### Strava Web App
###### A simple web application which enables you to look up and analyse your Strava 'footprint'.

- Total activities
- Total distance per sport
- Distance per week and per year (cumulative)
- Trips around the world / to the moon
- Heart rate statistics
- Elevation statistics
- Total year statistics
- Overview of activities (date, name, time, average pace, distance...)

### Spotify Web App
###### A simple web application which enables you to look up and analyse your Spotify 'footprint'.
- Example: https://musicaldata.com/
- Web Player
- Analytics
- Best of 2017, 2018, 2019...

**Features**
- App Authorization through Spotify's Authorization Code Flow [(link to documentation)](https://developer.spotify.com/documentation/general/guides/authorization-guide/#authorization-code-flow)
- Long running application where user grants permission once and access token can be refreshed
	- **Prompt** user to wepbage where they can choose to grant access
	- Receive **access token** and **refresh token**
![Authorization Code Flow](https://developer.spotify.com/assets/AuthG_AuthoriztionCode.png)

**Notes**
- Spotify Web API endpoints return data in JSON-format
- When a collection of objects is returned and the number of objects is **variable**, the collection is wrapped in a **paging object** to simplify retrieval of further objects

**To Do**

- Info tooltips on hover
- 


