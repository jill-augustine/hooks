import os
from contextlib import nullcontext
from tempfile import NamedTemporaryFile

import pytest

from hooks.format_commit_msg import Commit

param_options = (
    (
        "branch_name,commit_msg,exp_commit_msg,exp_default_commit_type,"
        "exp_commit_type,exp_issue_no"
    ),
    [
        (
            "feat/ABC-123/my_feat",
            "my message here",
            nullcontext("ABC-123(feat): my message here"),
            "feat",
            "feat",
            "ABC-123",
        ),
        (
            "feat/ABC-456/my_feat",
            "fix: my message here",
            nullcontext("ABC-456(fix): my message here"),
            "feat",
            "fix",
            "ABC-456",
        ),
        (
            "fix/ABC-789/my_fix",
            "feat: my message here",
            nullcontext("ABC-789(feat): my message here"),
            "fix",
            "feat",
            "ABC-789",
        ),
        # Empty string because None is a valid value
        (
            "fix/my_fix",
            "chore: my message here",
            pytest.raises(ValueError, match="no jira issue"),
            "",
            "",
            "",
        ),  # branch contains commit type but not issue no
        (
            "develop",
            "my message",
            pytest.raises(ValueError, match="type could not be determined"),
            "",
            "",
            "",
        ),  # commit type not in branch or message
        (
            "develop",
            "feat: my message",
            pytest.raises(ValueError, match="issue_no could not be determined"),
            "",
            "",
            "",
        ),  # issue number not in branch name
        (
            "develop",
            "invalidtype: my message",
            pytest.raises(ValueError, match="not allowed"),
            "",
            "",
            "",
        ),  # neither commit type nor issue number in branch name
        ("develop", "skip: my message", nullcontext("my message"), None, None, None),
    ],
)


@pytest.mark.parametrize(*param_options)
def test_one(
    branch_name,
    commit_msg,
    exp_commit_msg,
    exp_default_commit_type,
    exp_commit_type,
    exp_issue_no,
):
    tmp_file = NamedTemporaryFile(delete=False)

    with open(tmp_file.name, mode="w", encoding="utf-8") as f:
        f.write(commit_msg)

    try:
        with exp_commit_msg as exp:  # exp = the value of `nullcontext(value)`
            commit = Commit(message_fp=tmp_file.name, branch_name=branch_name)
            commit.format_message()
            with open(tmp_file.name, mode="r", encoding="utf-8") as f:
                # This value is the same as commit.commit_message
                updated_msg = f.read()
            assert updated_msg == exp
            assert commit.default_commit_type == exp_default_commit_type
            assert commit.issue_no == exp_issue_no
    finally:
        os.remove(tmp_file.name)
