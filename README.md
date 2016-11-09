# B R O K E N

## Features
* Crawls for broken links from a given URL
    - You can choose which additional links are crawled
        + If they start with the same base URL as the given URL or
        + if they are sub-paths of the given URL
* Finds broken `href` links, image and video sources
    - Includes image hosting sites that do not conform to typical HTML 404 responses.
    - Includes video embeds whereby the videos are removed due to copyright claims.
* Provides options for the user to choose the crawling policy, maximum crawl duration and whether broken images and videos should be reported
* Simple and fast web interface.

## Architecture

>Sam wants to make batteries, she approaches the HQ. When the HQ receives such a request to produce batteries, it hires a `Manager`. The `Manager` in turns hires `Workers` to make batteries. He is also given a key to a `Store` in a warehouse. Every manager is given a `Store` in the warehouse. This entire warehouse is managed by surveillance drones, so when new batteries are created, they immediately announce to the customer (Sam) that a new item has been produced. Sam will then know when production is completed, including the number of batteries that exploded during production (i.e those that broke).

* Python 3.5
* [Tornado](http://www.tornadoweb.org/en/stable/) - An asynchronous networking library and web framework which provides the abstractions for handling HTTP requests and responses.
* [ZeroMQ](http://zeromq.org/) - Uses TCP connections to carry messages across different processes/threads, based on patterns such as Publisher-Subscriber and Push-Pull. Allows us to handle multiple crawls from different users which in turn spawn multiple worker threads to handle the crawls.
* [WebSockets](https://en.wikipedia.org/wiki/WebSocket) - Provides a full-duplex communication channel over a single TCP connection. Used to send crawl requests from the user and to provide realtime updates of the crawl from the backend.

## Development
After cloning the repo, you can either open it in PyCharm or create a virtual environment (then activate it) and install the requirements (`pip install -r requirements.txt`).

### PyCharm
1. Open the project in PyCharm
2. Create a virtualenv `File > Settings > Project Interpreter > Click on the plus icon` in the same directory, name it `venv`
3. Open any of the source files and PyCharm will prompt you to install the requirements
4. Right click on the `broken` package and `Mark Directory as` a source folder

### Run the app
Run `main.py` (backend) and `app.py` (frontend). App will run on http://localhost:8888.

### Frontend dev
`npm install -g gulp`
In the frontend folder:
`npm install`
`gulp`
