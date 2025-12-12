$(document).ready(function(){

    $("#start").select2({
        placeholder: "Select a start station",
        ajax: {
            url: "/get_stations",
            dataType: "json",
            delay: 250,
            data: function (parameters) {
                return { search: parameters.term };
            },
            processResults: function (data) {
                return { results: data };
            },
            cache: true
        }
    });

    $("#end").select2({
        placeholder: "Select an end station",
        ajax: {
            url: "/get_stations",
            dataType: "json",
            delay: 250,
            data: function (parameters) {
                return { search: parameters.term };
            },
            processResults: function (data) {
                return { results: data };
            },
            cache: true
        }
    });
});