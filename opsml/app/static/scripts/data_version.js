function insert_data_metadata(data, datacard, metadata) {
    

    document.getElementById("metadata-interface").innerHTML = metadata["interface_type"];
    document.getElementById("metadata-type").innerHTML = metadata["data_type"];

    // insert data
    let data_uri = document.getElementById("data-uri");
    data_uri.href = `/opsml/data/download?uid=${datacard["uid"]}`;
    data_uri.setAttribute("download", data["data_filename"]);

    if (data["profile_uri"] !== null ) {
        let profile_uri = document.getElementById("data-profile-uri");
        profile_uri.href = `/opsml/data/download/profile?uid=${datacard["uid"]}`;
        profile_uri.setAttribute("download", data["data_profile_filename"]);
        $("#data-profile").show();
    }


}

function insert_data_extras(data, datacard, metadata) {


    if (data["data_splits"] !== null) {
        $("#split-button").show();
        let code = data["data_splits"];
        let html = Prism.highlight(code, Prism.languages.json, 'json');
        document.getElementById("DataSplitCode").innerHTML = html;

        document.getElementById("split-button").onclick = function() {
            $("#Splits").toggle();
        }
    }

    // set depen vars
    let data_interface = datacard["interface"];

    // check if interface has dependent vars
    if (Object.hasOwn(data_interface, "dependent_vars")) {

        //check if interface has dependent vars
        if (data_interface["dependent_vars"].length > 0) {
            $("#dep-var-button").show();
            let depen_var = document.getElementById("depen-var-body");
            depen_var.innerHTML = "";

            for (let i = 0; i < data_interface["dependent_vars"].length; i++) {
                let _var = data_interface["dependent_vars"][i];
                depen_var.innerHTML += `
                <tr>
                    <td>${_var}</td>
                </tr>
                `
            }

            document.getElementById("dep-var-button").onclick = function() {
                $("#DependentVars").toggle();
            }
        }
    } 
    

    // set feature_map
    let feature_map = metadata["feature_map"];

    // check if feature_map keys > 0
    if (Object.keys(feature_map).length > 0) {
        $("#feature-map-button").show();
        let feature_body = document.getElementById("feature-map-body");
        feature_body.innerHTML = "";
        for (let key in feature_map) {
            let value = feature_map[key];
            feature_body.innerHTML += `
            <tr>
                <td><font color="#999">${key}</font></td>
                <td>${value}</td>
            </tr>
            `
        }

        document.getElementById("feature-map-button").onclick = function() {
            $("#FeatureMap").toggle();
        }
    }

    // set feature descriptions

    if (Object.hasOwn(data_interface, "feature_descriptions")) {

        let feature_descriptions = data_interface["feature_descriptions"];

        // check if feature_descriptions keys > 0
        if (Object.keys(feature_descriptions).length > 0) {
            $("#feature-desc-button").show();
            let feature_desc_body = document.getElementById("feature-desc-body");
            feature_desc_body.innerHTML = "";
            for (let key in feature_descriptions) {
                let value = feature_descriptions[key];
                feature_desc_body.innerHTML += `
                <tr>
                    <td><font color="#999">${key}</font></td>
                    <td>${value}</td>
                </tr>
                `
            }

            document.getElementById("feature-desc-button").onclick = function() {
                $("#FeatureDesc").toggle();
            }
        }
    }

    // set sql 
    if (Object.hasOwn(data_interface, "sql_logic")) {
        let sql_logic = data_interface["sql_logic"];

        if (Object.keys(sql_logic).length > 0) {
            $("#sql-button").show();
            let sql_div = document.getElementById("sql-div");
            sql_div.innerHTML = "";
            for (let key in sql_logic) {
                let value = sql_logic[key];

                let html_logic = Prism.highlight(value, Prism.languages.sql, 'sql');
                sql_div.innerHTML +=  `
                <h6><i style="color:#04b78a"></i> <font color="#999">${key}</font>
                <clipboard-copy for="${key}Code">
                    Copy
                    <span class="notice" hidden>Copied!</span>
                </clipboard-copy>
                </h6>
                <pre style="max-height: 500px; overflow: scroll;"><code id="${key}Code">${html_logic}</code></pre>
                `
            }

            document.getElementById("sql-button").onclick = function() {
                $("#SQL").toggle();
            }
        }

    }


    // check if sql is not null

    




}

function build_data_version_ui(data) {

    let datacard = data["card"];
    let metadata = datacard["metadata"];

    insert_data_metadata(data, datacard, metadata);
    insert_data_extras(data, datacard, metadata);

}

export { build_data_version_ui };