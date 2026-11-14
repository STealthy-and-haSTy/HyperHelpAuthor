import sublime
import sublime_plugin

import os
import textwrap

from HyperHelp.helpcore.common import log, hh_syntax
from HyperHelp.helpcore.core import help_index_list


###----------------------------------------------------------------------------


# Whether or not HyperHelp was installed and available at the time that the
# package was loaded.
#
# The value here is used by the command sub classes below to know whether or
# not our core commands should be enabled or not.
_hyperhelp_enabled = False


###----------------------------------------------------------------------------


def _check_hh_enabled():
    """
    A simple function which determines if HyperHelp is currently an available
    package in the system. This is done by checking to see if its Help index is
    available or not.

    The return value is True if HyperHelp is installed and available, and False
    otherwise.

    Note that if HyperHelp is installed but in ignored_packages, this will
    return False even though imports of functionality from within it will still
    function as expected.
    """
    return bool([res for res in sublime.find_resources('hyperhelp.json')
                 if "/HyperHelp/" in res])


###----------------------------------------------------------------------------


def loaded():
    """
    Do package setup at package load time.
    """
    global _hyperhelp_enabled
    _hyperhelp_enabled = _check_hh_enabled()
    if not _hyperhelp_enabled:
        sublime.message_dialog(textwrap.dedent("""
            HyperHelpAuthor requires the HyperHelp package to be enabled in
            order operate.

            HyperHelp is installed, but currently disabled. Re-enable HyperHelp
            and restart Sublime to enable HyperHelpAuthor commands and
            functionality.
        """))

    hha_setting.obj = sublime.load_settings("HyperHelpAuthor.sublime-settings")
    hha_setting.default = {
        "update_header_on_save": True,
        "reload_index_on_save": True,
        "lint_output_to_view": False,
        "author_view_settings": {
            "rulers": [80],
            "match_selection": True,
            "draw_indent_guides": True
        }
    }


def unloaded():
    """
    Do package cleanup at unload time.
    """
    pass


###----------------------------------------------------------------------------


def is_hyperhelp_enabled():
    """
    Returns True or False to indicate if HyperHelp was active and available at
    the point at which the plugin loaded.
    """
    return _hyperhelp_enabled


###----------------------------------------------------------------------------


class AuthorTextCommand(sublime_plugin.TextCommand):
    """
    Custom base class for an authoring text commands; such commands hide and
    disable themselves if HyperHelp was installed and not disabled at the time
    that the package loaded.
    """
    def is_visible(self, *args, **kwargs):
        return _hyperhelp_enabled

    def is_enabled(self, *args, **kwargs):
        return _hyperhelp_enabled


class AuthorWindowCommand(sublime_plugin.WindowCommand):
    """
    Custom base class for an authoring window commands; such commands hide and
    disable themselves if HyperHelp was installed and not disabled at the time
    that the package loaded.
    """
    def is_visible(self, *args, **kwargs):
        return _hyperhelp_enabled

    def is_enabled(self, *args, **kwargs):
        return _hyperhelp_enabled


class AuthorApplicationCommand(sublime_plugin.ApplicationCommand):
    """
    Custom base class for an authoring application commands; such commands hide
    and disable themselves if HyperHelp was installed and not disabled at the
    time that the package loaded.
    """
    def is_visible(self, *args, **kwargs):
        return _hyperhelp_enabled

    def is_enabled(self, *args, **kwargs):
        return _hyperhelp_enabled


###----------------------------------------------------------------------------


def hha_setting(key):
    """
    Get a HyperHelpAuthor setting from a cached settings object.
    """
    default = hha_setting.default.get(key, None)
    return hha_setting.obj.get(key, default)


def is_authoring_source(view):
    """
    Given a view object, tells you if that view represents a help source file.
    """
    if view.match_selector(0, "text.hyperhelp.help"):
        return not view.is_read_only()

    return False


def package_for_view(view):
    """
    Given a view object, provides you back the help index tuple for the help
    package that contains this file. This may be None if this file is not a
    Sublime package file, or if it doesn't correspond to a loaded help package.

    This does not verify that the file is actually a part of the provided help
    package, only that it is in the document root for said package.
    """
    if view.file_name() is not None:
        spp = sublime.packages_path()
        if view.file_name().startswith(spp):
            file_name = view.file_name()[len(spp)+1:]
            for pkg_info in help_index_list().values():
                if file_name.startswith(pkg_info.doc_root):
                    return pkg_info

    return None


def local_help_filename(pkg_info, help_file):
    """
    Determine what the full file name of a help file from a given package would
    be if it was stored locally.
    """
    return os.path.normpath(os.path.join(sublime.packages_path(),
                            pkg_info.doc_root, help_file))


def local_help_index(pkg_info):
    """
    Determine what the full file name of the help index file for the given
    package would be if it was stored locally.
    """
    return os.path.normpath(os.path.join(sublime.packages_path(),
                            pkg_info.index_file[len("Packages/"):]))


def format_template(template, *args):
    """
    Given incoming text, remove all common indent, then strip away the leading
    and trailing whitespace from it.

    This is a modified version of code from Default/new_templates.py from the
    core Sublime code.
    """
    return textwrap.dedent(template % args).strip()


def open_local_help(pkg_info, help_file, window=None):
    """
    Attempt to open the provided help file locally for editing.
    """
    window = window if window is not None else sublime.active_window()
    local_path = local_help_filename(pkg_info, help_file)

    if not os.path.exists(local_path):
        return log(format_template(
            """
            Specified help file does not exist; cannot open.

            Note: HyperHelpAuthor can not currently open help
            files from packed packages for editing.
            """), dialog=True)

    view = window.open_file(local_path)
    view.settings().set("_hh_auth", True)
    if not view.is_loading():
        apply_authoring_settings(view)


def open_help_index(pkg_info, window=None):
    """
    Attempt to open the provided help index file localy for editing.
    """
    window = window if window is not None else sublime.active_window()

    # The index file is stored as a resource file spec, so strip the prefix
    local_path = local_help_index(pkg_info)

    if not os.path.exists(local_path):
        return log(format_template(
            """
            Specified help index does not exist; cannot open.

            Note: HyperHelpAuthor can not currently open help
            indexes from packed packages for editing.
            """), dialog=True)

    window.open_file(local_path)


def apply_authoring_settings(view):
    """
    Given a view, apply the appropriate settings to it to ensure that it is set
    up properly for editing.
    """
    # Ensure help files with no header get the appropriate syntax set
    view.assign_syntax(hh_syntax("HyperHelp-Help.sublime-syntax"))

    author_view_settings = hha_setting("author_view_settings")
    settings = view.settings()
    for option in author_view_settings:
        settings.set(option, author_view_settings[option])


###----------------------------------------------------------------------------
