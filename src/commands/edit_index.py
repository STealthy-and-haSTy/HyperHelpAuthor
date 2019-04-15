import sublime
import sublime_plugin

from hyperhelpcore.common import log, help_package_prompt, current_help_package
from hyperhelpcore.core import help_index_list

from ..common import open_help_index


###----------------------------------------------------------------------------


class HyperhelpAuthorEditIndexCommand(sublime_plugin.WindowCommand):
    """
    Open the index for the help package provided. If no package is given and one
    cannot be inferred from the current help view, the user will be prompted to
    supply one. The prompt always occurs if the argument asks.
    """
    def run(self, package=None, prompt=False):
        package = package or current_help_package(window=self.window)
        if package is None or prompt:
            return help_package_prompt(help_index_list(),
                                       on_select=lambda pkg: self.run(pkg))

        pkg_info = help_index_list().get(package, None)
        if pkg_info is None:
            return log("Cannot edit help file; package '%s' unknown", package,
                       dialog=True)

        open_help_index(pkg_info)


###----------------------------------------------------------------------------
