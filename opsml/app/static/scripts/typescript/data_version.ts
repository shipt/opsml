import $ from 'jquery';
import * as Prism from 'prismjs';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-python';
import showdown from 'showdown';

interface CardMetadata {
  description: {
    summary: string;
    sample_code: string;
  };
  feature_map: {[key: string]: string};
  interface_type: string;
  data_type: string;
}

interface Card {
  name: string;
  repository: string;
  version: string;
  uid: string;
  data_filename: string;
  data_profile_filename: string;
  profile_uri: string;
  metadata: CardMetadata;
    interface: {
        dependent_vars: string[];
        feature_descriptions: {[key: string]: string};
        sql_logic: {[key: string]: string};
    };
}

interface Data {
  card: Card;
  data_splits: string;
  data_filename: string;
  profile_uri: string;
  data_profile_filename: string;

}

function insertDataMetadata(data: Data, datacard: Card, metadata: CardMetadata) {
  document.getElementById('metadata-interface').innerHTML = metadata.interface_type;
  document.getElementById('metadata-type').innerHTML = metadata.data_type;

  // insert data
  const dataUri: HTMLElement = document.getElementById('data-uri');
  dataUri.setAttribute('href', `/opsml/data/download?uid=${datacard.uid}`);
  dataUri.setAttribute('download', data.data_filename);

  if (data.profile_uri !== null) {
    const profileUri: HTMLElement = document.getElementById('data-profile-uri');
    profileUri.setAttribute('href', `/opsml/data/download/profile?uid=${datacard.uid}`);
    profileUri.setAttribute('download', data.data_profile_filename);
    $('#data-profile').show();
  }

  // set metadata button
  // summary-button on click
  document.getElementById('metadata-button').onclick = function metaButtonClick() {
    $('#CardBox').show();
    $('#ExtraBox').show();
    $('#SummaryBox').hide();
    $('#ProfileBox').hide();
    $(this).addClass('active');
  };
}

function insertDataExtras(data: Data, datacard: Card, metadata: CardMetadata) {
  if (data.data_splits !== null) {
    $('#split-button').show();
    const code: string = data.data_splits;
    const html: string = Prism.highlight(code, Prism.languages.json, 'json');
    document.getElementById('DataSplitCode').innerHTML = html;

    document.getElementById('split-button').onclick = function splitClick() {
      $('#Splits').toggle();
    };
  }

  // set depen vars
  const dataInterface: Card['interface'] = datacard.interface;

  // check if interface has dependent vars
  if (Object.hasOwn(dataInterface, 'dependent_vars')) {
    // check if interface has dependent vars
    if (dataInterface.dependent_vars.length > 0) {
      $('#dep-var-button').show();
      const depenVar: HTMLElement = document.getElementById('depen-var-body');
      depenVar.innerHTML = '';

      for (let i = 0; i < dataInterface.dependent_vars.length; i += 1) {
        const depVar: string = dataInterface.dependent_vars[i];
        depenVar.innerHTML += `
                <tr>
                    <td>${depVar}</td>
                </tr>
                `;
      }

      document.getElementById('dep-var-button').onclick = function depVarClick() {
        $('#DependentVars').toggle();
      };
    }
  }

  // set feature_map
  const featureMap: {[key: string]: string;} = metadata.feature_map;

  // check if feature_map keys > 0
  if (Object.keys(featureMap).length > 0) {
    $('#feature-map-button').show();
    const featureBody: HTMLElement = document.getElementById('feature-map-body');
    featureBody.innerHTML = '';

    Object.keys(featureMap).forEach((key) => {
      const value: string = featureMap[key];
      featureBody.innerHTML += `
        <tr>
            <td><font color="#999">${key}</font></td>
            <td>${value}</td>
        </tr>
        `;
    });

    document.getElementById('feature-map-button').onclick = function featMapToggle() {
      $('#FeatureMap').toggle();
    };
  }

  // set feature descriptions

  if (Object.hasOwn(dataInterface, 'feature_descriptions')) {
    const featDesc: {[key:string]: string} = dataInterface.feature_descriptions;

    // check if feature_descriptions keys > 0
    if (Object.keys(featDesc).length > 0) {
      $('#feature-desc-button').show();
      const featureDescBody: HTMLElement = document.getElementById('feature-desc-body');
      featureDescBody.innerHTML = '';

      Object.keys(featDesc).forEach((key) => {
        const value: string = featDesc[key];
        featureDescBody.innerHTML += `
            <tr>
                <td><font color="#999">${key}</font></td>
                <td>${value}</td>
            </tr>
            `;
      });

      document.getElementById('feature-desc-button').onclick = function featDescToggle() {
        $('#FeatureDesc').toggle();
      };
    }
  }

  // set sql
  if (Object.hasOwn(dataInterface, 'sql_logic')) {
    const sqlLogic: {[key: string]: string;} = dataInterface.sql_logic;

    if (Object.keys(sqlLogic).length > 0) {
      $('#sql-button').show();
      const sqlDiv: HTMLElement = document.getElementById('sql-div');
      sqlDiv.innerHTML = '';

      Object.keys(sqlLogic).forEach((key) => {
        const value: string = sqlLogic[key];

        const htmlLogic = Prism.highlight(value, Prism.languages.sql, 'sql');
        sqlDiv.innerHTML += `
                <h6><i style="color:#04b78a"></i> <font color="#999">${key}</font>
                <clipboard-copy for="${key}Code">
                    Copy
                    <span class="notice" hidden>Copied!</span>
                </clipboard-copy>
                </h6>
                <pre style="max-height: 500px; overflow: scroll;"><code id="${key}Code">${htmlLogic}</code></pre>
                `;
      });

      document.getElementById('sql-button').onclick = function sqlToggle() {
        $('#SQL').toggle();
      };
    }
  }
}

function insertSummary(datacard: Card, metadata: CardMetadata) {
  if (metadata.description.summary !== null) {
    const converter = new showdown.Converter();
    converter.setFlavor('github');
    const text: string = converter.makeHtml(metadata.description.summary);
    document.getElementById('summary-markdown').innerHTML = text;
    $('#summary-display').show();
    $('#SummaryText').hide();
  } else {
    $('#summary-display').hide();
    $('#SummaryText').show();
  }

  if (metadata.description.sample_code !== null) {
    const code: string = metadata.description.sample_code;
    const html:string = Prism.highlight(code, Prism.languages.python, 'python');
    document.getElementById('user-sample-code').innerHTML = html;
    $('SampleCode').show();
  } else {
    $('#SampleCode').hide();
  }

  const opsmlCode: string = `
    from opsml import CardRegistry

    data_registry = CardRegistry("data")
    datacard = model_registry.load_card(
        name="${datacard.name}", 
        repository="${datacard.repository}",
        version="${datacard.version}",
    )
    datacard.load_data()
    `;

  const html: string = Prism.highlight(opsmlCode, Prism.languages.python, 'python');
  document.getElementById('opsml-sample-code').innerHTML = html;

  // summary-button on click
  document.getElementById('summary-button').onclick = function summaryToggle() {
    $('#CardBox').hide();
    $('#ExtraBox').hide();
    $('#ProfileBox').hide();
    $('#SummaryBox').show();
    $(this).addClass('active');
  };
}

function insertHtmlIframe(data) {
  if (data.profile_uri !== null) {
    $('#data-profile-button').show();
    const htmlIframe: HTMLElement = document.getElementById('data-profile-html');
    htmlIframe.setAttribute('src', data.profile_uri);
  }

  // profile-button on click
  document.getElementById('data-profile-button').onclick = function profileToggle() {
    $('#CardBox').hide();
    $('#ExtraBox').hide();
    $('#SummaryBox').hide();
    $('#ProfileBox').show();
    $(this).addClass('active');
  };
}

function buildDataVersionUI(data: Data) {
  const datacard: Card = data.card;
  const { metadata } = datacard;

  insertDataMetadata(data, datacard, metadata);
  insertDataExtras(data, datacard, metadata);
  insertSummary(datacard, metadata);
  insertHtmlIframe(data);
}

export { buildDataVersionUI, Data, Card }; // eslint-disable-line import/prefer-default-export
