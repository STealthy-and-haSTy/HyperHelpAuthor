import sublime
import sublime_plugin

import os

from hyperhelpcore.common import log
from hyperhelpcore.core import help_index_list


###----------------------------------------------------------------------------


class HyperhelpAuthorReloadIndexCommand(sublime_plugin.TextCommand):
    """
    If the current view is a hyperhelp index view, this will attempt to reload
    the help index so that the current changes will immediately take effect.

    This will work both for an index file that is directly contained within
    the Packages folder as well as for any file that is a symlink to a file
    in the Packages folder.
    """
    def run(self, edit):
        filename = self.filename()
        if filename is None:
            return log("Cannot reload help index; not in package", status=True)

        # Make the filename be relative to the Packages folder.
        filename = os.path.relpath(filename, sublime.packages_path())
        filename = os.path.join("Packages/", filename)

        # Flip the help index structure so we can look up the package based on
        # the index file instead of the other way around.
        indexes = {value.index_file: key for key, value in help_index_list().items()}

        # If this index is known, reload it's package; otherwise rescan all
        # packages in order to bring this one in.
        package = None if filename not in indexes else indexes[filename]

        help_index_list(reload=True, package=package)

    def is_enabled(self):
        return (self.view.match_selector(0, "text.hyperhelp.index") and
                self.view.file_name() is not None)

    def filename(self):
        filename = self.view.file_name()
        if filename.startswith(sublime.packages_path()):
            return filename

        filename = os.path.realpath(filename)
        if filename.startswith(sublime.packages_path()):
            return filename


###----------------------------------------------------------------------------
