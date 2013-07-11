$.getJSON('{{ graph_data_url }}', function(data) {

    var requests = data.requests;
    var responses = data.responses;

    // helper for returning the weekends in a period

    function weekendAreas(axes) {

        var markings = [],
            requests = new Date(axes.xaxis.min);

        // go to the first Saturday

        requests.setUTCDate(requests.getUTCDate() - ((requests.getUTCDay() + 1) % 7))
        requests.setUTCSeconds(0);
        requests.setUTCMinutes(0);
        requests.setUTCHours(0);

        var i = requests.getTime();

        // when we don't set yaxis, the rectangle automatically
        // extends to infinity upwards and downwards

        do {
            markings.push({ xaxis: { from: i, to: i + 2 * 24 * 60 * 60 * 1000 } });
            i += 7 * 24 * 60 * 60 * 1000;
        } while (i < axes.xaxis.max);

        return markings;
    }

    var options = {
        xaxis: {
            mode: "time",
            tickLength: 1
        },
        grid: {
            markings: weekendAreas
        },
        series: {
            lines: { show: true },
            points: { show: true }
        },
        legend: {show: true}
    };

    var plot = $.plot("#placeholder", [{label: "Appels à la hotline", data:requests},
                                       {label: "Rappels par la hotline", data:responses}], options);

});
