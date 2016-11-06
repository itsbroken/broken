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
  var template =  "<div id='broken-link-{{index}}' class='broken-link-data {{type}}'>" +
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
  while (links && links.firstChild) {
    links.removeChild(links.firstChild);
  }
}

var optionsShown = false;
function showOptions() {
  var settingsIcon = document.getElementById("settings-path");
  if (optionsShown) {
    hide("crawl-options");
    settingsIcon.style.fill = "";
    optionsShown = false;
  } else {
    show("crawl-options");
    settingsIcon.style.fill = "#41D3BD";
    optionsShown = true;
  }
}

function getOptions() {
  var options = {};
  var acceptedUrlsRadios = document.getElementsByName("accepted-urls");
  var crawlDurationRadios = document.getElementsByName("crawl-duration");
  var mediaTypesCheckboxes = document.getElementsByName("media-types");

  for (var i=0, length=acceptedUrlsRadios.length; i<length; i++) {
    if (acceptedUrlsRadios[i].checked) {
      options.acceptedUrls = acceptedUrlsRadios[i].value;
      break;
    }
  }

  for (var i=0, length=crawlDurationRadios.length; i<length; i++) {
    if (crawlDurationRadios[i].checked) {
      options.crawlDuration = crawlDurationRadios[i].value;
      break;
    }
  }

  options.mediaTypes = [];
  for (var i=0, length=mediaTypesCheckboxes.length; i<length; i++) {
    if (mediaTypesCheckboxes[i].checked) {
      options.mediaTypes.push(mediaTypesCheckboxes[i].value);
    }
  }

  return options;
}

window.addEventListener("load", function () {
  var form = document.getElementById("url-form");

  // Submit listener
  form.addEventListener("submit", function (event) {
    event.preventDefault();

    document.getElementById('url').blur();

    if (crawling) {
        return;
    }
    crawling = true;

    reset();
    ws.send(JSON.stringify({
      "url": document.getElementById("url").value,
      "options": getOptions()
    }));
  });

  // Input url listener
  var input = document.getElementById("url");
  input.addEventListener('input', function() {
    url = input.value;

    // Add "http://" for urls without them
    if (!url.trim().startsWith("http://") && !url.trim().startsWith("https://")) {
      url = "http://" + url;
    }

    var parser = document.createElement('a');
    parser.href = url;
    var rootUrl = parser.protocol + "//" + parser.host;
    if (input.value === "") {
      document.getElementById("accepted-urls-1-label").childNodes[2].textContent = "Root URL";
      document.getElementById("accepted-urls-2-label").childNodes[2].textContent = "Entire given URL";
    } else {
      document.getElementById("accepted-urls-1-label").childNodes[2].textContent = "Root URL: " + rootUrl;
      document.getElementById("accepted-urls-2-label").childNodes[2].textContent = "Entire given URL: " + rootUrl + parser.pathname;
    }
  });

  var crawlStatusBar = document.getElementById("crawl-status");
  var stickPoint = form.offsetTop;
  var stuck = false;

  window.onscroll = function(e) {
    var offset = window.pageYOffset;
    if (!stuck && (offset >= stickPoint)) {
      stuck = true;
      show("crawl-status-padding");
      crawlStatusBar.style.top = '20px';
      crawlStatusBar.style.zIndex = '100';
      crawlStatusBar.style.position = 'fixed';
      crawlStatusBar.style.margin = '0 auto';
    } else if (stuck && (offset < stickPoint)) {
      hide("crawl-status-padding");
      stuck = false;
      crawlStatusBar.style.zIndex = '97';
      crawlStatusBar.style.position = 'static';
      crawlStatusBar.style.margin = '';
    }
  }

});
