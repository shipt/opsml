

import showdown from 'showdown';
import * as Prism from 'prismjs';

import 'prismjs/components/prism-json';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-python';

interface CardMetadata {
    description: {
        summary: string;
        sample_code: string;
    };
}

interface Card {
    name: string;
    repository: string;
    version: string;
    datacard_uid: string;
    metadata: CardMetadata ;
}

interface ModelMetadata {
    model_interface: string;
    model_type: string;
    onnx_uri: string;
    model_uri: string;
}

interface ProcessorUris {
    preprocessor: {
        filename: string;
        rpath: string;
    };
    tokenizer: {
        filename: string;
        rpath: string;
    };
    feature_extractor: {
        filename: string;
        rpath: string;
    };
}

interface ArtifactUris {
    remote_path: string;
}

interface Runcard {
    uid: string;
    tags: {[key: string]: string};
    parameters: {[key: string]: [{value: string}]};
    artifact_uris: {[key: string]: ArtifactUris};
}

interface Data {
    card: Card;
    metadata: string;
    onnx_filename: string;
    model_filename: string;
    processor_uris: ProcessorUris;
    runcard: Runcard;
  }

function insertModelMetadata(data: Data, modelcard: Card, metadata: ModelMetadata) {
  document.getElementById('metadata-interface')!.innerHTML = metadata.model_interface;
  document.getElementById('metadata-type')!.innerHTML = metadata.model_type;

  // check if onnx_uri exists
  if (metadata.onnx_uri !== null) {
    const onnxUri: HTMLElement = document.getElementById('onnx-uri')!;
    onnxUri.setAttribute('href', `/opsml/files/download/ui?path=${metadata.onnx_uri}`);
    onnxUri.setAttribute('download', data.onnx_filename);
    $('#onnx-uri-display').show();
  } else {
    $('#onnx-uri-display').hide();
  }

  // insert trained model
  const modelUri: HTMLElement = document.getElementById('model-uri')!;
  modelUri.setAttribute('href', `/opsml/files/download/ui?path=${metadata.model_uri}`);
  modelUri.setAttribute('download', data.model_filename);

  // check preprocessor
  if (data.processor_uris.preprocessor.filename !== null) {
    const preprocessorUri: HTMLElement = document.getElementById('preprocessor-uri')!;
    preprocessorUri.setAttribute('href', `/opsml/files/download/ui?path=${data.processor_uris.preprocessor.rpath}`);
    preprocessorUri.setAttribute('download', data.processor_uris.preprocessor.filename);
    $('#preprocessor-uri-display').show();
  } else {
    $('#preprocessor-uri-display').hide();
  }

  // check tokenizer
  if (data.processor_uris.tokenizer.filename !== null) {
    const tokenizerUri: HTMLElement = document.getElementById('tokenizer-uri')!;
    tokenizerUri.setAttribute('href', `/opsml/files/download/ui?path=${data.processor_uris.tokenizer.rpath}`);
    tokenizerUri.setAttribute('download', data.processor_uris.tokenizer.filename);
    $('#tokenizer-uri-display').show();
  } else {
    $('#tokenizer-uri-display').hide();
  }

  if (data.processor_uris.feature_extractor.filename !== null) {
    const extractorUri: HTMLElement = document.getElementById('feature-extractor-uri')!;
    extractorUri.setAttribute('href', `/opsml/files/download/ui?path=${data.processor_uris.feature_extractor.rpath}`);
    extractorUri.setAttribute('download', data.processor_uris.feature_extractor.filename);
    $('#feature-extractor-uri-display').show();
  } else {
    $('#feature-extractor-uri-display').hide();
  }

  // auditcard
  const auditLink: HTMLElement = document.getElementById('audit-link')!;
  auditLink.setAttribute('href', `/opsml/audit/?repository=${modelcard.repository}&model=${modelcard.name}&version=${modelcard.version}`);

  if (modelcard.datacard_uid !== null) {
    const datacardLink: HTMLElement = document.getElementById('datacard-link')!;
    datacardLink.setAttribute('href', `/opsml/ui?registry=data&uid=${modelcard.datacard_uid}`);
    $('#datacard-uid-display').show();
  } else {
    $('#datacard-uid-display').hide();
  }

  if (data.runcard !== null) {
    const runcardLink: HTMLElement = document.getElementById('runcard-link')!;
    runcardLink.setAttribute('href', `/opsml/ui?registry=run&uid=${data.runcard.uid}`);
    $('#runcard-uid-display').show();
  } else {
    $('#runcard-uid-display').hide();
  }

  // set metadata button
  // summary-button on click
  document.getElementById('metadata-button')!.onclick = function metaToggle() {
    $('#CardBox').show();
    $('#TagBox').show();
    $('#ExtraBox').show();
    $('#SummaryBox').hide();
    $(this).addClass('active');
  };
}

// insert tags into the model card ui
// data: card data from ajax response
function insertModelTags(data: Data) {
  const { runcard } = data;
  if (runcard !== null) {
    if (Object.keys(data.runcard.tags).length > 0) {
      const modelTagBody: HTMLElement = document.getElementById('tag-body')!;
      modelTagBody.innerHTML = '';

      Object.keys(data.runcard.tags).forEach((name) => {
        const value: string = data.runcard.tags[name];
        modelTagBody.innerHTML += `
                <tr>
                    <td><font color="#999">${name}:</font></td>
                    <td>${value}</td>
                </tr>
                `;
      });
    }
  } else {
    const modelTagBody: HTMLElement = document.getElementById('tag-body')!;
    modelTagBody.innerHTML = '';
    modelTagBody.innerHTML += '<tr><td><font color="#999">None</font></td><tr>';
  }
}

function insertModelExtras(data: Data) {
  // hide extra buttons
  $('#Params').hide();
  $('#MetadataJson').hide();

  const { runcard } = data;

  if (runcard !== null) {
    // check params
    if (Object.keys(runcard.parameters).length > 0) {
      const paramBody: HTMLElement = document.getElementById('param-body')!;
      paramBody.innerHTML = '';

      Object.keys(data.runcard.parameters).forEach((name) => {
        const value: [{'value': string}] = data.runcard.parameters[name];
        paramBody.innerHTML += `
                <tr>
                    <td><font color="#999">${name}</font></td>
                    <td>${value[0].value}</td>
                </tr>
                `;
      });

      // show Params on click
      document.getElementById('param-button')!.onclick = function paramToggle() {
        $('#Params').toggle();
      };
      $('#param-button').show();
    } else {
      $('#param-button').hide();
    }

    // check artifacts
    if (Object.keys(runcard.artifact_uris).length > 0) {
      const artifactBody: HTMLElement = document.getElementById('artifact-uris')!;
      artifactBody.innerHTML = '';

      Object.keys(runcard.artifact_uris).forEach((name) => {
        const value: ArtifactUris = runcard.artifact_uris[name];
        const pathParts: string[] = value.remote_path.split('/');
        const downloadName: string = pathParts[pathParts.length - 1];

        artifactBody.innerHTML += `
                <tr>
                    <td><font color="#999">${name}</font></td>
                    <td>
                        <a href="/opsml/files/download?path=${value.remote_path}" download='${downloadName}'>
                        <button id="download-button" type="submit" class="btn btn-success">Download</button>
                        </a>
                    </td>
                </tr>
                `;
      });

      // show artifacts on click
      document.getElementById('artifact-button')!.onclick = function artifactToggle() {
        $('#Artifacts').toggle();
      };
      $('#artifact-button').show();
    } else {
      $('#artifact-button').hide();
    }
  } else {
    $('#param-button').hide();
    $('#artifact-button').hide();
  }

  const code: string = data.metadata;
  const html: string = Prism.highlight(code, Prism.languages.json, 'json');
  document.getElementById('MetadataCode')!.innerHTML = html;

  document.getElementById('metadata-extra-button')!.onclick = function extraToggle() {
    $('#MetadataJson').toggle();
  };
}

function insertModelSummary(modelcard: Card) {
  const cardMetadata: CardMetadata = modelcard.metadata;

  if (cardMetadata.description.summary !== null) {
    const converter = new showdown.Converter();
    converter.setFlavor('github');
    const text: string = converter.makeHtml(cardMetadata.description.summary);
    document.getElementById('summary-markdown')!.innerHTML = text;
    $('#summary-display').show();
    $('#SummaryText').hide();
  } else {
    $('#summary-display').hide();
    $('#SummaryText').show();
  }

  if (cardMetadata.description.sample_code !== null) {
    const code: string = cardMetadata.description.sample_code;
    const html: string = Prism.highlight(code, Prism.languages.python, 'python');
    document.getElementById('user-sample-code')!.innerHTML = html;
    $('SampleCode').show();
  } else {
    $('#SampleCode').hide();
  }

  const opsmlCode: string = `
    from opsml import CardRegistry

    model_registry = CardRegistry("model")
    modelcard = model_registry.load_card(
        name="${modelcard.name}", 
        repository="${modelcard.repository}",
        version="${modelcard.version}",
    )
    modelcard.load_model() # load the train model
    `;

  const html: string = Prism.highlight(opsmlCode, Prism.languages.python, 'python');
  document.getElementById('opsml-sample-code')!.innerHTML = html;

  // summary-button on click
  document.getElementById('summary-button')!.onclick = function summaryToggle() {
    $('#CardBox').hide();
    $('#TagBox').hide();
    $('#ExtraBox').hide();
    $('#SummaryBox').show();
    $(this).addClass('active');
  };
}

function buildModelVersionUI(data: Data) {
  const modelcard: Card = data.card;
  const metadata: ModelMetadata = JSON.parse(data.metadata);

  insertModelMetadata(data, modelcard, metadata);
  insertModelTags(data);
  insertModelExtras(data);
  insertModelSummary(modelcard);
}

export { buildModelVersionUI, Data, Card }; // eslint-disable-line
