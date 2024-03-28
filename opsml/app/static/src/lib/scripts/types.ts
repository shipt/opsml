type record = [string, string, number, number, number, number];

export interface registryPage {
  page: record[];
}

export interface registryStats {
  nbr_names: number;
  nbr_versions: number;
  nbr_repos: number;
}

export interface repositories {
  repositories: string[];
}

export interface metadataRequest {
  repository: string;
  name: string;
  version?: string;
}

export interface ModelMetadata {
  model_name: string;
  model_class: string;
  model_type: string;
  model_interface: string;
  onnx_uri: string;
  onnx_version: string;
  model_uri: string;
  model_version: string;
  model_repository: string;
  opsml_version: string;
  data_schema: string;
  preprocessor_uri?: string;
  preprocessor_name?: string;
  quantized_model_uri?: string;
  tokenizer_uri?: string;
  tokenizer_name?: string;
  feature_extractor_uri?: string;
  feature_extractor_name?: string;
}
