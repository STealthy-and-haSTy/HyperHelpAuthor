import sublime
import sublime_plugin

from ..linter_base import LinterBase


###----------------------------------------------------------------------------


class MissingHelpSourceLinter(LinterBase):
    """
    Lint the help index to determine if the list of help files listed in the
    index matches the list of help files that exist for the package.
    """
    def __init__(self, pkg_info):
        super().__init__(pkg_info)

        root = "Packages/%s/" % (self.pkg_info.doc_root)
        d_files = {file[len(root):] for file in sublime.find_resources("*.txt")
                      if file.startswith(root)}

        i_files = {key for key in self.pkg_info.help_files.keys()}

        for file in d_files - i_files:
            self.add_index(
                "warning",
                "Help file '%s' is in Packages/%s/ but missing from the index",
                file, self.pkg_info.doc_root)

        for file in i_files - d_files:
            self.add_index(
                "error",
                "Help file '%s' is in the index but not in Packages/%s/",
                file, self.pkg_info.doc_root)


###----------------------------------------------------------------------------
