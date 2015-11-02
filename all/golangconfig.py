# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import os
import threading
import sys
import shellenv
import sublime

if sys.version_info < (3,):
    str_cls = unicode  # noqa
    py2 = True
else:
    str_cls = str
    py2 = False


__version__ = '0.9.0'
__version_info__ = (0, 9, 0)


# The sublime.platform() function will not be available in ST3 upon initial
# import, so we determine the platform via the sys.platform value. We cache
# the value here to prevent extra IPC calls between plugin_host and
# sublime_text in ST3.
_platform = {
    'win32': 'windows',
    'darwin': 'osx'
}.get(sys.platform, 'linux')


# A special value object to detect if a setting was not found, versus a setting
# explicitly being set to null/None in a settings file. We can't use a Python
# object here because the value is serialized to json via the ST API. Byte
# strings end up turning into an array of integers in ST3.
_NO_VALUE = '\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F'


class EnvVarError(EnvironmentError):

    """
    An error occurred finding one or more required environment variables
    """

    missing = None


class GoRootNotFoundError(EnvironmentError):

    """
    An error occurred finding the $GOROOT on disk
    """

    directory = None


class GoPathNotFoundError(EnvironmentError):

    """
    An error occurred finding one or more directories from $GOPATH on disk
    """

    directories = None


class ExecutableError(EnvironmentError):

    """
    An error occurred locating the executable requested
    """

    name = None
    dirs = None


def debug_enabled():
    """
    Checks to see if the "debug" setting is true

    :raises:
        RuntimeError
            When the function is called from any thread but the UI thread

    :return:
        A boolean - if debug is enabled
    """

    # The Sublime Text API is not threadsafe in ST2, so we
    # double check here to prevent crashes
    if not isinstance(threading.current_thread(), threading._MainThread):
        raise RuntimeError('golangconfig.setting_value() must be called from the main thread')

    value = sublime.load_settings('golang.sublime-settings').get('debug')
    return False if value == '0' else bool(value)


def subprocess_info(executable_name, required_vars, optional_vars=None, view=None, window=None):
    """
    Gathers and formats information necessary to use subprocess.Popen() to
    run one of the go executables, with details pulled from setting_value() and
    executable_path().

    Ensures that the executable path and env dictionary are properly encoded for
    Sublime Text 2, where byte strings are necessary.

    :param executable_name:
        A unicode string of the executable to locate, e.g. "go" or "gofmt"

    :param required_vars:
        A list of unicode strings of the environment variables that are
        required, e.g. "GOPATH". Obtains values from setting_value().

    :param optional_vars:
        A list of unicode strings of the environment variables that are
        optional, but should be pulled from setting_value() if available - e.g.
        "GOOS", "GOARCH". Obtains values from setting_value().

    :param view:
        A sublime.View object to use in finding project-specific settings. This
        should be passed whenever available.

    :param window:
        A sublime.Window object to use in finding project-specific settings.
        This should be passed whenever available.

    :raises:
        RuntimeError
            When the function is called from any thread but the UI thread
        TypeError
            When any of the parameters are of the wrong type
        golangconfig.ExecutableError
            When the executable requested could not be located. The .name
            attribute contains the name of the executable that could not be
            located. The .dirs attribute contains a list of unicode strings
            of the directories searched.
        golangconfig.EnvVarError
            When one or more required_vars are not available. The .missing
            attribute will be a list of the names of missing environment
            variables.
        golangconfig.GoPathNotFoundError
            When one or more directories specified by the GOPATH environment
            variable could not be found on disk. The .directories attribute will
            be a list of the directories that could not be found.
        golangconfig.GoRootNotFoundError
            When the directory specified by GOROOT environment variable could
            not be found on disk. The .directory attribute will be the path to
            the directory that could not be found.

        golangconfig.EnvVarError
            When one or more required_vars are not available. The .missing
            attribute will be a list of the names of missing environment
            variables.

    :return:
        A two-element tuple.

         - [0] A unicode string (byte string for ST2) of the path to the executable
         - [1] A dict to pass to the env parameter of subprocess.Popen()
    """

    path, _ = executable_path(executable_name, view=view, window=window)
    if path is None:
        name = executable_name
        if sys.platform == 'win32':
            name += '.exe'
        dirs = []
        settings_path, _ = _get_most_specific_setting('PATH', view=view, window=window)
        if settings_path and settings_path != _NO_VALUE:
            dirs.extend(settings_path.split(os.pathsep))
        _, shell_dirs = shellenv.get_path()
        for shell_dir in shell_dirs:
            if shell_dir not in dirs:
                dirs.append(shell_dir)
        exception = ExecutableError(
            'The executable "%s" could not be located in any of the following locations: "%s"' %
            (
                name,
                '", "'.join(dirs)
            )
        )
        exception.name = name
        exception.dirs = dirs
        raise exception

    path = shellenv.path_encode(path)

    _, env = shellenv.get_env(for_subprocess=True)

    var_groups = [required_vars]
    if optional_vars:
        var_groups.append(optional_vars)

    missing_vars = []

    for var_names in var_groups:
        for var_name in var_names:
            value, _ = setting_value(var_name, view=view, window=window)
            var_key = var_name

            if value is not None:
                value = str_cls(value)
                value = shellenv.env_encode(value)
            var_key = shellenv.env_encode(var_key)

            if value is None:
                if var_key in env:
                    del env[var_key]
                continue

            env[var_key] = value

    for required_var in required_vars:
        var_key = shellenv.env_encode(required_var)
        if var_key not in env:
            missing_vars.append(required_var)

    if missing_vars:
        missing_vars = sorted(missing_vars, key=lambda s: s.lower())
        exception = EnvVarError(
            'The following environment variable%s currently unset: %s' %
            (
                's are' if len(missing_vars) > 1 else ' is',
                ', '.join(missing_vars)
            )
        )
        exception.missing = missing_vars
        raise exception

    encoded_goroot = shellenv.env_encode('GOROOT')
    if encoded_goroot in env:
        unicode_sep = shellenv.path_decode(os.sep)
        name = executable_name
        if sys.platform == 'win32':
            name += '.exe'
        relative_executable_path = shellenv.path_encode('bin%s%s' % (unicode_sep, name))
        goroot_executable_path = os.path.join(env[encoded_goroot], relative_executable_path)
        if goroot_executable_path != path:
            print(
                'golangconfig: warning - binary %s was found at "%s", which is not inside of the GOROOT "%s"' %
                (
                    executable_name,
                    path,
                    shellenv.path_decode(env[encoded_goroot])
                )
            )

    return (path, env)


def setting_value(setting_name, view=None, window=None):
    """
    Returns the user's setting for a specific variable, such as GOPATH or
    GOROOT. Supports global and per-platform settings. Finds settings by
    looking in:

    1. If a project is open, the project settings
    2. The global golang.sublime-settings file
    3. The user's environment variables, as defined by their login shell

    If the setting is a known name, e.g. GOPATH or GOROOT, the value will be
    checked to ensure the path exists.

    :param setting_name:
        A unicode string of the setting to retrieve

    :param view:
        A sublime.View object to use in finding project-specific settings. This
        should be passed whenever available.

    :param window:
        A sublime.Window object to use in finding project-specific settings.
        This should be passed whenever available.

    :raises:
        RuntimeError
            When the function is called from any thread but the UI thread
        TypeError
            When any of the parameters are of the wrong type
        golangconfig.GoPathNotFoundError
            When one or more directories specified by the GOPATH environment
            variable could not be found on disk. The .directories attribute will
            be a list of the directories that could not be found.
        golangconfig.GoRootNotFoundError
            When the directory specified by GOROOT environment variable could
            not be found on disk. The .directory attribute will be the path to
            the directory that could not be found.

    :return:
        A two-element tuple.

        If no setting was found, the return value will be:

         - [0] None
         - [1] None

        If a setting was found, the return value will be:

         - [0] The setting value
         - [1] The source of the setting, a unicode string:
           - "project file (os-specific)"
           - "golang.sublime-settings (os-specific)"
           - "project file"
           - "golang.sublime-settings"
           - A unicode string of the path to the user's login shell

        The second element of the tuple is intended to be used in the display
        of debugging information to end users.
    """

    _require_unicode('setting_name', setting_name)
    _check_view_window(view, window)

    setting, source = _get_most_specific_setting(setting_name, view, window)

    if setting == _NO_VALUE:
        setting = None
        source = None

        shell, env = shellenv.get_env()
        if setting_name in env:
            source = shell
            setting = env[setting_name]

    if setting_name not in set(['GOPATH', 'GOROOT']):
        return (setting, source)

    if setting is None and source is None:
        return (setting, source)

    # We add some extra processing here for known settings to improve the
    # user experience, especially around debugging
    _debug_unicode_string(setting_name, setting, source)

    if not isinstance(setting, str_cls):
        setting = str_cls(setting)

    if setting_name == 'GOROOT':
        if os.path.exists(setting):
            return (setting, source)

    has_multiple = False
    if setting_name == 'GOPATH':
        values = setting.split(os.pathsep)
        has_multiple = len(values) > 1
        missing = []

        for value in values:
            if not os.path.exists(value):
                missing.append(value)

        if not missing:
            return (setting, source)

    if setting_name == 'GOROOT':
        message = 'The GOROOT environment variable value "%s" does not exist on the filesystem'
        e = GoRootNotFoundError(message % setting)
        e.directory = setting
        raise e

    if not has_multiple:
        suffix = 'value "%s" does not exist on the filesystem' % missing[0]
    elif len(missing) == 1:
        suffix = 'contains the directory "%s" that does not exist on the filesystem' % missing[0]
    else:
        paths = ', '.join('"' + path + '"' for path in missing)
        suffix = 'contains %s directories that do not exist on the filesystem: %s' % (len(missing), paths)

    message = 'The GOPATH environment variable ' + suffix
    e = GoPathNotFoundError(message)
    e.directories = missing
    raise e


def executable_path(executable_name, view=None, window=None):
    """
    Uses the user's Sublime Text settings and then PATH environment variable
    as set by their login shell to find a go executable

    :param name:
        The name of the binary to find - a unicode string of "go", "gofmt" or
        "godoc"

    :param view:
        A sublime.View object to use in finding project-specific settings. This
        should be passed whenever available.

    :param window:
        A sublime.Window object to use in finding project-specific settings.
        This should be passed whenever available.

    :raises:
        RuntimeError
            When the function is called from any thread but the UI thread
        TypeError
            When any of the parameters are of the wrong type

    :return:
        A 2-element tuple.

        If the executable was not found, the return value will be:

         - [0] None
         - [1] None

        If the exeutable was found, the return value will be:

         - [0] A unicode string of the full path to the executable
         - [1] A unicode string of the source of the PATH value
           - "project file (os-specific)"
           - "golang.sublime-settings (os-specific)"
           - "project file"
           - "golang.sublime-settings"
           - A unicode string of the path to the user's login shell

        The second element of the tuple is intended to be used in the display
        of debugging information to end users.
    """

    _require_unicode('executable_name', executable_name)
    _check_view_window(view, window)

    executable_suffix = '.exe' if sys.platform == 'win32' else ''
    suffixed_name = executable_name + executable_suffix

    setting, source = _get_most_specific_setting('PATH', view, window)
    if setting is not _NO_VALUE:
        is_str = isinstance(setting, str_cls)
        if not is_str:
            if debug_enabled():
                _debug_unicode_string('PATH', setting, source)
        else:
            for dir_ in setting.split(os.pathsep):
                possible_executable_path = os.path.join(dir_, suffixed_name)
                if _check_executable(possible_executable_path, source, setting):
                    return (possible_executable_path, source)

            if debug_enabled():
                print(
                    'golangconfig: binary %s not found in PATH from %s - "%s"' %
                    (
                        executable_name,
                        source,
                        setting
                    )
                )

    shell, path_dirs = shellenv.get_path()
    for dir_ in path_dirs:
        possible_executable_path = os.path.join(dir_, suffixed_name)
        if _check_executable(possible_executable_path, shell, os.pathsep.join(path_dirs)):
            return (possible_executable_path, shell)

    if debug_enabled():
        print(
            'golangconfig: binary %s not found in PATH from %s - "%s"' %
            (
                executable_name,
                shell,
                os.pathsep.join(path_dirs)
            )
        )

    return (None, None)


def _get_most_specific_setting(name, view, window):
    """
    Looks up a setting in the following order:

    1. View settings, looking inside of the "osx", "windows" or "linux" key
       based on the OS that Sublime Text is running on. These settings are from
       a project file.
    2. Window settings (ST3 only), looking inside of the "osx", "windows" or
       "linux" key based on the OS that Sublime Text is running on. These
       settings are from a project file.
    3. golang.sublime-settings, looking inside of the "osx", "windows" or
       "linux" key based on the OS that Sublime Text is running on.
    4. The view settings. These settings are from a project file.
    5. The window settings (ST3 only). These settings are from a project file.
    6. golang.sublime-settings

    :param name:
        A unicode string of the setting to fetch

    :param view:
        A sublime.View object to use in finding project-specific settings. This
        should be passed whenever available.

    :param window:
        A sublime.Window object to use in finding project-specific settings.
        This should be passed whenever available.

    :return:
        A two-element tuple.

        If no setting was found, the return value will be:

         - [0] golangconfig._NO_VALUE
         - [1] None

        If a setting was found, the return value will be:

         - [0] The setting value
         - [1] A unicode string of the source:
           - "project file (os-specific)"
           - "golang.sublime-settings (os-specific)"
           - "project file"
           - "golang.sublime-settings"
    """

    # The Sublime Text API is not threadsafe in ST2, so we
    # double check here to prevent crashes
    if not isinstance(threading.current_thread(), threading._MainThread):
        raise RuntimeError('golangconfig.setting_value() must be called from the main thread')

    if view is not None and not isinstance(view, sublime.View):
        raise TypeError('view must be an instance of sublime.View, not %s' % _type_name(view))

    if window is not None and not isinstance(window, sublime.Window):
        raise TypeError('window must be an instance of sublime.Window, not %s' % _type_name(window))

    st_settings = sublime.load_settings('golang.sublime-settings')

    view_settings = view.settings().get('golang', {}) if view else {}

    if view and not window:
        window = view.window()

    window_settings = {}
    if window:
        if sys.version_info >= (3,) and window.project_data():
            window_settings = window.project_data().get('settings', {}).get('golang', {})
        elif not view and window.active_view():
            window_settings = window.active_view().settings().get('golang', {})

    settings_objects = [
        (view_settings, 'project file'),
        (window_settings, 'project file'),
        (st_settings, 'golang.sublime-settings'),
    ]

    for settings_object, source in settings_objects:
        platform_settings = settings_object.get(_platform, _NO_VALUE)
        if platform_settings == _NO_VALUE:
            continue
        if not isinstance(platform_settings, dict):
            continue
        if platform_settings.get(name, _NO_VALUE) != _NO_VALUE:
            return (platform_settings.get(name), source + ' (os-specific)')

    for settings_object, source in settings_objects:
        result = settings_object.get(name, _NO_VALUE)
        if result != _NO_VALUE:
            return (settings_object.get(name), source)

    return (_NO_VALUE, None)


def _require_unicode(name, value):
    """
    Requires that a parameter be a unicode string

    :param name:
        A unicode string of the parameter name

    :param value:
        The parameter value

    :raises:
        TypeError
            When the value is not a unicode string
    """

    if not isinstance(value, str_cls):
        raise TypeError('%s must be a unicode string, not %s' % (name, _type_name(value)))


def _check_view_window(view, window):
    """
    Ensures that the view and window parameters to a function are suitable
    objects for our purposes. There is not a strict check for type to allow for
    mocking during testing.

    :param view:
        The view parameter to check

    :param window:
        The window parameter to check

    :raises:
        TypeError
            When the view or window parameters are not of the appropriate type
    """

    if view is not None:
        if not isinstance(view, sublime.View):
            raise TypeError('view must be an instance of sublime.View, not %s' % _type_name(view))

    if window is not None:
        if not isinstance(window, sublime.Window) and sys.version_info >= (3,):
            raise TypeError('window must be an instance of sublime.Window, not %s' % _type_name(window))


def _type_name(value):
    """
    :param value:
        The value to get the type name of

    :return:
        A unicode string of the name of the value's type
    """

    value_cls = value.__class__
    value_module = value_cls.__module__
    if value_module in set(['builtins', '__builtin__']):
        return value_cls.__name__

    return '%s.%s' % (value_module, value_cls.__name__)


def _debug_unicode_string(name, value, source):
    """
    Displays a debug message to the console if the value is not a unicode string

    :param name:
        A unicode string of the name of the setting

    :param value:
        The setting value to check

    :param source:
        A unicode string of the source of the setting
    """

    if value is not None and not isinstance(value, str_cls):
        print(
            'golangconfig: the value for %s from %s is not a string, but instead a %s' %
            (
                name,
                source,
                _type_name(value)
            )
        )


def _check_executable(possible_executable_path, source, setting):
    """
    Checks to see if a path to an executable exists and that it is, in fact,
    executable. Will display debug info if the path exists, but is not
    executable.

    :param possible_executable_path:
        A unicode string of the full file path to the executable

    :param source:
        A unicode string of the source of the setting

    :param setting:
        A unicode string of the PATH value that the executable was found in

    :return:
        A boolean - if the possible_executable_path is a file that is executable
    """

    if os.path.exists(possible_executable_path):
        is_executable = os.path.isfile(possible_executable_path) and os.access(possible_executable_path, os.X_OK)
        if is_executable:
            return True

        if debug_enabled():
            executable_name = os.path.basename(possible_executable_path)
            print(
                'golangconfig: binary %s found in PATH from %s - "%s" - is not executable' %
                (
                    executable_name,
                    source,
                    setting
                )
            )

    return False
