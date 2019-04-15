import sublime
import sublime_plugin

from hyperhelpcore.common import current_help_package, current_help_file


###----------------------------------------------------------------------------


class HyperhelpAuthorContextEditHelpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pkg = current_help_package(self.view, self.view.window())
        file = current_help_file(self.view, self.view.window())

        self.view.window().run_command("hyperhelp_author_edit_help", {
            "package": pkg,
            "file": file
            })

    def is_enabled(self):
        if self.view.match_selector(0, "text.hyperhelp.help"):
            return self.view.is_read_only()

        return False

    def is_visible(self):
        return self.is_enabled()


###----------------------------------------------------------------------------
