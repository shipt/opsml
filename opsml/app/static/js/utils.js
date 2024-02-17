
// Function to generate html from data
// path: path to the function that generates the html
// path_data: data to be passed to the function
// div_id: id of the div where the html will be inserted
export function generate_html_from_data(path, path_data, div_id) {$.ajax({
    url: path,
    type: "POST",
    dataType:"html",
    contentType: "application/json",
    data: JSON.stringify(path_data),
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