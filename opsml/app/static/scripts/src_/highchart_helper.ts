import Highcharts from 'highcharts';
import 'highcharts/modules/exporting';
import 'highcharts/modules/export-data';
import 'highcharts/modules/boost';
import 'highcharts/modules/accessibility';
import 'highcharts/modules/series-label';

Highcharts.setOptions({
  colors: ['#04b78a', '#5e0fb7', '#bdbdbd', '#009adb', '#e74c3c', '#e73c3c', '#f2cc35'],
});

interface Graph {
    name: string;
    x_label: string;
    y_label: string;
    x: string[];
    y: string[];
    graph_style: string;
}

function getPlotOptions(graphStyle:string) {
  let PlotOptions;

  if (graphStyle === 'line') {
    PlotOptions = {
      series: {
        states: {
          inactive: {
            opacity: 1,
          },
        },
        lineWidth: 3,
        animation: false,
        marker: {
          enabled: false,
        },
      },
    };
  } else if (graphStyle === 'scatter') {
    PlotOptions = {
      series: {
        states: {
          inactive: {
            opacity: 1,
          },
        },
        marker: {
          enabled: true,
          radius: 3,
        },
        animation: false,
      },
    };
  }

  return PlotOptions;
}

function buildXyChart(graph: Graph) {
  const { name } = graph;
  const xLabel = graph.x_label;
  const yLabel = graph.y_label;
  const { x } = graph;
  const { y } = graph;
  const chartName = `graph_${name}`;
  const graphStyle = graph.graph_style;
  const plotOptions = getPlotOptions(graphStyle);

  Highcharts.chart({
    chart: {
      type: graphStyle,
      borderColor: '#390772',
      borderWidth: 2,
      shadow: true,
      renderTo: chartName,
    },
    title: {
      text: name,
      align: 'left',
    },

    xAxis: {
      labels: {
        format: '{value:.1f}',
        // @ts-expect-error: skipping
        tickInterval: 5,
      },
      categories: x,
      allowDecimals: false,
      title: {
        text: xLabel,
      },
      lineWidth: 1,
    },

    yAxis: {
      labels: {
        format: '{value:.1f}',
        step: 1,
      },
      title: {
        text: yLabel,
      },
      lineWidth: 1,
      tickLength: 10,
      tickWidth: 1,
    },

    // @ts-expect-error: skipping
    series: [{ data: y }],
    plotOptions,
    credits: {
      enabled: false,
    },
  });
}

function getYSeries(yKeys, y) {
  const ySeries = [];
  for (let i = 0; i < yKeys.length; i += 1) {
    ySeries.push({
      name: yKeys[i],
      data: y[yKeys[i]],
    });
  }
  return ySeries;
}

function buildMultiXyChart(graph: Graph) {
  const { name } = graph;
  const xLabel = graph.x_label;
  const yLabel = graph.y_label;
  const { x } = graph;
  const { y } = graph;
  const yKeys = Object.keys(y);
  const chartName = `graph_${name}`;
  const ySeries = getYSeries(yKeys, y);
  const graphStyle = graph.graph_style;
  const plotOptions = getPlotOptions(graphStyle);

  Highcharts.chart({
    chart: {
      type: graphStyle,
      borderColor: '#390772',
      borderWidth: 2,
      shadow: true,
      renderTo: chartName,
    },
    title: {
      text: name,
      align: 'left',
    },

    xAxis: {
      labels: {
        format: '{value:.1f}',

        // @ts-expect-error: skipping
        tickInterval: 5,
      },
      categories: x,
      allowDecimals: false,
      title: {
        text: xLabel,
      },
      lineWidth: 1,
    },

    yAxis: {
      labels: {
        format: '{value:.1f}',
        step: 1,
      },
      title: {
        text: yLabel,
      },
      lineWidth: 1,
      tickLength: 10,
      tickWidth: 1,
    },

    series: ySeries,
    plotOptions,

    credits: {
      enabled: false,
    },

    legend: {
      align: 'left',
      verticalAlign: 'top',
      borderWidth: 0,
    },
    tooltip: {
      shared: true,

      // @ts-expect-error: skipping
      crosshairs: true,
    },
  });
}

function buildBarChart(name, metrics) {
  Highcharts.setOptions({
    colors: ['#04b78a', '#5e0fb7', '#bdbdbd', '#009adb'],
  });

  const scores = [];
  const metricNames = Object.keys(metrics);

  // iterate over metricsNames
  for (let i = 0; i < metricNames.length; i += 1) {
    const { y } = metrics[metricNames[i]];
    scores.push(y[y.length - 1]);
  }

  // get min and max values for y axis across all metrics
  // if min is greater than 0 set to 0
  // add padding to max
  const minyValue = Math.min(Math.min(...scores), 0);

  Highcharts.chart({
    chart: {
      type: 'column',
      plotBackgroundColor: null,
      plotBorderWidth: null,
      plotShadow: false,
      height: `${(9 / 16) * 90}%`,
      renderTo: 'MetricChart',
    },
    title: {
      text: `Metrics for ${name}`,
      align: 'left',
    },

    xAxis: {
      type: 'category',
      categories: metricNames,
      lineWidth: 1,
    },
    yAxis: {
      min: minyValue,
      title: {
        text: 'Metric Value)',
      },
      lineWidth: 1,
      tickLength: 10,
      tickWidth: 1,
    },
    legend: {
      enabled: true,
    },
    plotOptions: {
      series: {
        borderWidth: 1,
        borderColor: 'black',
        states: {
          inactive: {
            opacity: 1,
          },
        },
        lineWidth: 3,
      },
    },
    series: [
      {
        name: 'Metrics',
        colorByPoint: true,
        data: scores,
        colors: ['#04b78a', '#5e0fb7', '#bdbdbd', '#009adb'],
        pointPadding: 0,
        type: 'column',

      },
    ],
  });
}

function buildLineChart(name, metrics) {
  Highcharts.setOptions({
    colors: ['#04b78a', '#5e0fb7', '#bdbdbd', '#009adb'],
  });

  const metricNames = Object.keys(metrics);

  const data = [];
  // iterate over metricsNames
  for (let i = 0; i < metricNames.length; i += 1) {
    const points = [];
    const { y } = metrics[metricNames[i]];
    const { x } = metrics[metricNames[i]];

    for (let j = 0; j < x.length; j += 1) {
      points.push([x[j] || 1, y[j]]);
    }

    data.push({
      name: metricNames[i],
      data: points,
      marker: {
        enabled: false,
      },
    });
  }

  Highcharts.chart({
    chart: {
      type: 'line',
      height: `${(9 / 16) * 90}%`,
      renderTo: 'MetricChart',
    },
    title: {
      text: `Metrics for ${name}`,
      align: 'left',
    },

    xAxis: {
      type: 'category',
      title: {
        text: 'Step',
      },
      lineWidth: 1,
    },
    yAxis: {
      title: {
        text: 'Value',
      },
      lineWidth: 1,
      tickLength: 10,
      tickWidth: 1,
    },
    legend: {
      enabled: true,
    },

    series: data,
    plotOptions: {
      series: {
        states: {
          inactive: {
            opacity: 1,
          },
        },
        lineWidth: 3,
      },
    },
  });
}

export {
  buildXyChart, buildMultiXyChart, buildBarChart, buildLineChart,
};
