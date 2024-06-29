"""Format commit message according to branch name."""

import argparse
import re
from typing import Sequence, Union

import git

DEFAULT_COMMIT_TYPES = [
    "fix",
    "feat",
    "build",
    "chore",
    "ci",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
]
DEFAULT_SKIP_PREFIXES = ["skip", "no-verify", "s"]
# DEFAULT_BRANCH_FORMAT = "{commit_type}/{issue_no}/*"
# DEFAULT_COMMIT_FORMAT = ""


class Commit:

    def __init__(self, message_fp: Union[str], branch_name: str = None):

        self.message_fp = message_fp
        self.default_commit_type: str = None
        self.issue_no: str = None
        self.commit_message = None
        self.commit_type = None
        self.updated_commit_message = None
        self._commit_types = DEFAULT_COMMIT_TYPES
        self._skip_prefixes = DEFAULT_SKIP_PREFIXES
        self.branch_name = branch_name
        self.skipped = False

        # Update branch_name, and commit_type and issue_no if possible
        self._set_branch_info()

    def format_message(self):
        """Format the commit message where applicable."""
        self._read_commit_message()
        self._extract_type_from_commit_message()
        self._format_commit_message()
        self._write_commit_message()

    def _set_branch_info(self):
        """Set the default commit type and issue number (if any) described by
        the branch.


        Raises
        ------
        ValueError
            If default commit type is found but Jira issue no is not found.
        """
        if not self.branch_name:
            repo = git.Repo()
            self.branch_name = repo.active_branch.name
        branch_name_parts = self.branch_name.split("/")

        if branch_name_parts[0].lower() not in self._commit_types:
            return

        default_commit_type = branch_name_parts[0].lower()
        # Check for a match e.g. "PROJ-123"
        match = re.search(r"^[A-Za-z]+-[0-9]+$", branch_name_parts[1])
        if not match:
            err = "Branch name contains a type but no jira issue no."
            raise ValueError(err)

        self.default_commit_type = default_commit_type
        self.issue_no = match[0]
        return

    def _read_commit_message(self):
        with open(self.message_fp, "r", encoding="utf-8") as f:
            self.commit_message = f.read()

    def _write_commit_message(self):
        with open(self.message_fp, "w", encoding="utf-8") as f:
            f.write(self.updated_commit_message)

    def _extract_type_from_commit_message(self):
        """Extract the commit type from the commit message. Remove the commit
        type from the commit message.
        """

        match = re.search(r"^[A-Za-z]+(?=:)", self.commit_message)

        if match is None:
            if self.default_commit_type is None:
                err = (
                    "Commit type could not be determined from the branch "
                    f"name '{self.branch_name}' or the commit message "
                    f"'{self.commit_message.strip()}'. Start the commit "
                    "message with one of "
                    f"{ {s+':' for s in self._skip_prefixes} } to skip this "
                    "check."
                )
                raise ValueError(err)
            self.commit_type = self.default_commit_type
            # Leave commit message unchanged
            return

        if match[0].lower() in self._skip_prefixes + self._commit_types:
            self.commit_type = match[0]
            # +1 for the ":"
            self.commit_message = self.commit_message[
                len(self.commit_type) + 1 :
            ].strip()
            return

        err = (
            f"Commit type '{match[0].lower()}' is not allowed according to "
            "conventional commit."
        )
        raise ValueError(err)

    def _format_commit_message(self):
        if self.commit_type in self._skip_prefixes:
            # No further changes. (The skip prefix was already extracted)
            self.updated_commit_message = self.commit_message
            return

        if (self.commit_type is None) or (self.issue_no is None):
            raise ValueError("Either commit_type of issue_no could not be determined.")
        print(
            f"Extracted commit_type: '{self.commit_type}' and "
            f"issue_no: '{self.issue_no}'."
        )
        self.updated_commit_message = (
            f"{self.issue_no.upper()}"
            f"({self.commit_type.lower()}): "
            f"{self.commit_message}"
        )


def main(input_args: Sequence[str] | None = None) -> int:
    """Entry point to the hook."""
    parser = argparse.ArgumentParser()
    parser.add_argument("args", nargs="*")
    namespace = parser.parse_args(input_args)
    parsed_args = namespace.args
    try:
        Commit(message_fp=parsed_args[0]).format_message()
        return 0
    except ValueError as e:
        print(e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
