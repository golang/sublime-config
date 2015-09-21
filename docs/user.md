# golangconfig User Documentation

The `golangconfig` package is a reusable library that Go-related Sublime Text
packages can use to obtain information about your Go environment.

This documentation details how you can set OS-specific, per-project and global
Sublime Text configuration for all packages that utilize `golangconfig`.

 - [Environment Autodetection](#environment-autodetection)
 - [Overriding the Environment](#overriding-the-environment)
   - [Global Sublime Text Settings](#global-sublime-text-settings)
   - [OS-Specific Settings](#os-specific-settings)
   - [Project-Specific Settings](#project-specific-settings)

## Environment Autodetection

By default `golangconfig` tries to detect all of your Go configuration by
invoking your login shell. It will pull in your `PATH`, `GOPATH`, and any other
environment variables you have set.

## Overriding the Environment

Generally, autodetecting the shell environment is sufficient for most users
with a homogenous Go environment. If your Go configuration is more complex,
Sublime Text settings may be used to handle it, via:

 - [Global Sublime Text Settings](#global-sublime-text-settings)
 - [OS-Specific Settings](#os-specific-settings)
 - [Project-Specific Settings](#project-specific-settings)

Settings are loading using the following precedence, from most-to-least
specific:

 - OS-specific project settings
 - OS-specific global Sublime Text settings
 - Project settings
 - Global Sublime Text settings
 - Shell environment

### Global Sublime Text Settings

To set variables for use in Sublime Text windows, you will want to edit your
`golang.sublime-settings` file. This can be accessed via the menu:

 1. Preferences
 2. Package Settings
 3. Golang Config
 3. Settings - User

Settings are placed in a json structure. Common settings include:

 - `PATH` - a list of directories to search for executables within. On Windows
   these are separated by `;`. OS X and Linux use `:` as a directory separator.
 - `GOPATH` - a string of the path to the root of your Go environment

Other Go settings may, or may not, be supported by the packages using these
settings. Examples include: `GOOS`, `GOARCH`, `GOROOT`.

```json
{
    "PATH": "/Users/jsmith/go/bin",
    "GOPATH": "/Users/jsmith/go"
}
```

### OS-Specific Settings

For users that are working on different operating systems, it may be necessary
to segement settings per OS. All settings may be nested under a key of one of
the following strings:

 - "osx"
 - "windows"
 - "linux"

```json
{
    "osx": {
        "PATH": "/Users/jsmith/go/bin",
        "GOPATH": "/Users/jsmith/go"
    },
    "windows": {
        "PATH": "C:\\Users\\jsmith\\go\\bin",
        "GOPATH": "C:\\Users\\jsmith\\go"
    },
    "linux": {
        "PATH": "/home/jsmith/go/bin",
        "GOPATH": "/home/jsmith/go"
    },
}
```

### Project-Specific Settings

When working on Go projects that use different environments, it may be
necessary to define settings in a
[Sublime Text project](http://docs.sublimetext.info/en/latest/file_management/file_management.html#projects)
file. The *Project* menu in Sublime Text provides the interface to create and
edit project files.

Within projects, all Go settings are placed under the `"settings"` key and then
further under a subkey named `"golang"`.

```json
{
    "folders": {
        "/Users/jsmith/projects/myproj"
    },
    "settings": {
        "golang": {
            "PATH": "/Users/jsmith/projects/myproj/env/bin",
            "GOPATH": "/Users/jsmith/projects/myproj/env"
        }
    }
}
```

Project-specific settings may also utilize the OS-specific settings feature.

```json
{
    "folders": {
        "/Users/jsmith/projects/myproj"
    },
    "settings": {
        "golang": {
            "osx": {
                "PATH": "/Users/jsmith/projects/myproj/env/bin",
                "GOPATH": "/Users/jsmith/projects/myproj/env"
            },
            "linux": {
                "PATH": "/home/jsmith/projects/myproj/env/bin",
                "GOPATH": "/home/jsmith/projects/myproj/env"
            }
        }
    }
}
```
