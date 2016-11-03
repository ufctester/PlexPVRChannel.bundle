import inspect
import os

from unittest import TestCase
from abc import ABCMeta

import bootstrap
from mock import mock
from plex import BasicRequest, FrameworkCore, PreferenceManager, Runtime


class PlexTestCase(TestCase):

    __metaclass__ = ABCMeta

    module_name = None

    mock = mock

    def __init__(self, methodName='runTest'):
        TestCase.__init__(self, methodName)
        # Get bundle and channel info for framework initialization.
        self.bundle_directory = bootstrap.bundle_directory
        self.config = bootstrap.config
        self.framework_directory = bootstrap.framework_directory
        # Autodetect module name if not defined explicitly.
        if self.module_name is None:
            self.module_name = self.__module__
            if self.module_name[-5:] == '_test':
                self.module_name = self.module_name[:-5]

    def tearDown(self):
        # Call teardown methods automatically if not called from the child classes.
        if hasattr(self, '_core'):
            self.teardown_framework()

    def setup_framework(self):
        # Setup framework core object, either call this from `setUp` method or it'll be called when first accessing
        # the object's `core` property.
        self._initialize_framework(self.bundle_directory, self.framework_directory, self.config)

    def _initialize_framework(self, bundle_path, framework_dir, config):
        # Check if the framework has already been initialized.
        if hasattr(self, '_core'):
            raise RuntimeError('Plex Framework already initialized.')
        # Create Framework core object instance.
        self._core = FrameworkCore(bundle_path, framework_dir, config)
        # Force wait for shared code sandbox loaded event.
        self._core.services.shared_code_sandbox
        # Initialize framework code and start plugin (same as in framework's bootstrap method `run`).
        if not self._core.load_code():
            raise RuntimeError('Error loading bundle code.')
        self._core.start()
        default_prefs = {k: v.default_value for k, v in self._core.sandbox.preferences.get()._prefs.items()}
        self._core.sandbox.preferences = PreferenceManager(default_prefs)

    def teardown_framework(self):
        # Tear down framework core object, call this from `tearDown` method.
        if hasattr(self, '_core'):
            self._core.runtime.taskpool.shutdown()
            self._core.runtime.check_threads()
            del self._core

    @property
    def core(self):
        # Initialize framework automatically if not yet done.
        if not hasattr(self, '_core'):
            self.setup_framework()
        return self._core

    @property
    def environment(self):
        return self.core.sandbox.environment

    @property
    def module(self):
        return self.environment[self.module_name]

    @property
    def networking(self):
        return self.core.networking

    @property
    def preferences(self):
        return self.core.sandbox.preferences.get()

    @property
    def shared_code_environment(self):
        return self.core.services.shared_code_sandbox.environment

    def get_file_contents(self, filename):
        # Read file placed in a subdirectory named after the testcase class name.
        test_path = os.path.dirname(inspect.getfile(self.__class__))
        with open('%s/%s/%s' % (test_path, self.__class__.__name__, filename), 'r') as content_file:
            content = content_file.read()
        return content

    def request(self, path, headers={}, method='GET', body=''):
        # Make a request to the channel code.
        request = BasicRequest(path, headers, method, body)
        return self.core.runtime.handle_request(request)
