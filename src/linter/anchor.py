import sublime
import sublime_plugin

from hyperhelpcore.core import lookup_help_topic
from hyperhelpcore.core import parse_anchor_body

from ..linter_base import LinterBase


###----------------------------------------------------------------------------


class HelpAnchorLinter(LinterBase):
    """
    Lint one or more source help files trying to identify problems related to
    anchors contained in that file, such as their not being included in the
    index or being in the wrong file.
    """
    def lint(self, view, file_name):
        index_topics = {t["topic"] for t in self.pkg_info.help_topics.values()
                        if t["file"] == file_name}

        seen = {file_name}

        file_topics = {file_name}
        for pos in view.find_by_selector("meta.anchor"):
            topic, text = parse_anchor_body(view.substr(pos))
            index_info = lookup_help_topic(self.pkg_info, topic)

            sev, msg = self.validate(seen, topic, text, index_info, file_name)
            if sev is not None:
                self.add(view, sev, file_name, pos.begin(), msg)
            elif not topic.startswith("_"):
                file_topics.add(topic)

            seen.add(topic)

        for topic in index_topics - file_topics:
            self.add_index("warning",
                     "Topic '%s' appears in the index but not in '%s'",
                     topic, file_name)

    def validate(self, seen_topics, topic, text, index_info, file_name):
        if "\u00a0" in topic or "\t" in topic:
            return ("error",
                    "Topic '{}' contains nonbreaking spaces or tabs".format(
                        topic))

        if "  " in topic:
            return ("error",
                    "Topic '{}' contains consecutive whitespace characters".format(
                        topic))

        if topic.startswith("_"):
            return ((None, None) if topic in ["_none"] else
                    ("warning",
                     "The topic '{}' is reserved for internal use".format(
                         topic)))

        if index_info is None:
            return ("warning",
                    "Topic '{}' was not found in the help index".format(
                        topic))

        if index_info["file"] != file_name:
            return ("error",
                    "The topic '{}' is defined in another file ('{}')".format(
                        topic,
                        index_info["file"]))

        if topic in seen_topics:
            return ("error",
                    "The topic '{}' already appears in this file".format(
                        topic))

        return (None, None)


###----------------------------------------------------------------------------
