import errno
import os

import config

BUNDLED_PLUGINS_PATH_KEY = 'PLEXBUNDLEDPLUGINSPATH'
LOCAL_APP_DATA_KEY = 'PLEXLOCALAPPDATA'

framework_dir_template = os.path.join('Framework.bundle', 'Contents')
plugins_path_template = os.path.join(framework_dir_template, 'Resources', 'Versions', '%i', 'Python')
shared_libs_path_template = os.path.join(framework_dir_template, 'Resources', 'Platforms', 'Shared', 'Libraries')
framework_versions = [2, 1, 0]
plugin_bundle_path_template = ['Plex Media Server', 'Plug-ins', '.bundle', 'Contents']
plugin_bundle_key = 2


# Raise error if in the environment variable key is not set or its value is not a directory.
def validate_directory(key):
    if not os.environ[key]:
        raise ValueError('Environment variable %s is empty' % key)
    elif not os.path.isdir(os.environ[key]):
        raise OSError(errno.ENOTDIR, os.strerror(errno.ENOENT), os.environ[key])


# Determine whether the path in the argument is a framework version path and returns it, or None.
def pick_framework_path(path_arg):
    if not path_arg.endswith('Python'):
        return None
    for version in framework_versions:
        path = plugins_path_template % version
        if path_arg.endswith(path):
            return path
    return None


# Find the current plugin bundle directory based on assumption that the current file is in some of its subdirectories.
def find_bundle_directory(path_arg):
    if not __file__.startswith(path_arg):
        raise ValueError('File path (%s) expected to start with %s' % (__file__, path_arg))
    bundle_parts = [path_arg.rstrip(os.sep)]
    parts = __file__[len(path_arg):].split(os.sep)
    for index, actual_name in enumerate(parts):
        if index >= len(plugin_bundle_path_template):
            break
        expected_name = plugin_bundle_path_template[index]
        if index != plugin_bundle_key and actual_name != expected_name:
            raise ValueError('Unexpected directory name in %s, expected %s' % (__file__, actual_name))
        elif index == plugin_bundle_key and not actual_name.endswith(expected_name):
            raise ValueError('Unexpected directory name in %s, expected to end with %s' % (__file__, actual_name))
        if index <= plugin_bundle_key:
            bundle_parts.append(actual_name)
    return os.path.join(*bundle_parts)


# Try autodetect `PLEXLOCALAPPDATA` environment variable if not already set.
if LOCAL_APP_DATA_KEY not in os.environ:
    def find_plex_local_app_data_path():
        if 'LOCALAPPDATA' not in os.environ:
            raise KeyError('Environment variable %s is not set' % 'LOCALAPPDATA')
        return os.environ['LOCALAPPDATA'] + os.sep
    os.environ[LOCAL_APP_DATA_KEY] = find_plex_local_app_data_path()
validate_directory(LOCAL_APP_DATA_KEY)


# Try autodetect `PLEXBUNDLEDPLUGINSPATH` environment variable if not already set.
if BUNDLED_PLUGINS_PATH_KEY not in os.environ:
    def find_plex_bundled_plugins_path():
        for sys_path in os.sys.path:
            path = pick_framework_path(sys_path)
            if path is not None:
                bundle_path = sys_path[:-len(path)]
                return bundle_path.rstrip(os.sep)
    os.environ[BUNDLED_PLUGINS_PATH_KEY] = find_plex_bundled_plugins_path()
validate_directory(BUNDLED_PLUGINS_PATH_KEY)


# Add shared libraries path if not already added.
def setup_shared_libs_path(bundled_plugins_path):
    path = os.path.join(bundled_plugins_path, shared_libs_path_template)
    if path not in os.sys.path:
        os.sys.path.append(path)
setup_shared_libs_path(os.environ[BUNDLED_PLUGINS_PATH_KEY])


# Remove and re-add framework paths in `sys.path` as they may have been added in the wrong order.
def setup_framework_paths(bundled_plugins_path):
    def make_framework_path(version):
        return os.path.join(bundled_plugins_path, plugins_path_template) % version
    version_index = 0
    for path_index, sys_path in enumerate(os.sys.path):
        if version_index not in framework_versions:
            break
        path = pick_framework_path(sys_path)
        if path is not None:
            os.sys.path[path_index] = make_framework_path(framework_versions[version_index])
            version_index += 1
    for version_index in range(version_index, len(framework_versions)):
        os.sys.path.append(make_framework_path(framework_versions[version_index]))
setup_framework_paths(os.environ[BUNDLED_PLUGINS_PATH_KEY])

# Set module variables useful for framework initialization inside test case.
bundle_directory = find_bundle_directory(os.environ[LOCAL_APP_DATA_KEY])
framework_directory = os.path.join(os.environ[BUNDLED_PLUGINS_PATH_KEY], plugins_path_template, '..') % 2
framework_directory = os.path.abspath(framework_directory)

# Import subsystem to install some built-ins required by framework.
import subsystem
