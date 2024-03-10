import Highcharts from 'highcharts';

Highcharts.setOptions({
    colors: ['#04b78a', "#5e0fb7", "#bdbdbd", "#009adb", "#e74c3c", "#e73c3c", "#f2cc35"],
  });

interface Graph {
    name: string;
    x_label: string;
    y_label: string;
    x: string[];
    y: string[];
    graph_style: string;
}
  
function getPlotOptions(graph_style:string) {
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

function buildXyChart(graph: Graph) {

var name = graph["name"];
var x_label = graph["x_label"];
var y_label = graph["y_label"];
var x = graph["x"];
var y = graph["y"];
var chart_name="graph_" + name;
var graph_style = graph["graph_style"];
var plot_options = getPlotOptions(graph_style);

Highcharts.chart( {
    chart: {
        type: graph_style,
        borderColor:'#390772',
        borderWidth: 2,
        shadow: true,
        renderTo: chart_name
    },
    title: {
        text: name,
        align: 'left'
    },

    xAxis: {
        labels: {
        format: '{value:.1f}',
        // @ts-expect-error
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

    // @ts-expect-error
    series: [{data: y,}],
    plotOptions: plot_options,
    credits: {
    enabled: false
    },
});
}

function getYSeries(y_keys, y) {
    var y_series = [];
    for (var i = 0; i < y_keys.length; i++) {
        // @ts-expect-error
        y_series.push({
        name: y_keys[i],
        data: y[y_keys[i]],
        });
    }
    return y_series;

}


function buildMultiXyChart(graph: Graph) {

var name = graph["name"];
var x_label = graph["x_label"];
var y_label = graph["y_label"];
var x = graph["x"];
var y = graph["y"];
var y_keys = Object.keys(y);
var chart_name="graph_" + name;
var y_series = getYSeries(y_keys, y);
var graph_style = graph["graph_style"];
var plot_options = getPlotOptions(graph_style);


Highcharts.chart({
    chart: {
    type: graph_style,
    borderColor:'#390772',
    borderWidth: 2,
    shadow: true,
    renderTo: chart_name
    },
    title: {
        text: name,
        align: 'left'
    },

    xAxis: {
        labels: {
        format: '{value:.1f}',

        // @ts-expect-error
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

    // @ts-expect-error
    crosshairs: true
},
});

}
