  // check if repositories is not empty
  if (repositories.length > 0) {
    var select = document.getElementById("MetadataRepositoriesSelect");
    // remove all content from select before adding new content
    select.innerHTML = "";

    for (var i = 0; i < repositories.length; i++) {
        var opt = document.createElement('option');
        opt.value = repositories[i];
        opt.innerHTML = repositories[i];
        select.appendChild(opt);
    }
} else {
    var select = document.getElementById("MetadataRepositoriesSelect");
    // remove all content from select before adding new content
    select.innerHTML = "";

    var opt = document.createElement('option');
    opt.value = "No repositories found";
    opt.innerHTML = "No repositories found";
    select.appendChild(opt);
}

// check if names is not empty and add 'card.html' to artifact-card-div

if (names.length > 0) {
    var artifact_card_div = document.getElementById("artifact-card-div");
    artifact_card_div.innerHTML = "";

    for (var i = 0; i < names.length; i++)
    {
        var card = document.createElement('div');
        card.className = "card text-left rounded m-1";
        card.style = "width: 14rem;";
        card.id = "artifact-card";

        var card_body = document.createElement('div');
        card_body.className = "card-body";

        var card_row = document.createElement('div');
        card_row.className = "row";

        var card_col = document.createElement('div');
        card_col.className = "col-sm-8";

        var card_title = document.createElement('h5');
        card_title.className = "card-title";
        card_title.innerHTML = names[i];

        var card_text = document.createElement('a');
        card_text.className = "stretched-link";
        card_text.href = "#";
        card_text.value = names[i];


        card_col.appendChild(card_title);
        card_col.appendChild(card_text);
        card_row.appendChild(card_col);

        // create image column
        var card_col_img = document.createElement('div');
        card_col_img.className = "col-sm-4";
        card_col_img.id = "artifact-card-img";

        var card_img = document.createElement('img');
        card_img.className = "center-block";
        card_img.src = "/static/images/chip.png";

        card_col_img.appendChild(card_img);
        card_row.appendChild(card_col_img);

        card_body.appendChild(card_row);
        card.appendChild(card_body);
        artifact_card_div.appendChild(card);
    }}
else {
    var artifact_card_div = document.getElementById("artifact-card-div");
    artifact_card_div.innerHTML = "";

 
}

