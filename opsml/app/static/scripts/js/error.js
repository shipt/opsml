var ACTIVE_CARD_PATH = '/opsml/ui/error';

function GoBackWithRefresh(event) {
    if ('referrer' in document) {
        window.location = document.referrer;
        /* OR */
        //location.replace(document.referrer);
    } else {
        window.history.back();
    }
}

function errorToPage(message) {
    var request = { message: message };
    return $.ajax({
        url: ACTIVE_CARD_PATH,
        type: 'POST',
        dataType: 'html',
        contentType: 'application/json',
        data: JSON.stringify(request),
        success: function (data) {
            document.open();
            document.write(data);
            document.close();
            $(document).ready(function () {
                $('#back-button').click(GoBackWithRefresh);
            });
        },
        error: function (xhr, status, error) {
            // send request to error route on error
            var err = JSON.parse(xhr.responseText);
            alert(JSON.stringify(err)); // eslint-disable-line no-alert
        },
    });
}
export { errorToPage }; // eslint-disable-line import/prefer-default-export
