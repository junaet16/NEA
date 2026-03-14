// Ensure the page DOM is fully loaded before running any JavaScript
$(document).ready(function(){

    /* Start Station Dropdown (Select2) */

    // Initialise Select2 for the start station input field
    $("#start").select2({

        // Placeholder text shown before the user selects a station
        placeholder: "Select a start station",

        // Configure AJAX-based searching for station names
        ajax: {
            // Backend endpoint that returns matching station names
            url: "/get_stations",

            // Expected response format
            dataType: "json",

            // Delay to prevent excessive requests while typing
            delay: 250,

            // Send the user's search term to the backend
            data: function (parameters) {
                return { search: parameters.term };
            },

            // Convert the backend response into Select2-compatible results
            processResults: function (data) {
                return { results: data };
            },

            // Cache results to improve performance and reduce server load
            cache: true
        }
    });


    /* End Station Dropdown (Select2) */

    // Initialise Select2 for the end station input field
    $("#end").select2({

        // Placeholder text shown before the user selects a station
        placeholder: "Select an end station",

        // Configure AJAX-based searching for station names
        ajax: {
            // Backend endpoint that returns matching station names
            url: "/get_stations",

            // Expected response format
            dataType: "json",

            // Delay to prevent excessive requests while typing
            delay: 250,

            // Send the user's search term to the backend
            data: function (parameters) {
                return { search: parameters.term };
            },

            // Convert the backend response into Select2-compatible results
            processResults: function (data) {
                return { results: data };
            },

            // Cache results to improve performance and reduce server load
            cache: true
        }
    });
});