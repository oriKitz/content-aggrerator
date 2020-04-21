$(document).ready(function() {
  $('[data-toggle="tooltip"]').tooltip();
});

function search() {
    var req = new XMLHttpRequest();
    var searchBox = document.getElementById('searchbox');
    var checkbox = document.getElementById('regex');
    req.open('GET', '/search?search=' + searchBox.value + '&regex=' + checkbox.checked);
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

function getPrettyDate(dateString) {
    var date = new Date(dateString.slice(0, -3))
    return date.getDate().toString().padStart(2, '0') + "." + date.getMonth().toString().padStart(2, '0') + " " + date.getHours().toString().padStart(2, '0') + ':' + date.getMinutes().toString().padStart(2, '0')
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function hasHebrew(text) {
    var hebrew = /[\u0590-\u05FF]/;
    return hebrew.test(text);
};

function renderHTML(data) {
    var articlesRow = document.getElementById('articles');
    var htmlString = ''
    for (var key in data) {
        htmlString += '<div class="col col-md-5 mb-4">'
        htmlString += '<h5 class="display-5" align="center" >' + key + '</h5>'
        for (var i = 0; i < data[key].length; i++) {
            var article = data[key][i]
            if (hasHebrew(article.headline)) {
                htmlString += '<div class="row"><div class="col col-md-9 hebrew" style="border-bottom: 1px solid #eeeded;">'
            }
            else {
                htmlString += '<div class="row"><div class="col col-md-9" style="border-bottom: 1px solid #eeeded;">'
            }
            if (article.summary != '') {
                htmlString += '<a style="text-decoration: none; color: black;" href="' + article.link + '" target="_blank" data-toggle="tooltip" data-placement="bottom" data-html="true" title="<em>'
                htmlString += escapeHtml(article.summary) + '</em>">' + escapeHtml(article.headline) + '</a>'
            }
            else {
                htmlString += '<a style="text-decoration: none; color: black;" href="' + article.link + '" target="_blank">' + escapeHtml(article.headline) + '</a>'
            }
            htmlString += '</div><div class="col col-md-3" style="text-align: right;"><em style="font-size: 12px;">' + getPrettyDate(article.publish_time) + '</em></div></div>'
        }
        htmlString += '</div>'
    }
    articlesRow.insertAdjacentHTML('beforeend', htmlString);
    $(function() {
      $('[data-toggle="tooltip"]').tooltip();
    });
}
