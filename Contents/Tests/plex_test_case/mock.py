import imp
import os

mock_path = os.path.join(os.path.dirname(__file__), 'mock')
f, filename, desc = imp.find_module('mock', [mock_path])
mock = imp.load_module('mock', f, filename, desc)
