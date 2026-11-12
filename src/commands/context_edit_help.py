from __future__ import annotations

import sublime         # noqa: F401
import sublime_plugin  # noqa: F401

from HyperHelp.helpcore.common import current_help_package, current_help_file

from ..common import AuthorTextCommand


###----------------------------------------------------------------------------


class HyperhelpAuthorContextEditHelpCommand(AuthorTextCommand):
    def run(self, edit: sublime.Edit) -> None:
        window = self.view.window()
        if window is None:
            return

        pkg = current_help_package(self.view, window)
        file = current_help_file(self.view, window)

        window.run_command("hyperhelp_author_edit_help", {
            "package": pkg,
            "file": file
            })

    def is_enabled(self, *args: sublime.Value, **kwargs: sublime.Value) -> bool:
        if not super().is_enabled():
            return False

        if self.view.match_selector(0, "text.hyperhelp.help"):
            return self.view.is_read_only()

        return False

    def is_visible(self, *args: sublime.Value, **kwargs: sublime.Value) -> bool:
        return self.is_enabled()


###----------------------------------------------------------------------------
