import sublime
import sublime_plugin

import os
import posixpath

from .common import error_dialog, global_package_list
from .common import make_help_index, make_root_help

from hyperhelpcore.common import log
from hyperhelpcore.core import help_index_list, load_help_index

from ..common import format_template


###----------------------------------------------------------------------------


class HyperhelpAuthorCreateIndexCommand(sublime_plugin.WindowCommand):
    """
    Create a new empty help system in the package provided, prompting for the
    package if none is given. This will create the package index and a stub
    help file and reload the help index.
    """
    def run(self, package=None, doc_root=None):
        if package is None:
            items = list(global_package_list())

            def pick(i):
                if i >= 0:
                    self.run(items[i], doc_root)

            return self.window.show_quick_panel(items=items,
                                                on_select=lambda i: pick(i))

        if package in help_index_list():
            return error_dialog(
                """
                Specified package already has help defined:
                    '%s'

                Use the Edit Help Index command to edit the
                existing help system in this package.
                """, package)

        if doc_root is not None:
            return self.create_index(package, doc_root)

        self.window.show_input_panel("Document Root: Packages/%s/" % package,
                                     "help/",
                                     lambda r: self.create_index(package, r),
                                     None, None)

    def create_index(self, package, doc_root):
        root_path = self.make_document_root(package, doc_root)
        if root_path is not None:
            index_path = os.path.join(root_path, "hyperhelp.json")
            help_path = os.path.join(root_path, "index.txt")

            if os.path.exists(index_path):
                return error_dialog(
                    """
                    Help index file already exists in package:
                        '%s'

                    This may indicate that the index is broken and
                    cannot be loaded.
                    """, package)

            if os.path.exists(help_path):
                return error_dialog(
                    """
                    Root help file already exists in package:
                        '%s'

                    This may indicate that an existing help index
                    for this package is broken and cannot be
                    loaded.
                    """, package)

            try:
                os.makedirs(root_path, exist_ok=True)
                make_help_index(package, doc_root, index_path)
                make_root_help(package, help_path)

                res = posixpath.join("Packages", package, doc_root, "hyperhelp.json")
                new_pkg_info = load_help_index(res)
                if new_pkg_info is None:
                    raise IOError("Unable to load new help index")

                help_index_list()[package] = new_pkg_info

                msg = format_template(
                    """
                    Initial help files created for package:
                       '%s'
                          -> %s
                          -> %s

                    """,
                    package,
                    posixpath.join(doc_root, "hyperhelp.json"),
                    posixpath.join(doc_root, "index.txt"))

                # Prompt the user to see if they want to open the files just
                # created or not.
                if sublime.ok_cancel_dialog(msg, "Open created files"):
                    self.window.run_command("hyperhelp_author_edit_index",
                                           {"package": package})
                    self.window.run_command("hyperhelp_author_edit_help",
                                            {"package": package,
                                            "file": "index.txt"})

                    # This relies on load_resource() being able to load a
                    # resource that find_resources() can't find yet; might
                    # need to make help loading open local files as for
                    # indexes.
                    sublime.run_command("hyperhelp_topic",
                                        {"package": package,
                                        "topic": "index.txt"})


            except Exception as err:
                log("Error: %s", str(err))
                return error_dialog(
                    """
                    Error adding help to package:
                        '%s'

                    Unable to create the document root, index file
                    or root help file.
                    """, package)

    # TODO: Maybe this should ensure that the document root is always in the
    # appropriate path format for posix.
    def make_document_root(self, package, doc_root):
        help_path = os.path.join(sublime.packages_path(), package, doc_root)
        help_path = os.path.normpath(help_path)

        if not help_path.startswith(sublime.packages_path()):
            return error_dialog(
                """
                Invalid document root specified:
                    '%s'

                The document root must be contained within the
                package itself.
                """, doc_root)

        return help_path


###----------------------------------------------------------------------------
