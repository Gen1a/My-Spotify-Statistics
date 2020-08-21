// jQuery code to which loads all tooltips
$(document).ready(function () {
    // Loads all tooltips
    $('[data-toggle="tooltip"]').tooltip();
    // Hide alerts
    $('.alert').hide();
    // Show modal + ask confirmation when trying to log out
    $('#navbar-logout').on("click", function (e) {
        $('#modal').modal('show');
        $('#modal-title').text("Log Out");
        $('#modal-body').text("Are you sure you want to log out?");
        // Add confirm button to modal footer and change cancel button text
        $('#modal-cancel').text("No");
        $('#modal-confirm').removeClass("hidden");
    })
    // Makes bootstrap table rows clickable
    //$(".clickable-row").on("click", function (e, row, $element) {
    //    window.location = $(this).data('href');
    //});
    // Adds DataTables features to webpage
    $('.datatable-overview').DataTable();
    // Adds loading spinners to login and analytics buttons
    $('.track-analytics-button').on("click", function () {
        $(this).closest('td').html('<div class="spinner-border text-success disabled" role="status"><span class="sr-only"></span></div>');
    });
    $('.loader-button').on("click", function () {
        $(this).html('<div class="spinner-border text-success disabled" role="status"><span class="sr-only"></span></div>');
        $('#modal').modal('show');
        $('#modal-title').text("Playlist Analytics");
        $('#modal-body').text("Loading may take up to a minute, depending on magnitude of the playlist.");
    });
    $('#login-button').on("click", function () {
        $(this).html('<div class="spinner-border text-success disabled" role="status"><span class="sr-only"></span></div>');
    });
    // Change href of anchor element depending on selected playlist
    $('#playlist_overview').on("change", function () {
        playlist_id = $(this).find(":selected").val();
        var playlist_url = "/playlist-analytics%3Fplaylist_id%3D" + playlist_id;
        $('#selected_playlist').attr("href", playlist_url);
    });
    // Link form enter button to click event of button
    $(document).keypress(function (event) {
        if (event.which == '13') {
            event.preventDefault();
            $('#artist-search').click();
        }
    });
    // Party planner tool
    $('#artist-search').on("click", function () {
        var artist = $('#artist-name').val();
        // Check if input entered
        if (artist == "") {
            // Show alert message
            $('.alert').alert();
            $('#alert-message').text("Please enter an artist name.");
            $(".alert").fadeTo(2000, 500).slideUp(500, function () {
                $(".alert").slideUp(500);
            });
        }
        // Remove search button focused outline
        if (document.activeElement.toString() == '[object HTMLButtonElement]') {
            document.activeElement.blur();
        };
        // Request search query for type artist
        $.ajax({
            url: "/request",
            method: "GET",
            data: {
                type: "artist",
                query: artist
            },
            success: function (response) {
                // Delete container content, if any
                $("#imagerow").empty();
                // Show search results container
                $('#search-results-grid').removeClass("hidden");
                $('#search-results-info').text('Search results for: "' + artist + '"');
                // If no results found
                if (response.artists.total == 0)
                    $("#imagerow").html("<div class='col'>No results found</div>");
                //console.log(response);
                // Loop through AJAX response
                $.each(response.artists.items, function (index, artist) {
                    // Create new artist image
                    var thumbnail = $("<img>").addClass("rounded-circle mx-auto d-block");
                    if (typeof artist.images[0] === 'undefined' || artist.images[0] === null) {
                        thumbnail.attr("src", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png");
                    }
                    else {
                        thumbnail.attr("src", artist.images[0].url);
                    }
                    thumbnail.attr({
                        width: 125,
                        height: 125,
                        alt: artist.name
                    });
                    // Create new col for grid
                    var column = $("<div>").addClass("col");
                    // Create new card
                    var card = $("<div>").addClass("card pt-1 mb-2");
                    card.attr({
                        "style": "width: 9.5rem;",
                        "data-artist-id": artist.id
                    });
                    card.append(thumbnail);
                    var card_body = $("<div>").addClass("card-body text-center");
                    var card_title = $("<a>").addClass("card-title stretched-link").text(artist.name);
                    // Add card into column div
                    card.append(card_body.append(card_title));
                    // Add click event to cards
                    card.on("click", function () {
                        $("#generate-playlist").removeClass("hidden");
                        $('#selected-placeholder').remove();
                        var card_copy = card.clone();
                        var artist_id = card_copy[0].dataset.artistId;
                        var col = $("<div>").addClass("col");
                        col.append(card_copy);
                        // Check if artist is already selected
                        var selection = $("#artist-selection").find(".card");
                        var add = true;
                        for (i = 0; i < selection.length; i++) {
                            var check = selection[i].dataset.artistId;
                            if (check == artist_id) {
                                add = false;
                            }
                        }
                        // Add artist to selection
                        if (add) {
                            // Add remove event to card
                            col.on("click", function () {
                                this.remove();
                                // Check whether an artist remains
                                let selection_element = $('#artist-selection').find(".card");
                                if (selection_element.length == 0) {
                                    $('#generate-playlist').addClass("hidden");
                                }
                                // Show alert message
                                $('.alert').alert();
                                $('#alert-message').text("Artist removed");
                                $(".alert").fadeTo(2000, 500).slideUp(500, function () {
                                    $(".alert").slideUp(500);
                                });
                            })
                            $("#artist-selection").append(col);
                        }
                        // Artist already selected
                        else {
                            // Show modal message
                            $('#modal').modal('show');
                            $('#modal-title').text("Sorry");
                            $('#modal-body').text("This artist is already added. Give other artists some love as well!");
                        }
                    })
                    column.append(card);
                    $("#imagerow").append(column);
                })
            },
            error: function () {
                console.log("failed");
            }
        });
    });
    // Generate Party Playlist
    $('#generate-playlist').on("click", function () {
        // Add loading spinner to button and reset back to normal
        var old_html = $('#generate-playlist').html();
        $('#generate-playlist').html('<div class="spinner-border text-success disabled" role="status"><span class= "sr-only">Loading...</span></div>');
        setTimeout(function () { $('#generate-playlist').html(old_html); }, 7000);
        // Collect selected artist ids
        let selection_element = $('#artist-selection').find(".card");
        // Save artist ids
        let selection_ids = [];
        for (i = 0; i < selection_element.length; i++) {
            selection_ids.push(selection_element[i].dataset.artistId);
        }
        //console.log(selection_ids);
        // Clear previous table data
        $('#partyplanner-table-body').empty();
        // Request playlist 
        $.ajax({
            url: "/request",
            method: "GET",
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            data: {
                type: "generate-playlist",
                query: JSON.stringify(selection_ids)
            },
            success: function (response) {
                // Hide selected artists and search results grid
                $('#search-results-grid').addClass("hidden");
                // Show created playlist overview
                $('#partyplanner-overview').removeClass("hidden");
                // Show modal with information
                $('#modal').modal('show');
                $('#modal-title').text("Playlist generated");
                $('#modal-body').text("Great! You can now check out your unique playlist's audio features and playlist content.");
                // Calculate amount of columns
                columns = $('#playlist-tab-content').find("th").length;              
                // Playlist info
                var trackCounter = 1;
                let playlistDuration = 0;
                let uri_counter = 0
                // Construct table body with nested loop (artist > top tracks)
                $.each(response.top_tracks, function () {
                    // Loop through each track in response
                    for (let i = 0; i < this.tracks.length; i++) {
                        var row = $("<tr>");
                        // Store track uri in table
                        row.attr('data-track-uri', response.tracks_uris[uri_counter++]);                   
                        // Loop through each row's columns
                        for (let j = 0; j < columns; j++) {
                            var td = $("<td>").addClass("align-middle text-center");
                            switch (j) {
                                case 0:
                                    td.text(trackCounter++);
                                    break;
                                case 1:
                                    td.text(this.tracks[i].name);
                                    break;
                                case 2:
                                    td.text(this.tracks[i].artists[0].name);
                                    break;
                                case 3:
                                    // Convert milliseconds to m:ss notation
                                    let minutes = this.tracks[i].duration_ms / 60000.0;
                                    playlistDuration += minutes;
                                    if (minutes > 1.0) {
                                        seconds = minutes % Math.floor(minutes) * 60.0;
                                    }
                                    // if track is less than 1 minute long
                                    else {
                                        seconds = minutes * 60.0;
                                    }
                                    if (seconds < 10) {
                                        let s = "0" + Math.floor(seconds);
                                        td.text(Math.floor(minutes) + ":" + s);
                                    }
                                    else {
                                        td.text(Math.floor(minutes) + ":" + Math.floor(seconds));
                                    }
                                    break;
                                case 4:
                                    td.text(this.tracks[i].popularity);
                                    break;
                                default:
                                    console.log("Playlist creation failed.");
                            }
                            row.append(td);
                            $('#partyplanner-table-body').append(row);
                        }                
                    }    
                })
                // Construct Partyplanner playlist info
                $('#partyplanner-info').empty();
                function formatDuration(duration) {
                    let hours = Math.floor(duration / 60);
                    if (hours > 0){
                        minutes = duration - (hours * 60);
                        return hours + (hours > 1 ? " hours " : " hour ") + Math.floor(minutes) + " minutes";
                    }
                    else
                        return Math.floor(duration) + " minutes";
                }
                var infoElement = '<div class="row align-items-center"><div class="col-12 col-md-6">' +
                    '<div class="small-content-block text-center"><img src="data:image/png;base64,' + response.url + '" class="img-fluid features" alt="playlist features" /></div></div>' +
                    '<div class="col-12 col-md-6">' +
                    '<ul class="list-group list-group-analytics my-2">' +
                    '<li class="list-group-item">Amount of tracks<span class="badge badge-pill float-right">' + (trackCounter - 1) + '</span></li>' +
                    '<li class="list-group-item">Playlist Duration<span class="badge badge-pill float-right">' + formatDuration(playlistDuration) + '</span></li>' +
                    '<li class="list-group-item">Top Genres<span class="badge badge-pill float-right">' + response.top_genres[0][0] + (typeof (response.top_genres[1]) === "undefined" ? "" : " & ") + (typeof (response.top_genres[1]) === "undefined" ? "" : response.top_genres[1][0]) + '</span></li>' +
                    '<li class="list-group-item" data-toggle="tooltip" data-placement="top" title="Danceability describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A value of 0.0 is least danceable and 1.0 is most danceable.">Danceability <i class="gg-info"></i><span class="badge badge-pill float-right">' + response.features_data.danceability.toFixed(3) + '</span></li>' +
                    '<li class="list-group-item" data-toggle="tooltip" data-placement="top" title="Energy is a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy, while a Bach prelude scores low on the scale. Perceptual features contributing to this attribute include dynamic range, perceived loudness, timbre, onset rate, and general entropy.">Energy<i class="gg-info"></i><span class="badge badge-pill float-right">' + response.features_data.energy.toFixed(3) + '</span></li>' +
                    '<li class="list-group-item" data-toggle="tooltip" data-placement="top" title="Speechiness detects the presence of spoken words in a track. The more exclusively speech-like the recording (e.g. talk show, audio book, poetry), the closer to 1.0 the attribute value. Values above 0.66 describe tracks that are probably made entirely of spoken words. Values between 0.33 and 0.66 describe tracks that may contain both music and speech, either in sections or layered, including such cases as rap music. Values below 0.33 most likely represent music and other non-speech-like tracks.">Speechiness<i class="gg-info"></i><span class="badge badge-pill float-right">' + response.features_data.speechiness.toFixed(3) + '</span></li>' +
                    '<li class="list-group-item" data-toggle="tooltip" data-placement="top" title="A measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry).">Valence<i class="gg-info"></i><span class="badge badge-pill float-right">' + response.features_data.valence.toFixed(3) + '</span></li>' + 
                    '<li class="list-group-item">Tempo<span class="badge badge-pill float-right">' + response.features_data.tempo.toFixed(0) + ' bpm</span></li>' + 
                    '</ul ></div>';
                $('#partyplanner-info').append(infoElement);
                // Reload all tooltips
                $('[data-toggle="tooltip"]').tooltip();
            },
            error: function () {
                console.log("AJAX Request Failed.");
            }
        });
    });
    // Create Party Playlist in Spotify Account
    $('#create-playlist').on("click", function () {
        // Get playlist name and description
        var playlistName = $('#playlist-name').val();
        if (playlistName == "") {
            // Show alert message
            $('.alert').alert();
            $('#alert-message').text("Please enter a name for your playlist.");
            $(".alert").fadeTo(2000, 500).slideUp(500, function () {
                $(".alert").slideUp(500);
            });
            return false;
        }
        var playlistDescription = $('#playlist-description').val();
        // Get all track uris and store in array
        var track_uris_elements = $('#playlist-tab-content').find('[data-track-uri]');
        var track_uris = []
        for (i = 0; i < track_uris_elements.length; i++) {
            track_uris.push(track_uris_elements[i].dataset.trackUri)
        }
        // Send data in POST request (GET request has limited characters depending on browser)
        $.ajax({
            url: "/request",
            method: "POST",
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            data: JSON.stringify({
                "uris": JSON.stringify(track_uris),
                "name": playlistName,
                "description": playlistDescription
            }),
            success: function (response) {
                $('#modal').modal('show');
                $('#modal-title').text("Playlist created");
                var modal_body_content = "<p>Check out your Spotify account or click the link below to find your new Party Playlist and share it with friends!</p>";
                modal_body_content += '<a class="btn btn-sm" id="playlist-url" href="' + response + '" target="_blank"><i class="gg-share"></i>Link to playlist</a>';
                $('#modal-body').html(modal_body_content);
            },
            error: function () {
                $('#modal').modal('show');
                $('#modal-title').text("Sorry");
                $('#modal-body').text("Hmm, something went wrong :( Please contact the site owner to report the bug.");
            }
        });
    });
});
