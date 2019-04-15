import sublime
import sublime_plugin

import os
import posixpath
import codecs
import datetime
import re

from hyperhelpcore.common import log, help_package_prompt
from hyperhelpcore.common import current_help_package, current_help_file
from hyperhelpcore.core import help_index_list, load_help_index, reload_help_file
from hyperhelpcore.view import find_help_view

from .src.common import format_template, is_authoring_source
from .src.common import local_help_filename, open_local_help
from .src.common import open_help_index, apply_authoring_settings
from .src.common import package_for_view

from .src.linter import can_lint_view, find_lint_target, get_linters
from .src.linter import get_lint_file, format_lint


###----------------------------------------------------------------------------


# TODO: The code in help_index.py uses posixpath as the path module instead of
# os.path because in packages all files are posix. There is probably going to
# be interplay with that in this code in an unfortunate way since it needs to
# work with local files and match them to resources.


# Match a help header line focusing on the date field.
_header_date_re = re.compile(r'^(%hyperhelp.*\bdate=")(\d{4}-\d{2}-\d{2})(".*)')


###----------------------------------------------------------------------------


def _error_dialog(message, *args):
    """
    Simple local helper for displaying an error dialog using the log function.
    """
    log(format_template(message, *args), dialog=True)


def _global_package_list(filter_with_help=True):
    """
    Yield a list of packages that Sublime currently knows about (those that
    have at least one resource and are not ignored), optionally filtering away
    packages that have help indexes defined currently.

    The list is yielded in package load order.
    """
    pkg_set = set()
    for res in sublime.find_resources(''):
        if res.startswith("Packages/"):
            pkg_set.add(res.split("/")[1])

    if filter_with_help:
        pkg_set -= set([pkg.package for pkg in help_index_list().values()])

    if "Default" in pkg_set:
        yield "Default"

    for pkg in sorted(pkg_set):
        if pkg not in ["Default", "User"]:
            yield pkg

    if "User" in pkg_set:
        yield "User"

# TODO: This should use a template from a file resource instead
def _make_help_index(package, doc_root, index_path):
    """
    Create an empty help index for the provided package at the given index
    path location.
    """
    template = format_template(
        """
        {{
            "package": "{pkg}",
            "description": "Help for {pkg} Package",
            "doc_root": "{root}",

            "help_files": {{
                "index.txt": [
                    "Index file for {pkg} package",

                    {{
                        "topic": "index.txt",
                        "caption": "Index file",
                        "aliases": ["index file"]
                    }}
                ]
            }},

            "help_contents": [
                "index.txt"
            ]
        }}
        """.format(pkg=package, root=doc_root))
    with codecs.open(index_path, 'w', 'utf-8') as handle:
        handle.write(template)

# TODO: This should use a template from a file resource instead
def _make_root_help(package, help_path):
    """
    Create a stub root help file (index.txt) at the provided help path.
    """
    template = format_template(
        """
        %%hyperhelp title="Index file for {pkg} package" date="{date}"

        This is the root help file for the '{pkg}' package.
        """.format(
            pkg=package,
            date=datetime.date.today().strftime("%Y-%m-%d")))

    with codecs.open(help_path, 'w', 'utf-8') as handle:
        handle.write(template)


###----------------------------------------------------------------------------


# TODO: Maybe this could be partiall done in the core or something; at the
# very least, can we get the core to be the only place where the regex for
# this is stored, so that this package will always work?
class HyperhelpAuthorUpdateHeaderCommand(sublime_plugin.TextCommand):
    """
    If the current file is a help file that contains a header with a last
    modified date field, this will update the date field to be the current
    date. Quiet controls if the status line shows status about this or not.
    """
    def run(self, edit, quiet=False):
        now = datetime.date.today().strftime("%Y-%m-%d")

        h_line = self.view.line(0)
        header = self.view.substr(h_line)

        msg = "Help file date header is already current"
        match = _header_date_re.match(header)
        if match and match.group(2) != now:
            header = match.expand(r'\g<1>%s\g<3>' % now)
            self.view.replace(edit, h_line, header)

            msg = "Help file date header updated to the most recent date"

        if not quiet:
            log(msg, status=True)


    def is_enabled(self, quiet=False):
        return is_authoring_source(self.view)


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


class HyperhelpAuthorCreateIndexCommand(sublime_plugin.WindowCommand):
    """
    Create a new empty help system in the package provided, prompting for the
    package if none is given. This will create the package index and a stub
    help file and reload the help index.
    """
    def run(self, package=None, doc_root=None):
        if package is None:
            items = list(_global_package_list())

            def pick(i):
                if i >= 0:
                    self.run(items[i], doc_root)

            return self.window.show_quick_panel(items=items,
                                                on_select=lambda i: pick(i))

        if package in help_index_list():
            return _error_dialog(
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
                return _error_dialog(
                    """
                    Help index file already exists in package:
                        '%s'

                    This may indicate that the index is broken and
                    cannot be loaded.
                    """, package)

            if os.path.exists(help_path):
                return _error_dialog(
                    """
                    Root help file already exists in package:
                        '%s'

                    This may indicate that an existing help index
                    for this package is broken and cannot be
                    loaded.
                    """, package)

            try:
                os.makedirs(root_path, exist_ok=True)
                _make_help_index(package, doc_root, index_path)
                _make_root_help(package, help_path)

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
                return _error_dialog(
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
            return _error_dialog(
                """
                Invalid document root specified:
                    '%s'

                The document root must be contained within the
                package itself.
                """, doc_root)

        return help_path


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


class HyperhelpAuthorReloadHelpCommand(sublime_plugin.TextCommand):
    """
    If the current view is a hyperhelp help view, this will reload the file
    currently being displayed in the view.
    """
    def run(self, edit):
        # Running directly on the help view
        settings = self.view.settings()
        if settings.has("_hh_pkg") and settings.has("_hh_file"):
            return self.reload(self.view, current_help_file())

        # File must have a name and be in the packages folder.
        name = self.view.file_name()
        if name is None or not name.startswith(sublime.packages_path()):
            return log("Unable to reload help; help file is not in a package",
                       status=True)

        name = os.path.relpath(name, sublime.packages_path())
        pkg = name.split(os.sep)[0]
        file = os.path.split(name)[1]

        if pkg == current_help_package() and file == current_help_file():
            return self.reload(find_help_view(), file)

        log("Unable to reload help; this is not the current help file",
            status=True)

    def is_enabled(self):
        return self.view.match_selector(0, "text.hyperhelp.help")

    def reload(self, help_view, help_file):
        viewport = help_view.viewport_position()
        caret = help_view.sel()[0].b

        if reload_help_file(help_index_list(), help_view):
            help_view.sel().clear()
            help_view.sel().add(sublime.Region(caret))
            help_view.set_viewport_position(viewport, False)
            log("Reloaded help file '%s'", help_file, status=True)


class HyperhelpAuthorReloadIndexCommand(sublime_plugin.TextCommand):
    """
    If the current view is a hyperhelp index view, this will attempt to reload
    the help index so that the current changes will immediately take effect.

    This will work both for an index file that is directly contained within
    the Packages folder as well as for any file that is a symlink to a file
    in the Packages folder.
    """
    def run(self, edit):
        filename = self.filename()
        if filename is None:
            return log("Cannot reload help index; not in package", status=True)

        # Make the filename be relative to the Packages folder.
        filename = os.path.relpath(filename, sublime.packages_path())
        filename = os.path.join("Packages/", filename)

        # Flip the help index structure so we can look up the package based on
        # the index file instead of the other way around.
        indexes = {value.index_file: key for key, value in help_index_list().items()}

        # If this index is known, reload it's package; otherwise rescan all
        # packages in order to bring this one in.
        package = None if filename not in indexes else indexes[filename]

        help_index_list(reload=True, package=package)

    def is_enabled(self):
        return (self.view.match_selector(0, "text.hyperhelp.index") and
                self.view.file_name() is not None)

    def filename(self):
        filename = self.view.file_name()
        if filename.startswith(sublime.packages_path()):
            return filename

        filename = os.path.realpath(filename)
        if filename.startswith(sublime.packages_path()):
            return filename


class HyperhelpAuthorLintCommand(sublime_plugin.WindowCommand):
    def run(self):
        target = find_lint_target(self.window.active_view())
        linters = get_linters(target)

        spp = sublime.packages_path()
        doc_root = target.pkg_info.doc_root

        for file in target.files:
            view = get_lint_file(os.path.join(spp, doc_root, file))
            if view is not None:
                for linter in linters:
                    linter.lint(view, file)

            else:
                log("Unable to lint '%s' in '%s'", file, target.pkg_info.package)

        issues = list()
        for linter in linters:
            issues += linter.results()

        format_lint(target.pkg_info, issues, self.window)

    def is_enabled(self):
        return can_lint_view(self.window.active_view())


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
