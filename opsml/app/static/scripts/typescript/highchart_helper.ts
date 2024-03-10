Highcharts.setOptions({
    colors: ['#04b78a', "#5e0fb7", "#bdbdbd", "#009adb", "#e74c3c", "#e73c3c", "#f2cc35"],
  });
  
function get_plot_options(graph_style) {
var plot_options = {};
if (graph_style == "line") {
    plot_options = {
    series: {
        states: {
        inactive: {
            opacity: 1
            }
        },
        lineWidth: 3,
        animation: false,
        marker: {
        enabled: false,
        },
    }
    };
} else if (graph_style == "scatter"){
    plot_options = {
    series: {
        states: {
        inactive: {
            opacity: 1
            }
        },
        marker: {
        enabled: true,
        radius: 3,
        },
        animation: false
    }
    };
}
return plot_options;
}

function build_xy_chart(graph) {

var name = graph["name"];
var x_label = graph["x_label"];
var y_label = graph["y_label"];
var x = graph["x"];
var y = graph["y"];
var chart_name="graph_" + name;
var graph_style = graph["graph_style"];
var plot_options = get_plot_options(graph_style);

Highcharts.chart(chart_name, {
    chart: {
        type: graph_style,
        borderColor:'#390772',
        borderWidth: 2,
        shadow: true
    },
    title: {
        text: name,
        align: 'left'
    },

    xAxis: {
        labels: {
        format: '{value:.1f}',
        tickInterval: 5
    },
        categories: x,
        allowDecimals: false,
        title: {
        text: x_label
    },
    lineWidth: 1,
    },

    yAxis: {
        labels: {
        format: '{value:.1f}',
        step: 1
    },
        title: {
            text: y_label
        },
    lineWidth: 1,
    tickLength: 10,
    tickWidth: 1
    },

    series: [{data: y,}],
    plotOptions: plot_options,
    credits: {
    enabled: false
    },
});
}

function get_y_series(y_keys, y) {
var y_series = [];
for (var i = 0; i < y_keys.length; i++) {
    y_series.push({
    name: y_keys[i],
    data: y[y_keys[i]],
    });
}
return y_series;

}


function build_multixy_chart(graph) {

var name = graph["name"];
var x_label = graph["x_label"];
var y_label = graph["y_label"];
var x = graph["x"];
var y = graph["y"];
var y_keys = Object.keys(y);
var chart_name="graph_" + name;
var y_series = get_y_series(y_keys, y);
var graph_style = graph["graph_style"];
var plot_options = get_plot_options(graph_style);


Highcharts.chart(chart_name, {
    chart: {
    type: graph_style,
    borderColor:'#390772',
    borderWidth: 2,
    shadow: true
    },
    title: {
        text: name,
        align: 'left'
    },

    xAxis: {
        labels: {
        format: '{value:.1f}',
        tickInterval: 5
    },
        categories: x,
        allowDecimals: false,
        title: {
        text: x_label
    },
    lineWidth: 1,
    },

    yAxis: {
        labels: {
        format: '{value:.1f}',
        step: 1
    },
    title: {
            text: y_label
        },
    lineWidth: 1,
    tickLength: 10,
    tickWidth: 1
    },

    series: y_series,
    plotOptions: plot_options,

    credits: {
    enabled: false
    },

    legend: {
    align: 'left',
    verticalAlign: 'top',
    borderWidth: 0
},
    tooltip: {
    shared: true,
    crosshairs: true
},
});

}
