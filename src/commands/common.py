import sublime
import sublime_plugin

import codecs
import re

from hyperhelpcore.common import log
from ..common import format_template


###----------------------------------------------------------------------------


# TODO: The code in help_index.py uses posixpath as the path module instead of
# os.path because in packages all files are posix. There is probably going to
# be interplay with that in this code in an unfortunate way since it needs to
# work with local files and match them to resources.


# Match a help header line focusing on the date field.
header_date_re = re.compile(r'^(%hyperhelp.*\bdate=")(\d{4}-\d{2}-\d{2})(".*)')


###----------------------------------------------------------------------------


def error_dialog(message, *args):
    """
    Simple local helper for displaying an error dialog using the log function.
    """
    log(format_template(message, *args), dialog=True)


def global_package_list(filter_with_help=True):
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
def make_help_index(package, doc_root, index_path):
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
def make_root_help(package, help_path):
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
