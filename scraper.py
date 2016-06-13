#!/usr/bin/env python

import sys

from tornado import gen, ioloop
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado.queues import Queue

class Scraper():

    def __init__(
                self,
                destinations=None,
                transform=None,
                headers={ },
                max_clients=50,
                maxsize=50,
                connect_timeout=None,
                request_timeout=600,
                ):
        """Instantiate a tornado async http client to do multiple concurrent requests"""

        if None in [destinations, transform]:
            sys.stderr.write('You must pass both collection of URLS and a transform function')
            raise SystemExit

        self.max_clients = max_clients
        self.maxsize = maxsize
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout

        AsyncHTTPClient.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient", max_clients=self.max_clients)

        self.http_client = AsyncHTTPClient()
        self.queue = Queue(maxsize=50)
        self.destinations = destinations
        self.transform = transform
        self.headers = headers
        self.read(self.destinations)
        self.get(self.transform, self.headers, self.connect_timeout, self.request_timeout, self.http_client)
        self.loop = ioloop.IOLoop.current()
        self.join_future = self.queue.join()

        def done(future):
            self.loop.stop()

        self.join_future.add_done_callback(done)
        self.loop.start()

    @gen.coroutine
    def read(self, destinations):
        for url in destinations:
            yield self.queue.put(url)

    @gen.coroutine
    def get(self, transform, headers, connect_timeout, request_timeout, http_client):
        while True:
            url = yield self.queue.get()
            request = HTTPRequest(url,
                                connect_timeout=connect_timeout,
                                request_timeout=request_timeout,
                                method="GET",
                                headers = headers
                                )

            future = self.http_client.fetch(request)

            def done_callback(future):
                body = future.result().body
                url = future.result().effective_url
                transform(body, url=url)
                self.queue.task_done()

            try:
                future.add_done_callback(done_callback)
            except Exception as e:
                sys.stderr.write(str(e))
                queue.put(url)
