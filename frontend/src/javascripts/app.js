var ws_proto = location.protocol == "https:" ? "wss://" : "ws://";
var ws = new WebSocket( ws_proto + location.host + "/websocket");
var crawling = false;

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
      crawling = false;
    }
  } else if (data.response_type == "update_counts") {
    var numCrawled = data.counts[0];
    var numBroken = data.counts[1];
    updateCrawlSummary(numCrawled, numBroken);
  } else if (data.response_type == "update_links") {
    var link = data.links[0];
    updateBrokenLinkCard(link);
  }
};

function updateCrawlSummary(numCrawled, numBroken) {
  var data = {"numCrawled": numCrawled, "numBroken": numBroken};
  var summary = document.getElementById('crawl-summary');
  var template = "<p><b>{{numCrawled}}</b> URLs, <b>{{numBroken}}</b> broken links found</p>";
  var rendered = Mustache.render(template, data);
  summary.innerHTML = rendered;
}

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

    if (crawling) {
        return;
    }
    crawling = true;

    reset();
    ws.send(JSON.stringify({
      "url": document.getElementById("url").value
    }));
  });

  var searchBar = document.getElementById("crawl-status");
  var stickPoint = form.offsetTop;
  var stuck = false;

  window.onscroll = function(e) {
    var offset = window.pageYOffset;
    if (!stuck && (offset >= stickPoint)) {
      stuck = true;
      searchBar.style.top = '50px';
      if (navigator.userAgent.toLowerCase().indexOf('firefox') > -1) {
        searchBar.style.position = 'sticky';
      } else {
        searchBar.style.position = 'fixed';
      }
    } else if (stuck && (offset < stickPoint)) {
      stuck = false;
      searchBar.style.position = 'static';
    }
  }

});
