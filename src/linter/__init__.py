from __future__ import annotations

from typing import List

from ...authoring import reload

reload("src.linter", ["common", "base", "anchor", "link",
       "mismatching_title", "missing_help_source"])

from .anchor import HelpAnchorLinter
from .link import HelpLinkLinter
from .mismatching_title import MismatchingTitleLinter
from .missing_help_source import MissingHelpSourceLinter
from .missing_in_toc import MissingInTOCLinter
from .unlinked_files import UnlinkedHelpFilesLinter

__all__: List[str] = [
    # Linters
    "HelpAnchorLinter",
    "HelpLinkLinter",
    "MissingHelpSourceLinter",
    "MismatchingTitleLinter",
    "MissingInTOCLinter",
    "UnlinkedHelpFilesLinter"
]
