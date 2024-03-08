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

export { buildBarChart };