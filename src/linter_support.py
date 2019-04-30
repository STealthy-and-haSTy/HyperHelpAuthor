import sublime
import sublime_plugin

import os
from collections import OrderedDict, namedtuple
import codecs

from hyperhelpcore.common import log, hh_syntax
from hyperhelpcore.core import help_index_list, lookup_help_topic
from hyperhelpcore.core import parse_help_header, parse_anchor_body, parse_link_body
from hyperhelpcore.core import is_topic_file_valid

from .linter_base import LintTarget
from .common import hha_setting

from .linter import HelpAnchorLinter
from .linter import HelpLinkLinter
from .linter import MissingHelpSourceLinter
from .linter import MismatchingTitleLinter
from .linter import MissingInTOCLinter
from .linter import UnlinkedHelpFilesLinter


###----------------------------------------------------------------------------


def _find_or_create_output_view(window, target):
    """
    Find or create a view in the current window for putting the lint output in.
    This is used when lint_output_to_view is set to True to create the view for
    the lint results to be displayed in.
    """
    caption = {
        "package": "HyperHelpAuthor Lint: {pkg}",
        "single":  "HyperHelpAuthor Lint: {target} ({pkg})"
    }.get(target.target_type, "???").format(
        target=target.files[0],
        pkg=target.pkg_info.package)

    for view in window.views():
        if view.name().startswith("HyperHelpAuthor Lint"):
            view.set_name(caption)
            view.set_read_only(False)
            view.run_command("select_all")
            view.run_command("left_delete")
            return view

    view = window.new_file()
    view.set_name(caption)
    view.set_scratch(True)

    return view


###----------------------------------------------------------------------------


def can_lint_view(view):
    """
    Determine if the provided view can be the source of a lint. To be valid
    the view must represent a hyperhelp data file that has a path rooted in the
    Packages folder inside of a package whose help index is known.
    """
    if (view is not None and view.file_name() is not None and
            view.file_name().startswith(sublime.packages_path()) and
            view.match_selector(0, "text.hyperhelp")):

        # Make the path relative to the packages folder, then throw the
        # filename away, which should be a document root.
        name = os.path.relpath(view.file_name(), sublime.packages_path())
        name = os.path.split(name)[0].replace("\\", "/")

        for info in help_index_list().values():
            if info.doc_root == name:
                return True

    return False


def find_lint_target(view):
    """
    Examine a given view and return a LintTarget that describes what is being
    linted. None is returned if the view is not a valid lint target.
    """
    if not can_lint_view(view):
        return None

    # Make the path relative to the packages folder, then get both the path
    # and the file name parts.
    name = os.path.relpath(view.file_name(), sublime.packages_path())
    name, target = os.path.split(name)
    name = name.replace("\\", "/")

    # Use the location as the document root to find the appropriate package.
    for info in help_index_list().values():
        if info.doc_root == name:
            pkg_name = info.package

    pkg_info = help_index_list().get(pkg_name)

    if view.match_selector(0, "text.hyperhelp.help"):
        return LintTarget("single", pkg_info, [target])

    return LintTarget("package", pkg_info, list(pkg_info.help_files))


def get_linters(target):
    """
    Given a LintTarget, return back an array of all of the linters that should
    be run for that target.

    Some targets may only be run on the package as a whole while others may be
    allowed on a file by file basis. The returned linters may also be affected
    by user settings.
    """
    linters = []
    linters.append(HelpAnchorLinter(target.pkg_info))
    linters.append(HelpLinkLinter(target.pkg_info))

    if target.target_type == "package":
        linters.append(MissingHelpSourceLinter(target.pkg_info))
        linters.append(MismatchingTitleLinter(target.pkg_info))
        linters.append(MissingInTOCLinter(target.pkg_info))
        linters.append(UnlinkedHelpFilesLinter(target.pkg_info))

    return linters


def get_lint_file(filename):
    """
    Return a view that that contains the contents of the provided file name.
    If the file is not aready loaded, it is loaded into a hidden view and that
    is returned instead.

    Can return None if the file is not open and cannot be loaded.
    """
    for window in sublime.windows():
        view = window.find_open_file(filename)
        if view is not None:
            return view

    content = None
    try:
        # TODO: This will break if we lint a packed package
        with codecs.open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
    except:
        pass

    if content:
        view = sublime.active_window().create_output_panel("_hha_tmp", True)
        view.run_command("select_all")
        view.run_command("left_delete")
        view.run_command("append", {"characters": content})
        view.assign_syntax(hh_syntax("HyperHelp-Help.sublime-syntax"))
        return view

    return None


def format_lint(target, issues, window=None):
    """
    Takes a list of LintResult issues for a package and returns back output
    suitable for passing to display_lint().

    If a window is provided, display_lint() is called prior to returning in
    order to display the output first.
    """
    files = OrderedDict()
    for issue in issues:
        if issue.file not in files:
            files[issue.file] = []
        files[issue.file].append(issue)

    if target.target_type == "package":
        output = ["Linting help package: {pkg}\n".format(
            pkg=target.pkg_info.package)]
    else:
        output = ["Linting {target} in help package: {pkg}\n".format(
            target=target.files[0],
            pkg=target.pkg_info.package)]

    warn = 0
    err = 0
    for file in files:
        output.append("%s:" % file)

        for issue in files[file]:
            issue_pos = "%d:%d" % (issue.line, issue.column)
            output.append("    %-7s @ %-7s %s" % (
                issue.type, issue_pos, issue.message))

            if issue.type == "warning":
                warn += 1
            elif issue.type == "error":
                err += 1

        output.append("")

    output.append("%d warning%s, %d error%s" % (
        warn,
        "" if warn == 1 else "s",
        err,
        "" if err == 1 else "s"))

    if window:
        display_lint(window, target, output)

    return output


def display_lint(window, target, output):
    """
    Display the lint output provided into the given window. The output is
    assumed to have been generated from the provided package, which is used to
    know where the help files are located.
    """
    if hha_setting("lint_output_to_view"):
        prev_view = window.active_view()
        view = _find_or_create_output_view(window, target)
    else:
        view = window.create_output_panel("HyperHelpAuthor Lint", False)

    basedir = os.path.join(sublime.packages_path(), target.pkg_info.doc_root)
    # print("encoding:", view.encoding())

    if not isinstance(output, str):
        output = "\n".join(output)

    view.assign_syntax(hh_syntax("HyperHelpLinter.sublime-syntax"))

    settings = view.settings()
    settings.set("result_base_dir", basedir)
    settings.set("result_file_regex", r"^([^:]+):$")
    settings.set("result_line_regex", r"^.*?@ (\d+):(\d+)\s+(.*)$")

    view.set_read_only(False)
    view.run_command("append", {"characters": output})
    view.set_read_only(True)

    if hha_setting("lint_output_to_view"):
        # In views, find results fail until the focus is lost and regained.
        # This is a bug in Sublime, so work around it by changing the focus.
        window.focus_view(prev_view)
        window.focus_view(view)
    else:
        window.run_command("show_panel", {"panel": "output.HyperHelpAuthor Lint"})


###----------------------------------------------------------------------------
