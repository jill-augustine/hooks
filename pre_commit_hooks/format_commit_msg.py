import argparse
import re
from typing import Sequence, Union, Tuple

import git

class Commit:
    COMMIT_TYPES = ["fix", "feat", "build", "chore", "ci", "docs", "style", "refactor", "perf", "test"]
    SKIP_PREFIXES = ["skip", "no-verify", "s"]

    def __init__(self, message_fp: Union[str, "pathlib.Path"]):

        self.message_fp = message_fp
        self.default_commit_type: str = None
        self.issue_no: str = None
        self.commit_message = None
        self.commit_type = None

        # Update commit_type and issue_no if possible
        self._set_branch_info()

    def format_message(self):
        print('Formatting message')
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
        repo = git.Repo()
        branch_name = repo.active_branch.name
        branch_name_parts = branch_name.split("/")

        if branch_name_parts[0].lower() not in self.COMMIT_TYPES:
            print(
            "Commit type and issue_no could not be determined from branch name "
            f"'{branch_name}'."
            )
            return

        default_commit_type = branch_name_parts[0].lower()
        # Check for a match e.g. "PROJ-123"
        match = re.search(r"^[A-Za-z]+-[0-9]+$", branch_name_parts[1])
        if not match:
            raise ValueError("Branch name contains a type but no jira issue no.")

        self.default_commit_type = default_commit_type
        self.issue_no = match[0]
        return

    def _read_commit_message(self):
        with open(self.message_fp, "r", encoding="utf-8") as f:
            self.commit_message = f.read()

    def _write_commit_message(self):
        with open(self.message_fp, "w", encoding="utf-8") as f:
            f.write(self.commit_message)

    def _extract_type_from_commit_message(self):
        """Extract the commit type from the commit message. Remove the commit 
        type from the commit message.
        """

        match = re.search(r"^[A-Za-z]+(?=: )", self.commit_message)
        
        if match is None:
            if self.default_commit_type is None:
                err = (
                        "Commit type could not be determined from the branch "
                        "name or the commit message"
                    )
                raise ValueError(err)
            self.commit_type = self.default_commit_type
            # Leave commit message unchanged
            return
        
        if match[0].lower() in self.SKIP_PREFIXES + self.COMMIT_TYPES:
            self.commit_type = match[0]
            # +2 for the ": "
            self.commit_message = self.commit_message[len(self.commit_type)+2:]
            return

        err = (
            f"commit type '{match[0].lower()}' is not allowed according to "
            "conventional commit")
        raise ValueError(err)

    def _format_commit_message(self):
        if self.commit_type in self.SKIP_PREFIXES:
            # No further changes. (The skip prefix was already extracted)
            return
        self.commit_message = (
            f"{self.issue_no.upper()}({self.commit_type.lower()}): {self.commit_message}"
            )


def main(input_args: Sequence[str] | None = None) -> int:
    """Entry point to the hook."""
    parser = argparse.ArgumentParser()
    parser.add_argument("args", nargs="*")
    parsed_args = parser.parse_args(input_args).args

    try:
        Commit(message_fp=parsed_args[0]).format_message()
        return 0
    except ValueError:
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
