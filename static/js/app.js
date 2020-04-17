$(document).ready(function() {
  $('[data-toggle="tooltip"]').tooltip();
});

function search() {
    var req = new XMLHttpRequest();
    var searchBox = document.getElementById('searchbox');
    req.open('GET', '/search?search=' + searchBox.value);
    console.log('/search?search=' + searchBox.value);
    req.onload = function() {
        var json = JSON.parse(req.responseText)
        var articlesRow = document.getElementById('articles');
        articlesRow.innerHTML = '';
        renderHTML(json)
    };
    req.onerror = function() {
        console.log("Connection error");
    };
    req.send();
};

function renderHTML(data) {
    var articlesRow = document.getElementById('articles');
    var htmlString = ''
    for (var key in data) {
        htmlString += '<div class="col col-md-5 mb-4">'
        htmlString += '<h5 class="display-5" align="center" >' + key + '</h5>'
        for (var i = 0; i < data[key].length; i++) {
            var article = data[key][i]
            htmlString += '<div class="row"><div class="col col-md-9" style="border-bottom: 1px solid #eeeded;">'
            if (article.summary != '') {
                htmlString += '<a style="text-decoration: none; color: black;" href="' + article.link + '" target="_blank" data-toggle="tooltip" data-placement="bottom" data-html="true" title="<em>'
                htmlString += article.summary + '</em>">' + article.headline + '</a>'
            }
            else {
                htmlString += '<a style="text-decoration: none; color: black;" href="' + article.link + '" target="_blank">' + article.headline + '</a>'
            }
            htmlString += '</div><div class="col col-md-3" style="text-align: right;"><em style="font-size: 12px;">' + article.publish_time + '</em></div></div>'
        }
        htmlString += '</div>'
    }
    articlesRow.insertAdjacentHTML('beforeend', htmlString);
    $(function() {
      $('[data-toggle="tooltip"]').tooltip();
    });
}
