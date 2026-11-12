from __future__ import annotations

import sublime         # noqa: F401
import sublime_plugin  # noqa: F401

from HyperHelp.helpcore.common import current_help_package

from ..common import AuthorTextCommand, package_for_view


###----------------------------------------------------------------------------


class HyperhelpAuthorContextEditIndexCommand(AuthorTextCommand):
    def run(self, edit: sublime.Edit) -> None:
        window = self.view.window()
        if window is None:
            return

        pkg = current_help_package(self.view, window)
        if pkg is None:
            pkg_info = package_for_view(self.view)
            if pkg_info is not None:
                pkg = pkg_info.package

        if pkg is not None:
            window.run_command("hyperhelp_author_edit_index", {
                "package": pkg
                })

    def is_enabled(self, *args: sublime.Value, **kwargs: sublime.Value) -> bool:
        if not super().is_enabled():
            return False

        return self.view.match_selector(0, "text.hyperhelp.help")

    def is_visible(self, *args: sublime.Value, **kwargs: sublime.Value) -> bool:
        return self.is_enabled()


###----------------------------------------------------------------------------
