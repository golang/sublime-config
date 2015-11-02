# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import unittest

import sys
import os

if sys.version_info < (3,):
    str_cls = unicode  # noqa
else:
    str_cls = str

import shellenv
import golangconfig
from .mocks import GolangConfigMock
from .unittest_data import data, data_class


class CustomString():

    value = None

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def __unicode__(self):
        return self.__str__()


@data_class
class GolangconfigTests(unittest.TestCase):

    @staticmethod
    def subprocess_info_data():
        return (
            (
                'basic_shell',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                None,
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['gopath/'],
                'go',
                ['GOPATH'],
                None,
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}gopath',
                    }
                ),
            ),
            (
                'view_setting_override',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath', 'GOOS': 'windows'},
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                None,
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}custom/gopath',
                    }
                ),
            ),
            (
                'view_setting_override_optional_missing',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath'},
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                ['GOOS'],
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}custom/gopath',
                    }
                ),
            ),
            (
                'view_setting_override_optional_present',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath', 'GOOS': 'windows'},
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                ['GOOS'],
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}custom/gopath',
                        'GOOS': 'windows',
                    }
                ),
            ),
            (
                'view_setting_unset',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                    'GOOS': 'windows'
                },
                {'GOPATH': '{tempdir}custom/gopath', 'GOOS': None},
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                ['GOOS'],
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}custom/gopath',
                    }
                ),
            ),
            (
                'no_executable',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath'},
                None,
                {'debug': True, 'PATH': '{tempdir}usr/local/bin'},
                [],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                None,
                golangconfig.ExecutableError
            ),
            (
                'env_var_missing',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath'},
                None,
                {'debug': True},
                ['bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH', 'GOROOT'],
                None,
                golangconfig.GoRootNotFoundError
            ),
        )

    @data('subprocess_info_data', True)
    def subprocess_info(self, shell, env, view_settings, window_settings, sublime_settings,
                        executable_temp_files, temp_dirs, executable_name, required_vars, optional_vars,
                        expected_result):

        with GolangConfigMock(shell, env, view_settings, window_settings, sublime_settings) as mock_context:

            mock_context.replace_tempdir_env()
            mock_context.replace_tempdir_view_settings()
            mock_context.replace_tempdir_window_settings()
            mock_context.replace_tempdir_sublime_settings()

            mock_context.make_executable_files(executable_temp_files)
            mock_context.make_dirs(temp_dirs)

            if isinstance(expected_result, tuple):
                tempdir = mock_context.tempdir + os.sep
                executable_path = expected_result[0].replace('{tempdir}', tempdir)
                executable_path = shellenv.path_encode(executable_path)

                env_vars = {}
                for name, value in expected_result[1].items():
                    value = value.replace('{tempdir}', tempdir)
                    name = shellenv.env_encode(name)
                    value = shellenv.env_encode(value)
                    env_vars[name] = value

                expected_result = (executable_path, env_vars)

                self.assertEquals(
                    expected_result,
                    golangconfig.subprocess_info(
                        executable_name,
                        required_vars,
                        optional_vars=optional_vars,
                        view=mock_context.view,
                        window=mock_context.window
                    )
                )
                self.assertEqual('', sys.stdout.getvalue())

            else:
                def do_test():
                    golangconfig.subprocess_info(
                        executable_name,
                        required_vars,
                        optional_vars=optional_vars,
                        view=mock_context.view,
                        window=mock_context.window
                    )
                self.assertRaises(expected_result, do_test)

    @staticmethod
    def executable_path_data():
        return (
            (
                'basic_shell',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin'
                },
                None,
                None,
                {'debug': True},
                ['bin/go'],
                [],
                None,
                ('{tempdir}bin/go', '/bin/bash'),
            ),
            (
                'basic_view_settings',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin'
                },
                {'PATH': '{tempdir}usr/bin:{tempdir}usr/local/bin'},
                {},
                {},
                ['usr/local/bin/go'],
                ['usr/bin/go'],
                None,
                ('{tempdir}usr/local/bin/go', 'project file'),
            ),
            (
                'basic_view_settings_debug',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin'
                },
                {'PATH': '{tempdir}usr/bin:{tempdir}usr/local/bin'},
                {},
                {'debug': True},
                ['usr/local/bin/go'],
                ['usr/bin/go'],
                'is not executable',
                ('{tempdir}usr/local/bin/go', 'project file'),
            ),
            (
                'basic_view_settings_none_found',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin'
                },
                {'PATH': '{tempdir}usr/bin:{tempdir}usr/local/bin'},
                {},
                {'debug': True},
                [],
                ['usr/bin/go'],
                'is not executable',
                (None, None),
            ),
        )

    @data('executable_path_data', True)
    def executable_path(self, shell, env, view_settings, window_settings, sublime_settings,
                        executable_temp_files, non_executable_temp_files, expected_debug, expected_result):

        with GolangConfigMock(shell, env, view_settings, window_settings, sublime_settings) as mock_context:

            mock_context.replace_tempdir_env()
            mock_context.replace_tempdir_view_settings()
            mock_context.replace_tempdir_window_settings()

            mock_context.make_executable_files(executable_temp_files)
            mock_context.make_files(non_executable_temp_files)

            if expected_result[0]:
                tempdir = mock_context.tempdir + os.sep
                expected_result = (expected_result[0].replace('{tempdir}', tempdir), expected_result[1])

            self.assertEquals(
                expected_result,
                golangconfig.executable_path('go', mock_context.view, mock_context.window)
            )
            if expected_debug is None:
                self.assertEqual('', sys.stdout.getvalue())
            else:
                self.assertTrue(expected_debug in sys.stdout.getvalue())

    def test_executable_path_path_not_string(self):
        shell = '/bin/bash'
        env = {
            'PATH': '/bin'
        }
        view_settings = {
            'PATH': 1
        }
        with GolangConfigMock(shell, env, view_settings, None, {'debug': True}) as mock_context:
            self.assertEquals((None, None), golangconfig.executable_path('go', mock_context.view, mock_context.window))
            self.assertTrue('is not a string' in sys.stdout.getvalue())

    @staticmethod
    def setting_value_gopath_data():
        return (
            (
                'basic_shell',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                None,
                None,
                {},
                'GOPATH',
                (os.path.expanduser('~'), '/bin/bash'),
            ),
            (
                'basic_shell_2',
                '/bin/bash',
                {
                    'PATH': '/bin'
                },
                None,
                None,
                {},
                'PATH',
                ('/bin', '/bin/bash'),
            ),
            (
                'basic_view_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {'GOPATH': '/usr/bin'},
                None,
                {},
                'GOPATH',
                ('/usr/bin', 'project file'),
            ),
            (
                'basic_window_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                None,
                {'GOPATH': '/usr/bin'},
                {},
                'GOPATH',
                ('/usr/bin', 'project file'),
            ),
            (
                'basic_sublime_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {},
                {},
                {'GOPATH': '/usr/local/bin'},
                'GOPATH',
                ('/usr/local/bin', 'golang.sublime-settings'),
            ),
            (
                'os_view_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {
                    'osx': {'GOPATH': '/usr/bin'},
                    'windows': {'GOPATH': '/usr/bin'},
                    'linux': {'GOPATH': '/usr/bin'},
                },
                {},
                {},
                'GOPATH',
                ('/usr/bin', 'project file (os-specific)'),
            ),
            (
                'os_window_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                None,
                {
                    'osx': {'GOPATH': '/usr/bin'},
                    'windows': {'GOPATH': '/usr/bin'},
                    'linux': {'GOPATH': '/usr/bin'},
                },
                {},
                'GOPATH',
                ('/usr/bin', 'project file (os-specific)'),
            ),
            (
                'os_sublime_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {
                    'GOPATH': '/foo/bar'
                },
                {},
                {
                    'osx': {'GOPATH': '/usr/local/bin'},
                    'windows': {'GOPATH': '/usr/local/bin'},
                    'linux': {'GOPATH': '/usr/local/bin'},
                },
                'GOPATH',
                ('/usr/local/bin', 'golang.sublime-settings (os-specific)'),
            ),
            (
                'os_sublime_settings_wrong_type',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {},
                {},
                {
                    'osx': 1,
                    'windows': 1,
                    'linux': 1,
                },
                'GOPATH',
                (os.path.expanduser('~'), '/bin/bash'),
            ),
        )

    @data('setting_value_gopath_data', True)
    def setting_value_gopath(self, shell, env, view_settings, window_settings, sublime_settings, setting, result):

        with GolangConfigMock(shell, env, view_settings, window_settings, sublime_settings) as mock_context:
            self.assertEquals(result, golangconfig.setting_value(setting, mock_context.view, mock_context.window))
            self.assertEqual('', sys.stdout.getvalue())

    def test_setting_value_bytes_name(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.expanduser('~')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            def do_test():
                golangconfig.setting_value(b'GOPATH', mock_context.view, mock_context.window)
            self.assertRaises(TypeError, do_test)

    def test_setting_value_custom_type(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.expanduser('~')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            def do_test():
                golangconfig.setting_value(CustomString('GOPATH'), mock_context.view, mock_context.window)
            self.assertRaises(TypeError, do_test)

    def test_setting_value_incorrect_view_type(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.expanduser('~')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            def do_test():
                golangconfig.setting_value('GOPATH', True, mock_context.window)
            self.assertRaises(TypeError, do_test)

    def test_setting_value_incorrect_window_type(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.expanduser('~')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            def do_test():
                golangconfig.setting_value('GOPATH', mock_context.view, True)
            self.assertRaises(TypeError, do_test)

    def test_setting_value_gopath_not_existing(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.join(os.path.expanduser('~'), 'hdjsahkjzhkjzhiashs7hdsuybyusbguycas')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            def do_test():
                golangconfig.setting_value('GOPATH', mock_context.view, mock_context.window)
            self.assertRaises(golangconfig.GoPathNotFoundError, do_test)

    def test_setting_value_multiple_gopath_one_not_existing(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': '{tempdir}bin%s{tempdir}usr/bin' % os.pathsep
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            mock_context.replace_tempdir_env()
            mock_context.make_dirs(['usr/bin'])

            def do_test():
                golangconfig.setting_value('GOPATH', mock_context.view, mock_context.window)
            self.assertRaises(golangconfig.GoPathNotFoundError, do_test)

    def test_setting_value_multiple_gopath(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': '{tempdir}bin%s{tempdir}usr/bin' % os.pathsep
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            mock_context.replace_tempdir_env()
            mock_context.make_dirs(['bin', 'usr/bin'])
            self.assertEquals(
                (env['GOPATH'], shell),
                golangconfig.setting_value('GOPATH', mock_context.view, mock_context.window)
            )
            self.assertEqual('', sys.stdout.getvalue())

    def test_setting_value_gopath_not_string(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': 1
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            def do_test():
                golangconfig.setting_value('GOPATH', mock_context.view, mock_context.window)
            self.assertRaises(golangconfig.GoPathNotFoundError, do_test)

    def test_subprocess_info_goroot_executable_not_inside(self):
        shell = '/bin/bash'
        env = {
            'PATH': '{tempdir}bin:{tempdir}go/bin',
            'GOPATH': '{tempdir}workspace',
            'GOROOT': '{tempdir}go'
        }
        with GolangConfigMock(shell, env, None, None, {}) as mock_context:
            mock_context.replace_tempdir_env()
            mock_context.replace_tempdir_view_settings()
            mock_context.replace_tempdir_window_settings()

            mock_context.make_executable_files(['bin/go', 'go/bin/go'])
            mock_context.make_dirs(['workspace'])

            golangconfig.subprocess_info(
                'go',
                ['GOPATH'],
                optional_vars=['GOROOT'],
                view=mock_context.view,
                window=mock_context.window
            )
            self.assertTrue('which is not inside of the GOROOT' in sys.stdout.getvalue())
