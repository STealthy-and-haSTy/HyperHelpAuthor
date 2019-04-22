import sublime
import sublime_plugin

from hyperhelpcore.core import lookup_help_topic, help_index_list
from hyperhelpcore.core import parse_link_body

from ..linter_base import LinterBase


###----------------------------------------------------------------------------


class UnlinkedHelpFilesLinter(LinterBase):
    """
    Lint in the help index to find all help files that appear in the index but
    which don't appear at least one in the defined table of contents.
    """
    def __init__(self, pkg_info):
        super().__init__(pkg_info)

        self.help_files = {file for file in pkg_info.help_files}
        self.linked_files = set(["index.txt"])

    def lint(self, view, file_name):
        for pos in view.find_by_selector("meta.link"):
            link_body = view.substr(pos)
            pkg, topic, text = parse_link_body(link_body)

            file = self.validate(pkg, topic, file_name)
            if file is not None:
                self.linked_files.add(file)

    def validate(self, pkg, topic, file_name):
        if topic is None:
            return None

        link_pkg = self.pkg_info if pkg is None else help_index_list().get(pkg)
        if link_pkg is None or link_pkg.package != self.pkg_info.package:
            return None

        index_info = lookup_help_topic(link_pkg, topic)
        if index_info is None:
            return None

        if index_info["file"] == file_name:
            return None

        return index_info["file"]

    def results(self):
        for file in self.help_files - self.linked_files:
            self.add_index(
                "warning",
                "Help file '%s' is not linked to from any other file in this package",
                file)

        return super().results()


###----------------------------------------------------------------------------
