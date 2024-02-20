

// Function to get data and content type
// type: type of request
// path_data: data to be passed to the function
function get_data_and_content_type(type,path_data) {

    if (type == "POST") {
        let request_data = JSON.stringify(path_data);
        let content_type = "application/json";
        return request_data, content_type;
    } else {
        let request_data = path_data;
        let content_type = "application/x-www-form-urlencoded";
        return request_data, content_type;
    }
}


// Function to generate html from data
// path: path to the function that generates the html
// path_data: data to be passed to the function
// div_id: id of the div where the html will be inserted
function generate_html_from_data(type, path, path_data, div_id) {
    let request_data, content_type = get_data_and_content_type(type, path_data);

    $.ajax({
    url: path,
    type: type,
    dataType:"html",
    contentType: content_type,
    data: request_data,
    success: function(data) {
        console.log("success",data);
        document.getElementById(div_id).innerHTML = data;
    },
    error: function() {
        console.log("error", data);
        alert('error loading from database...');
        }
  });
}


// Function to execute the image modal
function execute_image_modal() {
    $('#ImageModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget) // Button that triggered the modal
        var uri = button.data('whatever') // Extract info from data-* attributes
        var name = button.data('name') // Extract info from data-* attributes
        var modal = $(this)
    
    
        modal.find('.modal-title').text(name)
        modal.find('#modal-download').attr('href', uri)
        modal.find('#modal_img').attr('src', uri)
    
    });
}

// Function to set up top toggles for project page
function ready_project_toggles() {
    $('#CardTabBox > span').click(function() {
    var ix = $(this).index();
    
    $('#CardBox').toggle( ix === 0 );
    $('#TagBox').toggle( ix === 0 );
    $('#ExtraBox').toggle( ix === 0 );
    $('#PlotBox').toggle( ix === 1 );
    $('#GraphBox').toggle( ix === 2 );
    $('#GraphicsBox').toggle( ix === 3 );
    
    });


}

// Function to call graphics
// uris: uris to be passed to the function
function call_graphics(uris) {
    var uri_data = uris;
    var path = "/opsml/runs/graphics";
    generate_html_from_data("POST", path, uri_data, "Insert");
    
}

// Function to set up project page
function ready_project_page() {
    $('#MetadataRepositoriesSelect').select2();

    $("#MetadataRepositoriesSelect").on('select2:select', function(e){
        window.location.href = e.params.data.id;
    });

    $('.list-group-item').click(function() {
        $('.list-group-item').removeClass('active');
        $(this).addClass('active');
        var version_uid = $(this).attr('id');
        alert(id);
          // write javscript that will take the value of the active div on click and pass that value to another div
       });

    $( "#metric-button" ).on( "click", function() {
        $( "#Metrics" ).toggle();
    } );
    
    $( "#param-button" ).on( "click", function() {
        $( "#Params" ).toggle();
    } );
    
    $( "#artifact-button" ).on( "click", function() {
        $( "#Artifacts" ).toggle();
    } );

    execute_image_modal();
    ready_project_toggles();

}

export {
    generate_html_from_data, 
    execute_image_modal, 
    ready_project_page,
    ready_project_toggles,
    call_graphics,
};