const ACTIVE_CARD_PATH = "/opsml/ui/error";

function errorToPage(message) {

    let request = {"message": message};

    return $.ajax({
        url: ACTIVE_CARD_PATH,
        type: "POST",
        dataType: "html",
        contentType: "application/json",
        data: JSON.stringify(request),
        success: function(data) {

            document.open();
            document.write(data);
            document.close();

        },

        error: function(xhr, status, error) {
            // send request to error route on error
            var err = JSON.parse(xhr.responseText);
            alert(JSON.stringify(err));
        }
    });
}

export { errorToPage };