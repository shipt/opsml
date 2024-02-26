const LIST_CARD_PATH = "/opsml/cards/list";

function get_versions(registry, name, repository, version) {
    var list_data = {"registry_type": registry, "repository": repository, "name": name, "version": version};


    $.ajax({
        url: LIST_CARD_PATH,
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(list_data),
        success: function(data) {

            //alert(JSON.stringify(data));
          
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
          }
    });

}


//function to get version pages
// this could be in it's own separate file
function set_version_page(registry, repository, name) {

    // hide repository page
    //$("#repository-page").hide();
    // display version page
    //document.getElementById("version-page").style.display = "block";
    // hide repository page and show version page
    $("#repository-page").hide();


    document.getElementById("version-header").innerHTML = name;
    get_versions(registry, name, repository);
    $("#version-page").show();

}

export {set_version_page};