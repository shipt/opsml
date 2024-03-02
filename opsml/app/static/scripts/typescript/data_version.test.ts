import { exportAllDeclaration } from '@babel/types'; // eslint-disable-line @typescript-eslint/no-unused-vars
import { buildDataVersionUI, Data } from './data_version';

// write test for buildDataVersionUI
test('test-buildDataVersionUI', () => {
  // Set up our document body
  document.body.innerHTML = `
    <div class="card-body">
        <h4>Data
        <div id="CardTabBox">
            <span><button id="download-button" type="submit" class="btn btn-success" >Metadata</button></span>
            <span><button id="download-button" type="submit" class="btn btn-success" >Summary</button></span>
            <span><button id="download-button" type="submit" class="btn btn-success focus" >Data Profile</button></span>
        </div>
        </h4>
    </div>

    <div class="card-body">
        <h4>Data
            <div id="CardTabBox">
            <button id="metadata-button" type="submit" class="btn btn-success">Metadata</button>
            <button id="summary-button" type="submit" class="btn btn-success">Summary</button>
            <button id="data-profile-button" type="submit" class="btn btn-success" style="display: none;">Data Profile</button>
            </div>
        </h4>
    </div>

    <div class="card-body" id="CardButtons" >
        <button id="split-button" type="submit" class="btn btn-success" style="display: none;">Splits</button>
        <button id="dep-var-button" type="submit" class="btn btn-success" style="display: none;">Dependent Vars</button>
        <button id="feature-map-button" type="submit" class="btn btn-success" style="display: none;">Feature Map</button>
        <button id="feature-desc-button" type="submit" class="btn btn-success" style="display: none;">Feature Descriptions</button>
        <button id="sql-button" type="submit" class="btn btn-success" style="display: none;">SQL</button>
    </div>

    <div id="metadata-interface"></div>
    <div id="metadata-type"></div>
    <div id="data-uri"></div>
    <div id="data-profile" style="display: none;">
        <div id="data-profile-uri"></div>
    </div>
    <div id="CardBox"></div>
    <div id="ExtraBox"></div>
    <div id="ProfileBox">
        <div id="data-profile-html"></div>
    </div>
    <div id="SummaryBox">
        <div id="summary-markdown"></div>
        <div id="summary-display"></div>
        <div id="SummaryText"></div>
        <div id="user-sample-code"></div>
        <div id="SampleCode"></div>
        <div id="opsml-sample-code"></div>
    </div>
    <div id="DependentVars">
        <div id="depen-var-body"></div>
    </div>
    <div id="Splits">
        <div id="DataSplitCode"></div>
    </div>
    <div id="FeatureMap">
        <div id="feature-map-body"></div>
    </div>
    <div id="FeatureDesc">
        <div id="feature-desc-body"></div>
    </div>
    <div id="SQL">
        <div id="sql-div"></div>
    </div>
    `;

  const fakeData = ({
    card: {
      name: 'test',
      repository: 'test',
      version: 'test',
      uid: 'test',
      interface: {
        dependent_vars: ['test'],
        feature_descriptions: {
          var1: 'var1',
          var2: 'var2',
        },
        sql_logic: 'SELECT * FROM TEST',
      },
      metadata: {
        interface_type: 'test',
        data_type: 'test',
        description: {
          summary: 'test',
          sample_code: 'test',
        },
        feature_map: {
          var1: 'string',
          var2: 'int',
        },
      },

    },
    data_filename: 'test',
    profile_uri: 'test',
    data_profile_filename: 'test',
    data_splits: '{"hello": "world"}',

  } as unknown) as Data;

  buildDataVersionUI(fakeData);
  expect(document.getElementById('metadata-interface')?.innerHTML).toBe('test');
  expect(document.getElementById('metadata-type')?.innerHTML).toBe('test');
  expect(document.getElementById('data-uri')?.getAttribute('href')).toBe(`/opsml/data/download?uid=${fakeData.card.uid}`);
  expect(document.getElementById('data-profile-uri')?.getAttribute('href')).toBe(`/opsml/data/download/profile?uid=${fakeData.card.uid}`);
  expect(document.getElementById('DataSplitCode')?.innerHTML).not.toBe('');
  expect(document.getElementById('depen-var-body')?.innerHTML).not.toBe('');
  expect(document.getElementById('feature-map-body')?.innerHTML).not.toBe('');
  expect(document.getElementById('feature-desc-body')?.innerHTML).not.toBe('');
  expect(document.getElementById('sql-div')?.innerHTML).not.toBe('');
  expect(document.getElementById('summary-markdown')?.innerHTML).toBe('<p>test</p>');
  expect(document.getElementById('opsml-sample-code')?.innerHTML).not.toBe('');
  expect(document.getElementById('data-profile-html')?.getAttribute('src')).toBe('test');
});
