import sublime
import sublime_plugin

from hyperhelpcore.core import lookup_help_topic
from hyperhelpcore.core import parse_anchor_body

from ..linter_base import LinterBase


###----------------------------------------------------------------------------


class MissingInTOCLinter(LinterBase):
    """
    Lint in the help index to find all help files that appear in the index but
    which don't appear at least one in the defined table of contents.
    """
    def __init__(self, pkg_info):
        super().__init__(pkg_info)

        help_files = {file for file in pkg_info.help_files}
        toc_files = {topic["file"] for topic in pkg_info.help_toc}

        for file in help_files - toc_files:
            self.add_index(
                "warning",
                "Help file '%s' is not represented in the table of contents",
                file)


###----------------------------------------------------------------------------
