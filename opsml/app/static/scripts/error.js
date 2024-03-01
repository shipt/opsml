import $ from 'jquery';

const ACTIVE_CARD_PATH = '/opsml/ui/error';

function errorToPage(message) {
  const request = { message };

  return $.ajax({
    url: ACTIVE_CARD_PATH,
    type: 'POST',
    dataType: 'html',
    contentType: 'application/json',
    data: JSON.stringify(request),
    success(data) {
      document.open();
      document.write(data);
      document.close();
    },

    error(xhr, status, error) { // eslint-disable-line no-unused-vars
      // send request to error route on error
      const err = JSON.parse(xhr.responseText);
      alert(JSON.stringify(err)); // eslint-disable-line no-alert
    },
  });
}

export { errorToPage }; // eslint-disable-line import/prefer-default-export
