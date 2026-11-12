from __future__ import annotations

import sublime         # noqa: F401
import sublime_plugin  # noqa: F401

import datetime

from .common import header_date_re

from HyperHelp.helpcore.common import log

from ..common import AuthorTextCommand, is_authoring_source


###----------------------------------------------------------------------------


# TODO: Maybe this could be partiall done in the core or something; at the
# very least, can we get the core to be the only place where the regex for
# this is stored, so that this package will always work?
class HyperhelpAuthorUpdateHeaderCommand(AuthorTextCommand):
    """
    If the current file is a help file that contains a header with a last
    modified date field, this will update the date field to be the current
    date. Quiet controls if the status line shows status about this or not.
    """
    def run(self, edit: sublime.Edit, quiet: bool = False) -> None:
        now = datetime.date.today().strftime("%Y-%m-%d")

        h_line = self.view.line(0)
        header = self.view.substr(h_line)

        msg = "Help file date header is already current"
        match = header_date_re.match(header)
        if match and match.group(2) != now:
            header = match.expand(r'\g<1>%s\g<3>' % now)
            self.view.replace(edit, h_line, header)

            msg = "Help file date header updated to the most recent date"

        if not quiet:
            log(msg, status=True)


    def is_enabled(self, quiet: bool = False, *args: sublime.Value,
                   **kwargs: sublime.Value) -> bool:
        if not super().is_enabled():
            return False

        return is_authoring_source(self.view)


###----------------------------------------------------------------------------
