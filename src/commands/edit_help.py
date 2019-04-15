import sublime
import sublime_plugin

from hyperhelpcore.common import log, help_package_prompt, current_help_package
from hyperhelpcore.core import help_index_list

from ..common import open_local_help


###----------------------------------------------------------------------------


class HyperhelpAuthorEditHelpCommand(sublime_plugin.WindowCommand):
    """
    Open an existing help file from the package provided. If no package is
    given and one cannot be inferred from the current help view, the user will
    be prompted to supply one. The prompt always occurs if the argument asks.
    """
    def run(self, package=None, file=None, prompt=False):
        package = package or current_help_package(window=self.window)
        if package is None or prompt:
            return help_package_prompt(help_index_list(),
                                       on_select=lambda p: self.run(p, file))

        pkg_info = help_index_list().get(package, None)
        if pkg_info is None:
            return log("Cannot edit help file; package '%s' unknown", package,
                       dialog=True)

        files = pkg_info.help_files
        items = [[key, files[key]] for key in files]

        if not items:
            return log("The help index for '%s' lists no help files", package,
                       dialog=True)

        if file is not None:
            return open_local_help(pkg_info, file, window=self.window)

        def pick(index):
            if index >= 0:
                open_local_help(pkg_info, items[index][0], window=self.window)

        self.window.show_quick_panel(
            items=items,
            on_select=lambda index: pick(index))


###----------------------------------------------------------------------------
