function insert_model_metadata(data, datacard, metadata) {
    
    
    document.getElementById("metadata-interface").innerHTML = datacard["metadata"]["interface_type"];
    document.getElementById("metadata-type").innerHTML = datacard["metadata"]["data_type"];

    if (metadata.onnx_uri !== null ) {
        let onnx_uri = document.getElementById("onnx-uri");
        onnx_uri.href = `/opsml/files/download/ui?path=${metadata.onnx_uri}`;
        onnx_uri.setAttribute("download", data["onnx_filename"]);
        $("#onnx-uri-display").show();
    } else {
        $("#onnx-uri-display").hide();
    }
}

function build_model_version_ui(data) {
    let modelcard = data["card"];
    let metadata = JSON.parse(data["metadata"]);

    

}

export { build_data_version_ui };