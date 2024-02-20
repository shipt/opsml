import Highcharts from "https://code.highcharts.com/highcharts.js";

Highcharts.setOptions({
    colors: ['#04b78a', "#5e0fb7", "#bdbdbd", "#009adb"],
});

function build_bar_chart (metrics, selected_metrics) {
    var scores = [];
    for (var i = 0; i < selected_metrics.length; i++) {

        var metric = metrics[selected_metrics[i]];
        var last_metric = metric[metric.length - 1]
        scores.push(last_metric["value"]);
        
    };

    // get min and max values for y axis across all metrics
    // if min is greater than 0 set to 0
    // add padding to max
    minyValue = Math.min(Math.min(...scores), 0);
    maxyValue = Math.max(...scores) * 1.1;

    
    Highcharts.chart('MetricChart', {
        chart: {
          type: 'column'
        },
        title: {
          text: 'Metrics for {{ runcard["name"] }}',
          align: 'left'
        },
      
        xAxis: {
            type: 'category',
            categories: selected_metrics,
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

function build_line_chart(metrics, selected_metrics) {

    
  
    var data = [];
    for (var i = 0; i < selected_metrics.length; i++) {

        var metric = metrics[selected_metrics[i]];

    
        var points = [];

        for (var j = 0; j < metric.length; j++) {
            var curr_metric = metric[j];
            points.push([curr_metric["step"] || 1, curr_metric["value"]]);
        }

        data.push({
            name: selected_metrics[i],
            data: points,
            marker: {
                enabled: false,
              },
        });
    };

  

    Highcharts.chart('MetricChart', {
        chart: {
          type: 'line'
        },
        title: {
          text: 'Metrics for {{ runcard["name"] }}',
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

export { build_bar_chart, build_line_chart };