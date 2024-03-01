import { buildModelVersionUI } from "./model_version";

test('test-buildModelVersionUI', () => {


    // Set up our document body
  document.body.innerHTML = `
  <div class="card-body">
      <h4>Data
      <div id="CardTabBox">
        <button id="metadata-button" type="button" class="btn btn-success" >Metadata</button>
        <button id="summary-button" type="button" class="btn btn-success">Summary</button>
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
  <button id="metadata-extra-button" type="submit" class="btn btn-success" >Metadata</button>
  <button id="param-button" style="display: none;" type="submit" class="btn btn-success" >Params</button>
  <button id="artifact-button" style="display: none;" type="submit" class="btn btn-success" >Artifacts</button>
    </div>

  <div id="metadata-interface"></div>
  <div id="metadata-type"></div>
  <div id="onnx-uri"></div>
  <div id="model-uri" style="display: none;"></div>
  <div id="preprocessor-uri"></div>
  <div id="tokenizer-uri"></div>
  <div id="feature-extractor-uri"></div>
  <div id="datacard-link"></div>
  <div id="runcard-link"></div>
  <div id="MetadataCode"></div>
  <div id="param-body"></div>
  <div id="tag-body"></div>
  <div id="artifact-uris"></div>
  <div id="audit-link"></div>
  <div id="CardBox"></div>
  <div id="ExtraBox"></div>
  <div id="SummaryBox">
      <div id="summary-markdown"></div>
      <div id="summary-display"></div>
      <div id="SummaryText"></div>
      <div id="user-sample-code"></div>
      <div id="SampleCode"></div>
      <div id="opsml-sample-code"></div>
  </div>
  `

  let fakeData = {
    "card": {
      "name": "test",
      "repository": "test",
      "version": "test",
      "uid": "test",
      "datacard_uid": "test",
      "metadata": {
        "description": {
          "summary": "test", 
          "sample_code": "test"
        }
      },
    },
    "metadata":JSON.stringify({
        "model_interface": "test",
        "model_type": "test",
        "onnx_uri": "test",
        "model_uri": "test",
    }),
    "onnx_filename": "test",
    "model_filename": "test",
    "processor_uris": {
      "preprocessor": 
        {
          "filename": "test",
          "rpath" : "test"
        },
      "tokenizer" :{
        "filename": "test",
        "rpath" : "test"
      },
      "feature_extractor" :{
        "filename": "test",
        "rpath" : "test"
      }
    },
    "runcard": {
      "uid": "test",
      "tags": {"var1": "var1"},
      "parameters": {"var1": [{"value": "test"}]},
      "artifact_uris": {"var1": {"remote_path": "test/test.txt"}},
    }
    }
  buildModelVersionUI(fakeData)
  expect(document.getElementById('metadata-interface')?.innerHTML).toBe('test');
  expect(document.getElementById('metadata-type')?.innerHTML).toBe('test');
  expect(document.getElementById('onnx-uri')?.getAttribute('href')).toBe(`/opsml/files/download/ui?path=test`);
  expect(document.getElementById('model-uri')?.getAttribute('href'))?.toBe(`/opsml/files/download/ui?path=test`);
  expect(document.getElementById('preprocessor-uri')?.getAttribute('href')).toBe(`/opsml/files/download/ui?path=${fakeData.processor_uris.preprocessor.rpath}`);
  expect(document.getElementById('tokenizer-uri')?.getAttribute('href')).toBe(`/opsml/files/download/ui?path=${fakeData.processor_uris.tokenizer.rpath}`);
  expect(document.getElementById('feature-extractor-uri')?.getAttribute('href')).toBe(`/opsml/files/download/ui?path=${fakeData.processor_uris.feature_extractor.rpath}`);
  expect(document.getElementById('datacard-link')?.getAttribute('href')).toBe(`/opsml/ui?registry=data&uid=test`);
  expect(document.getElementById('runcard-link')?.getAttribute('href')).toBe(`/opsml/ui?registry=run&uid=test`);
  expect(document.getElementById('tag-body')?.innerHTML).not.toBe('');
  expect(document.getElementById('param-body')?.innerHTML).not.toBe('');
  expect(document.getElementById('artifact-uris')?.innerHTML).not.toBe('');
  expect(document.getElementById('MetadataCode')?.innerHTML).not.toBe('');
  expect(document.getElementById('summary-markdown')?.innerHTML).not.toBe('');
  expect(document.getElementById('user-sample-code')?.innerHTML).not.toBe('');
  expect(document.getElementById('opsml-sample-code')?.innerHTML).not.toBe('');

});