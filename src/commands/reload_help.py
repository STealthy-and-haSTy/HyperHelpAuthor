from __future__ import annotations

import sublime
import sublime_plugin  # noqa: F401

import os

from HyperHelp.helpcore.common import log, current_help_package, current_help_file
from HyperHelp.helpcore.core import help_index_list, reload_help_file
from HyperHelp.helpcore.view import find_help_view

from ..common import AuthorTextCommand


###----------------------------------------------------------------------------


class HyperhelpAuthorReloadHelpCommand(AuthorTextCommand):
    """
    If the current view is a hyperhelp help view, this will reload the file
    currently being displayed in the view.
    """
    def run(self, edit: sublime.Edit) -> None:
        # Running directly on the help view
        settings = self.view.settings()
        if settings.has("_hh_pkg") and settings.has("_hh_file"):
            current_file = current_help_file()
            if current_file is not None:
                return self.reload(self.view, current_file)

        # File must have a name and be in the packages folder.
        name = self.view.file_name()
        if name is None or not name.startswith(sublime.packages_path()):
            return log("Unable to reload help; help file is not in a package",
                       status=True)

        name = os.path.relpath(name, sublime.packages_path())
        pkg = name.split(os.sep)[0]
        file = os.path.split(name)[1]

        current_file = current_help_file()
        if pkg == current_help_package() and current_file is not None and file == current_file:
            help_view = find_help_view()
            if help_view is not None:
                return self.reload(help_view, file)

        log("Unable to reload help; this is not the current help file",
            status=True)

    def is_enabled(self, *args: sublime.Value, **kwargs: sublime.Value) -> bool:
        if not super().is_enabled():
            return False

        return self.view.match_selector(0, "text.hyperhelp.help")

    def reload(self, help_view: sublime.View, help_file: str) -> None:
        viewport = help_view.viewport_position()
        caret = help_view.sel()[0].b

        if reload_help_file(help_index_list(), help_view):
            help_view.sel().clear()
            help_view.sel().add(sublime.Region(caret))
            help_view.set_viewport_position(viewport, False)
            log("Reloaded help file '%s'", help_file, status=True)


###----------------------------------------------------------------------------
