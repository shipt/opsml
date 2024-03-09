function buildBarChart (name, metrics) {

    Highcharts.setOptions({
        colors: ['#04b78a', "#5e0fb7", "#bdbdbd", "#009adb"],
    });

    var scores = [];
    var metricNames = Object.keys(metrics);


    // iterate over metricsNames
    for (var i = 0; i < metricNames.length; i++) {
        let y = metrics[metricNames[i]]["y"];
        scores.push(y[y.length - 1]);
    }

    // get min and max values for y axis across all metrics
    // if min is greater than 0 set to 0
    // add padding to max
    let minyValue = Math.min(Math.min(...scores), 0);

    Highcharts.chart('MetricChart', {
        chart: {
          type: 'column',
          plotBackgroundColor: null,
          plotBorderWidth: null,
          plotShadow: false,
          height: (9 / 16 * 90) + '%',
        },
        title: {
          text: `Metrics for ${name}`,
          align: 'left'
        },
      
        xAxis: {
            type: 'category',
            categories: metricNames,
            lineWidth: 1,
        },
        yAxis: {
          min: minyValue,
          title: {
            text: 'Metric Value)'
          },
            lineWidth: 1,
            tickLength: 10,
            tickWidth: 1
        },
        legend: {
            enabled: true
        },
        plotOptions: {
            series: {
                borderWidth: 1,
                borderColor: 'black'
            }
        },
        series: [
            {
                name: 'Metrics',
                colorByPoint: true,
                data: scores,
                colors: ['#04b78a', "#5e0fb7", "#bdbdbd", "#009adb"],
                pointPadding: 0,
        
            }
        ],
        plotOptions: {
            series: {
              states: {
                inactive: {
                    opacity: 1
                  }
                },
              lineWidth: 3,
            }
        },
    });

}

function buildLineChart (name, metrics) {
    Highcharts.setOptions({
        colors: ['#04b78a', "#5e0fb7", "#bdbdbd", "#009adb"],
    });

    var metricNames = Object.keys(metrics);

    var data = [];
    // iterate over metricsNames
    for (var i = 0; i < metricNames.length; i++) {

        var points = [];
        let y = metrics[metricNames[i]]["y"];
        let x = metrics[metricNames[i]]["x"];

        for (var j = 0; j < x.length; j++) {
            points.push([x[j] || 1 , y[j]]);
        }

        data.push({
            name: metricNames[i],
            data: points,
            marker: {
                enabled: false,
              },
        });
    }

    Highcharts.chart('MetricChart', {
        chart: {
          type: 'line',
          height: (9 / 16 * 90) + '%',
        },
        title: {
          text: `Metrics for ${name}`,
          align: 'left'
        },
      
        xAxis: {
            type: 'category',
            title: {
                text: 'Step'
              },
              lineWidth: 1,
        },
        yAxis: {
          title: {
            text: 'Value'
          },
            lineWidth: 1,
            tickLength: 10,
            tickWidth: 1
        },
        legend: {
            enabled: true
        },
     
        series: data,
        plotOptions: {
            series: {
              states: {
                inactive: {
                    opacity: 1
                  }
                },
              lineWidth: 3,
            }
        },
    });


}

export { buildBarChart, buildLineChart };