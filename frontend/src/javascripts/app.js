var ws = new WebSocket("ws://localhost:8888/websocket");

ws.onmessage = function (event) {
  data = JSON.parse(event.data);
  console.log(data);
  if (data.response_type == "status") {
    if (data.status == "crawling") {
      show("crawl-status");
      hide("help-content");
    } else if (data.status == "done") {
      hide("spinner");
      show("tick");
    }
  } else if (data.response_type == "update") {
    var link = data.broken_links[0];
    updateBrokenLinkCard(link);
  }
};

function updateBrokenLinkCard(link) {
  var brokenLinks = document.getElementById('broken-links');
  var template =  "<div id='broken-link-{{index}}' class='broken-link-data'>" +
                    "<p class='broken-link-url'>{{link}}</p>" +
                    "<div class='broken-link-parents'>" +
                      "<p>Found in the following pages:</p>" +
                      "<ol>" + 
                        "{{#parents}}" +
                          "<li><a href='{{.}}'>{{.}}</a></li>" +
                        "{{/parents}}" +
                      "</ol>" +
                    "</div>" +
                  "</div>";
  
  idString = "broken-link-" + link.index;
  existingElem = document.getElementById(idString);
  if (existingElem) {
    var newParent = Mustache.render("<li><a href='{{.}}'>{{.}}</a></li>", link.parents[0]);
    existingElem.getElementsByTagName("ol")[0].insertAdjacentHTML('beforeend', newParent);
  } else {
    var rendered = Mustache.render(template, link);
    brokenLinks.insertAdjacentHTML('beforeend', rendered);
  }
}

function show(id) {
  document.getElementById(id).className = document.getElementById(id).className.replace( /(?:^|\s)hidden(?!\S)/g , '');
}

function hide(id) {
  document.getElementById(id).classList.add('hidden');
}

function reset() {
  hide("crawl-status");
  hide("tick");
  show("spinner");
  var links = document.getElementById("broken-links");
  while (links.firstChild) {
    links.removeChild(links.firstChild);
  }
}

window.addEventListener("load", function () { 
  var form = document.getElementById("url-form");

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    reset();
    ws.send(JSON.stringify({
      "url": document.getElementById("url").value
    }));
  });
});