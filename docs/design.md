# golangconfig Design

The `golangconfig` Sublime Text dependency was designed based on the following
ideas:

 - Settings should be supported coming from the following sources, in order:
   - Sublime Text project files under the `golang` key
   - Any `golang.sublime-settings` files
   - The user's shell environment, as defined by invoking their login shell
 - The project and global Sublime Text settings will also allow for placing
   settings in a platform-specific sub-dictionary to allow users to easily
   work across different operating systems. The keys for these are used by
   other ST packages to allow for platform-specific functionality:
   - "osx"
   - "windows"
   - "linux"
 - Platform-specific settings are always higher priority than
   non-platform-specific, no matter what source they are pulled from
 - Setting names that are core to Go configuration preserve the uppercase style
   of environment variables. Thus the settings are named `GOPATH`, `GOROOT`,
   `PATH`, etc.


 - When returning results, the value requested is returned along with a
   user-friendly source description that can be used when displaying
   configuration details to the user
 - The API eschews duck-typing in an attempt to prevent various edge-case bugs.
   This is largely due to the weak-typing issues of strings in Python 2 where
   byte strings and unicode strings are often mixed, only to cause exceptions
   at runtime on user machines where errors are harder to capture.
