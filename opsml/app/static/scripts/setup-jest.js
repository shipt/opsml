// this is needed because imports like this do not work for vanilla javascript
// putting these imports in the specific.ts file will create unusable js when compiled
import $ from 'jquery';
import * as Prism from 'prismjs';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-python';
import showdown from 'showdown';
import * as Highcharts from 'highcharts';
global.$ = $;
global.jQuery = $;
global.Prism = Prism;
global.showdown = showdown;
global.Highcharts = Highcharts;