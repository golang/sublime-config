# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import os
import sys
import shutil
import locale
import stat

import golangconfig

if sys.version_info < (3,):
    from cStringIO import StringIO
    str_cls = unicode  # noqa
else:
    from io import StringIO
    str_cls = str


class SublimeViewMock():

    _settings = None
    _context = None

    def __init__(self, settings, context):
        self._settings = settings
        self._context = context

    def settings(self):
        if self.window():
            # In Sublime Text, View objects inherit settings from the window/project
            # unless they are explicitly set on the view, so we replicate that here
            merged_golang_settings = {}
            project_data = self.window().project_data()
            if project_data:
                merged_golang_settings.update(project_data.get('settings', {}).get('golang', {}).copy())
            merged_golang_settings.update(self._settings)
        elif self._settings:
            merged_golang_settings = self._settings.copy()
        else:
            merged_golang_settings = {}
        return {'golang': merged_golang_settings}

    def window(self):
        return self._context.window


class SublimeWindowMock():

    _settings = None
    _context = None

    def __init__(self, settings, context):
        self._settings = settings
        self._context = context

    def project_data(self):
        if self._settings is None:
            return None
        return {'settings': {'golang': self._settings}}

    def active_view(self):
        if self._context.view:
            return self._context.view
        return SublimeViewMock({}, self._context)


class ShellenvMock():

    _env_encoding = locale.getpreferredencoding() if sys.platform == 'win32' else 'utf-8'
    _fs_encoding = 'mbcs' if sys.platform == 'win32' else 'utf-8'

    _shell = None
    _data = None

    def __init__(self, shell, data):
        self._shell = shell
        self._data = data

    def get_env(self, for_subprocess=False):
        if not for_subprocess or sys.version_info >= (3,):
            return (self._shell, self._data)

        shell = self._shell.encode(self._fs_encoding)
        env = {}
        for name, value in self._data.items():
            env[name.encode(self._env_encoding)] = value.encode(self._env_encoding)

        return (shell, env)

    def get_path(self):
        return (self._shell, self._data.get('PATH', '').split(os.pathsep))

    def env_encode(self, value):
        if sys.version_info >= (3,):
            return value
        return value.encode(self._env_encoding)

    def path_encode(self, value):
        if sys.version_info >= (3,):
            return value
        return value.encode(self._fs_encoding)

    def path_decode(self, value):
        if sys.version_info >= (3,):
            return value
        return value.decode(self._fs_encoding)


class SublimeSettingsMock():

    _values = None

    def __init__(self, values):
        self._values = values

    def get(self, name, default=None):
        return self._values.get(name, default)


class SublimeMock():

    _settings = None
    View = SublimeViewMock
    Window = SublimeWindowMock

    def __init__(self, settings):
        self._settings = SublimeSettingsMock(settings)

    def load_settings(self, basename):
        return self._settings


class GolangConfigMock():

    _shellenv = None
    _sublime = None
    _stdout = None

    _tempdir = None

    _shell = None
    _env = None
    _view_settings = None
    _window_settings = None
    _sublime_settings = None

    def __init__(self, shell, env, view_settings, window_settings, sublime_settings):
        self._shell = shell
        self._env = env
        self._view_settings = view_settings
        self._window_settings = window_settings
        self._sublime_settings = sublime_settings
        self._tempdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mock_fs')
        if not os.path.exists(self._tempdir):
            os.mkdir(self._tempdir)

    def replace_tempdir_env(self):
        for key in self._env:
            self._env[key] = self._env[key].replace(
                '{tempdir}',
                self.tempdir + os.sep
            )

    def replace_tempdir_view_settings(self):
        self._replace_tempdir_settings(self._view_settings)

    def replace_tempdir_window_settings(self):
        self._replace_tempdir_settings(self._window_settings)

    def replace_tempdir_sublime_settings(self):
        self._replace_tempdir_settings(self._sublime_settings)

    def _replace_tempdir_settings(self, settings_dict):
        if settings_dict:
            for key in settings_dict:
                if isinstance(settings_dict[key], str_cls):
                    settings_dict[key] = settings_dict[key].replace(
                        '{tempdir}',
                        self.tempdir + os.sep
                    )
            for platform in ['osx', 'windows', 'linux']:
                if platform not in settings_dict:
                    continue
                for key in settings_dict[platform]:
                    if isinstance(settings_dict[platform][key], str_cls):
                        settings_dict[platform][key] = settings_dict[platform][key].replace(
                            '{tempdir}',
                            self.tempdir + os.sep
                        )

    def make_executable_files(self, executable_temp_files):
        self.make_files(executable_temp_files)
        for temp_file in executable_temp_files:
            temp_file_path = os.path.join(self.tempdir, temp_file)
            st = os.stat(temp_file_path)
            os.chmod(temp_file_path, st.st_mode | stat.S_IEXEC)

    def make_files(self, temp_files):
        for temp_file in temp_files:
            temp_file_path = os.path.join(self.tempdir, temp_file)
            temp_file_dir = os.path.dirname(temp_file_path)
            if not os.path.exists(temp_file_dir):
                os.makedirs(temp_file_dir)
            with open(temp_file_path, 'a'):
                pass

    def make_dirs(self, temp_dirs):
        for temp_dir in temp_dirs:
            temp_dir_path = os.path.join(self.tempdir, temp_dir)
            if not os.path.exists(temp_dir_path):
                os.makedirs(temp_dir_path)

    @property
    def view(self):
        if self._view_settings is None:
            return None
        return SublimeViewMock(self._view_settings, self)

    @property
    def window(self):
        return SublimeWindowMock(self._window_settings, self)

    @property
    def tempdir(self):
        return self._tempdir

    def __enter__(self):
        self._shellenv = golangconfig.shellenv
        golangconfig.shellenv = ShellenvMock(self._shell, self._env)
        self._sublime = golangconfig.sublime
        golangconfig.sublime = SublimeMock(self._sublime_settings)
        self._stdout = sys.stdout
        sys.stdout = StringIO()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        golangconfig.shellenv = self._shellenv
        golangconfig.sublime = self._sublime
        temp_stdout = sys.stdout
        sys.stdout = self._stdout
        print(temp_stdout.getvalue(), end='')
        if self._tempdir and os.path.exists(self._tempdir):
            shutil.rmtree(self._tempdir)
