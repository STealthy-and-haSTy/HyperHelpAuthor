import sublime
import sublime_plugin

import os

from hyperhelpcore.common import log

from ..linter_support import can_lint_view, find_lint_target, get_linters
from ..linter_support import get_lint_file, format_lint


###----------------------------------------------------------------------------


class HyperhelpAuthorLintCommand(sublime_plugin.WindowCommand):
    def run(self):
        # The command can trigger from a build system, so don't execute if the
        # build is triggered from the help view; is_enabled() is not invoked
        # for build targets.
        target = find_lint_target(self.window.active_view())
        if target is None:
            return

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

        format_lint(target, issues, self.window)

    def is_enabled(self):
        return can_lint_view(self.window.active_view())


###----------------------------------------------------------------------------
