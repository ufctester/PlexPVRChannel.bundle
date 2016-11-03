import inspect
import logging
import os
import sys
import urllib2
from Framework import components, core
from StringIO import StringIO


GLOBAL_DEFAULT_TIMEOUT = components.networking.GLOBAL_DEFAULT_TIMEOUT

class BasicRequest(object):

    def __init__(self, uri, headers={}, method='GET', body=''):
        self.uri = uri
        self.headers = headers
        self.method = method
        self.body = body


class FrameworkCore(core.FrameworkCore):
    """
        Framework core class extension to modify components in testing environment.
    """
    def _setup_storage(self):
        # Don't configure output into real log file.
        logging.basicConfig()
        logging.setLoggerClass(core.FrameworkLogger)
        logger = logging.getLogger()
        logger.handlers[0].addFilter(core.LogFilter())
        self.log = logging.getLogger(self.identifier)
        self._start_component(components.Storage)
        self._values = {}
        self._values_file_path = os.path.join(self.plugin_support_path, 'Data', self.identifier, 'StoredValues')

    def get_server_info(self):
        # Don't do actual request to Plex server and return dummy values.
        self.attributes['machineIdentifier'] = 'Unit testing'
        self.attributes['serverVersion'] = None

    def start(self):
        # Same implementation as in parent class, just without error handling, to allow us to see what went wrong.
        if self.init_code:
            self.sandbox.execute(self.init_code)
        self.sandbox.call_named_function(core.START_FUNCTION_NAME)

    def log_exception(self, fmt, *args):
        error = sys.exc_info()
        if error:
            # Catch a special case in the original `Runtime.handle_request`. If error is allowed to raise here, then
            # the local variable `body` will not be set and the code fail on `UnboundLocalError` in `finally` later.
            (frame, _, _, function_name, _, _) = inspect.getouterframes(inspect.currentframe())[1]
            if function_name == 'handle_request' and frame.f_locals['self'].__class__ == Runtime:
                self.runtime.request_error = error
                return
            # In general case, just raise the error.
            raise error[0], error[1], error[2]

    def _start_component(self, component):
        # Replace runtime and networking components with our implementations.
        if component == components.Runtime:
            component = Runtime
        elif component == components.Networking:
            component = Networking
        super(FrameworkCore, self)._start_component(component)


class PreferenceManager(object):

    def __init__(self, values={}):
        self._dict = values

    def get(self):
        return self._dict


class ResponseHeaders(object):

    def __init__(self, headers):
        self.dict = {k: v.lower() for k, v in headers.iteritems()}

    def get(self, header, default=None):
        lowercase = header.lower()
        return self.dict[lowercase] if lowercase in self.dict else default


class ResponseBody(StringIO):

    def __init__(self, string):
        StringIO.__init__(self, string)
        self.recv = None

    @property
    def _sock(self):
        return self


class HTTPHandler(urllib2.HTTPHandler):

    def __init__(self, networking):
        self._networking = networking

    def get_response(self, req):
        if self._networking.http_response_body is not None:
            response = urllib2.addinfourl(ResponseBody(self._networking.http_response_body),
                                          ResponseHeaders(self._networking.http_response_headers),
                                          req.get_full_url())
            response.code = 200
            response.msg = "OK"
            return response
        raise RuntimeError('Unhandled HTTP request: %s' % req.get_full_url())

    def http_open(self, req):
        return self.get_response(req)


class Networking(components.Networking):
    """
        Networking class extension to avoid sending actual requests in tests.
    """
    def _init(self):
        super(Networking, self)._init()
        self.http_response_body = None
        self.http_response_headers = {}

    def build_opener(self, cookie_jar=None):
        return urllib2.build_opener(HTTPHandler(self))


class Runtime(components.Runtime):
    """
        Runtime class extension to keep track of the framework's threads and locks.
    """
    def _init(self):
        self._threads = []
        super(Runtime, self)._init()

    def create_thread(self, f, log=True, sandbox=None, globalize=True, *args, **kwargs):
        # Store the created threads so that their status can be checked after tests have run.
        thread = super(Runtime, self).create_thread(f, log, sandbox, globalize, *args, **kwargs)
        self._threads.append(thread)
        return thread

    def check_threads(self):
        # Check for alive non-daemon threads and throw error if found.
        # Ignored threads are just slow but they don't run in a loop so they'll finish eventually.
        ignored = ['_setup_shared_code_sandbox']
        for thread in self._threads:
            if thread.is_alive() and not thread.daemon and thread.name not in ignored:
                raise RuntimeError('Alive non-daemon thread %s found, this will prevent shutdown.' % str(thread))

    def handle_request(self, request):
        # In case the parent method encounters an error reported using `_report_error` method, we'll raise it here.
        self.request_error = None
        status, headers, body = super(Runtime, self).handle_request(request)
        if self.request_error is not None:
            raise self.request_error[0], self.request_error[1], self.request_error[2]
        return status, headers, body

    def _report_error(self, request, controller, kwargs, e):
        return

    def get_resource_hashes(self):
        return
