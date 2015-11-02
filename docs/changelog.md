# golangconfig Changelog

## 0.9.0

 - `subprocess_info()` and `setting_value()` will now raise
   `GoRootNotFoundError()` when the `GOROOT` environment variable points to a
   directory that could not be found on disk, and `GoPathNotFoundError()` when
   one or more of the entries in the `GOPATH` environment variable could not be
   found on disk.

## 0.8.1

 - Added support for GOPATH with multiple directories
 - Fix an error when no project was open when using Sublime Text 3

## 0.8.0

 - Initial release
