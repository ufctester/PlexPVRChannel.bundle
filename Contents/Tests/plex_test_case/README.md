Unit Tests for Plex Framework
=============================

This package is intended for [Plex][plex] channel developers and aims for recreating the Plex Framework environment
for [unit testing][unittest] the channel code. The framework runs channel code in a restricted sandbox and subjects
it to various restrictions making it hard to test the code independently. This package provides means to test the
channel code within the original sandbox as if it was run by the Plex Media Server.

Add to your channel
-------------------

The suggested place for the tests is a `Tests` subdirectory of the `Contents` directory, but it's not required.
The most simple way to add this module to your channel is to install it as a git submodule:

 1. Create and navigate to the `Contents/Tests` directory of your channel.
 2. Add a submodule to your repo:
    
    `git submodule add https://bitbucket.org/czukowski/plex-test-case.git plex_test_case`
    
 3. Initialize the submodule to have it download necessary code:
    
    `git submodule update --init --recursive`

Running tests
-------------

We'll use Python bundled with Plex Media Server to run the tests. To have it set up correctly, quite a lot of paths
need to be set up in `PYTHONPATH`. It helps to use an IDE that can help configure it more easily and also provide a
test runner. The following setup is described for the [PyCharm IDE][PyCharm] (though know that PyCharm introduces a
couple of its own obstacles to running tests).

 1. On Windows, the Python interpreter is a file named `PlexScriptHost.exe` located in the Plex folder in Program Files.
    For some reason PyCharm doesn't want to take a file with such name as a Python interpreter, so making its copy named
    `python.exe` may be necessary. It [might be fixed][PY-11992] somewhere in the future.
    
    For Plex on other operating systems things may be different.
    
    The interpreter is set in [Settings / Project Interpreter][PyCharm Interpreter] dialog.
    
 2. Unit test runner that comes with PyCharm, [`utrunner.py`][utrunner.py], is flawed in that it [won't load modules
    from a ZIP file][PY-12072]. To be able to use it, another file, [`pycharm_run_utils.py`][pycharm_run_utils.py],
    needs to be patched as described in [PY-12072]. This is not good as the IDE updates may overwrite that.
    
 3. Python libraries and extensions must be included in `PYTHONPATH`. The easy way to do it is to add them as content
    roots in [Settings / Project Structure][PyCharm Content Roots] dialog. The following files and directories are
    needed (example again from Windows, other OS users should figure that on their own, sorry):
     * `%ProgramFiles(x86)%\Plex\Plex Media Server\DLLs`
     * `%ProgramFiles(x86)%\Plex\Plex Media Server\Exts`
     * `%ProgramFiles(x86)%\Plex\Plex Media Server\python27.zip`
    
 4. Plex Framework specific code also need to be included in `PYTHONPATH`. This is done the same way as above, but first
    the actual base path has to be determined. It is located in a subfolder named `Plug-ins-???????` under the path
    `%ProgramFiles(x86)%\Plex\Plex Media Server\Resources\` (question marks stand for a string that resembles a git
    commit id) and may be different depending on the Plex Media Server version. Also it may change on PMS update and
    the old folder deleted. A good idea may be to make a copy and use it instead of the 'live' files.  The following
    directories need to be added as content roots:
    
     * `%ProgramFiles(x86)%\Plex\Plex Media Server\Resources\Plug-ins-???????\Framework.bundle\Contents\Resources\Platforms\Shared\Libraries`
     * `%ProgramFiles(x86)%\Plex\Plex Media Server\Resources\Plug-ins-???????\Framework.bundle\Contents\Resources\Versions\2\Python`
     * `%ProgramFiles(x86)%\Plex\Plex Media Server\Resources\Plug-ins-???????\Framework.bundle\Contents\Resources\Versions\1\Python`
     * `%ProgramFiles(x86)%\Plex\Plex Media Server\Resources\Plug-ins-???????\Framework.bundle\Contents\Resources\Versions\0\Python`
    
    Note the different framework versions in the list above, their load order is actually important, but PyCharm doesn't
    seem to offer a way to add the Content Roots in a specific order. A workaround for that is implemented in `bootstrap.py`
    to change the load order if needed.
    
 5. A [run configuration][PyCharm Run Tests] for unit tests has to be added for the project. Make sure 'Add content roots
    to PYTHONPATH' is checked. There is also an option to set environment variables that could be used to add the folders
    above to `PYTHONPATH`, but adding them as content roots has a benefit of offering some insight into the actual
    Framework code during debugging as well as a (very) limited code completion.

It should be possible to run the tests without any IDE and its test runners. The only thing necessary would be to configure
`PYTHONPATH` to include all the paths mentioned above, perhaps by creating a batch file.

Creating test cases
-------------------

Test case classes must extend the base test class, `PlexTestCase`. It provides the functionality to initialize the framework
and import the tested module in its sandbox. See `__init__.py` file for the implementation details. Many of it may be still
work in progress though.

To test the module, create a test case module with the same name and a `_test` suffix, then the tested module may be
accessed using `self.module` property. If you choose another naming convention, you'll need to set `module_name` attribute
in the test case class beforehand. Note that the tested module must be imported from `Code/__init__.py` either directly
or indirectly in order for it to be added to the sandboxed environment.

It is possible to test request handling by the channel controllers, using `self.request()` method.

HTTP requests made during testing will not send for real. The intention is to be able to mock these requests and return
predefined responses. The desired response body and headers may be preset using `self.networking.http_response_body` and
`self.networking.http_response_headers` in the test case class respectively.

There is a shortcut method to load file contents, accessible via `self.get_file_contents()`. It takes a file name that
is placed under the current module's subdirectory named after the current test case class.

Example test case module:

```python
from plex_test_case import PlexTestCase
from Framework.api.objectkit import ObjectContainer

class MyChannelTest(PlexTestCase):

    def test_main_menu(self):
        # Load './MyChannelTest/MainMenuObjectContainer.xml' as expected XML generated by channel.
        expected = self.get_file_contents('MainMenuObjectContainer.xml')
        # Fix HTTP response from the './MyChannelTest/Index.html' file contents.
        self.networking.http_response_body = self.get_file_contents('Index.html')
        # Make a request to channel code (which makes a HTTP request mocked above).
        status, headers, body = self.request('/video/mychannel')
        # Check the return values against expected.
        self.assertEquals(200, status)
        self.assertEquals('application/xml', headers['Content-Type'])
        self.assertEquals(expected, body)

class ParserTest(PlexTestCase):

    module_name = 'parser'

    def test_parse(self):
        # Load './ParserTest/Homepage.html' as input for parser.
        contents = self.get_file_contents('Homepage.html')
        # This is what the channel code would have called as 'HTML.ElementFromString(contents)'.
        # Shared Code modules (*.pys) run in a separate sandbox and could be accessed as `self.shared_code_environment`.
        nav = self.environment['HTML'].ElementFromString(contents)
        # Invoke `parse_categories()` function in 'parser.py' module.
        actual = self.module.parse_categories(nav)
        # Check actual return value against expected data structure, etc...
        ...
```

License
-------

This code is distributed under the MIT License.

 [plex]: https://plex.tv/
 [PY-11992]: https://youtrack.jetbrains.com/issue/PY-11992#comment=27-1259532
 [PY-12072]: https://youtrack.jetbrains.com/issue/PY-12072#comment=27-1255005
 [PyCharm]: https://www.jetbrains.com/pycharm/
 [PyCharm Interpreter]: https://www.jetbrains.com/pycharm/help/project-interpreter.html
 [PyCharm Content Roots]: https://www.jetbrains.com/pycharm/help/configuring-content-roots.html
 [PyCharm Run Tests]: https://www.jetbrains.com/pycharm/help/run-debug-configuration-python-unit-test.html
 [pycharm_run_utils.py]: https://github.com/JetBrains/intellij-community/blob/a7ac25ffa1298dd8d53f807889662763e4791a4c/python/helpers/pycharm/pycharm_run_utils.py
 [unittest]: https://docs.python.org/2/library/unittest.html
 [utrunner.py]: https://github.com/JetBrains/intellij-community/blob/a7ac25ffa1298dd8d53f807889662763e4791a4c/python/helpers/pycharm/utrunner.py