import sublime
import sublime_plugin

from hyperhelpcore.common import current_help_package

from ..common import package_for_view


###----------------------------------------------------------------------------


class HyperhelpAuthorContextEditIndexCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pkg = current_help_package(self.view, self.view.window())
        if pkg is None:
            pkg_info = package_for_view(self.view)
            if pkg_info is not None:
                pkg = pkg_info.package

        if pkg is not None:
            self.view.window().run_command("hyperhelp_author_edit_index", {
                "package": pkg
                })

    def is_enabled(self):
        return self.view.match_selector(0, "text.hyperhelp.help")

    def is_visible(self):
        return self.is_enabled()


###----------------------------------------------------------------------------
