import sublime
import sublime_plugin

import os
import datetime

from hyperhelpcore.common import log, help_package_prompt, current_help_package
from hyperhelpcore.core import help_index_list

from ..common import format_template
from ..common import local_help_filename
from ..common import apply_authoring_settings


###----------------------------------------------------------------------------


# TODO: This should perhaps have a customizable snippet to fill out the help
# file.
class HyperhelpAuthorCreateHelpCommand(sublime_plugin.WindowCommand):
    """
    Create a new help file in the package provided. If no package is given and
    one cannot be inferred from the current help view, the user will be
    prompted to supply one. The prompt always occurs if the argument asks.
    """
    def run(self, package=None, file=None, prompt=False):
        package = package or current_help_package(window=self.window)
        if package is None or prompt:
            return help_package_prompt(help_index_list(),
                                       on_select=lambda p: self.run(p, file))

        if help_index_list().get(package, None) is None:
            return log("Cannot add help file; package '%s' unknown", package,
                       dialog=True)

        if file is not None:
            return self.create_file(package, file)

        self.window.show_input_panel("New Help File (%s)" % package, "",
                                     lambda file: self.create_file(package, file),
                                     None, None)

    def create_file(self, package, file):
        if not file:
            return log("No help file given; skipping creation", status=True)

        pkg_info = help_index_list().get(package)
        local_path = local_help_filename(pkg_info, file)

        help_file = os.path.split(local_path)

        os.makedirs(help_file[0], exist_ok=True)

        view = self.window.new_file()
        view.settings().set("_hh_auth", True)
        view.settings().set("default_dir", help_file[0])
        view.set_name(help_file[1])
        apply_authoring_settings(view)

        template = format_template(
            """
            %%hyperhelp title="${1:Title}" date="${2:%s}"

            $0
            """,
            datetime.date.today().strftime("%Y-%m-%d"))

        view.run_command("insert_snippet", {"contents": template})


###----------------------------------------------------------------------------
