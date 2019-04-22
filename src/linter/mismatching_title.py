import sublime
import sublime_plugin

from hyperhelpcore.core import parse_help_header

from ..linter_base import LinterBase


###----------------------------------------------------------------------------


class MismatchingTitleLinter(LinterBase):
    """
    Lint the help index to ensure that the title that is declared for files in
    the index matches the title in the source help file itself.
    """
    def lint(self, view, file_name):
        first_line = view.substr(view.full_line(0))
        header = parse_help_header(file_name, first_line)

        if header is None:
            return self.add(view, "error", file_name, 0,
                            "File '%s' does not have a help header", file_name)

        index_title = self.pkg_info.help_files[file_name]
        file_title = header.title

        if index_title != file_title:
            self.add(view, "warning", file_name, 0,
                     "Title in file header for '%s' does not match the index",
                     file_name)


###----------------------------------------------------------------------------
