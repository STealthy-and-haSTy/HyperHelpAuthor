import sublime
import sublime_plugin

from hyperhelpcore.core import help_index_list, lookup_help_topic
from hyperhelpcore.core import parse_link_body
from hyperhelpcore.core import is_topic_file_valid

from ..linter_base import LinterBase


###----------------------------------------------------------------------------


class HelpLinkLinter(LinterBase):
    """
    Lint one or more source help files trying to identify problems related to
    links contained in that file, such as determining when they are malformed
    or do not point to valid targets.
    """
    def lint(self, view, file_name):
        for pos in view.find_by_selector("meta.link"):
            link_body = view.substr(pos)
            pkg, topic, text = parse_link_body(link_body)

            sev, msg = self.validate(pkg, topic, text, file_name, link_body)
            if sev is not None:
                self.add(view, sev, file_name, pos.begin(), msg)


    def validate(self, pkg, topic, text, file_name, link_body):
        if "\u00a0" in topic or "\t" in topic:
            return ("error",
                    "Link '{}' contains nonbreaking spaces or tabs".format(
                        topic))

        if topic is None:
            return ("error",
                    "Malformed link; not enough ':' characters ('{}')".format(
                        link_body))

        link_pkg = self.pkg_info if pkg is None else help_index_list().get(pkg)

        if link_pkg is None:
            return ("error",
                    "Link references a topic in a non-existant package ('{}')".format(
                        pkg))

        index_info = lookup_help_topic(link_pkg, topic)
        if index_info is None:
            return ("warning",
                    "Link references unknown topic '{}'".format(topic))

        if is_topic_file_valid(link_pkg, index_info) is False:
            return ("warning",
                    "Link references a non-existant package file ('{}')".format(
                        index_info["file"]))

        return (None, None)


###----------------------------------------------------------------------------
