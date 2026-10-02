import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import updater
from updater import archive_url, extracted_dir_name

FORK_URL = "https://github.com/rezenderaul/OpCore-Simplify/archive/refs/heads/usable-windows.zip"
UPSTREAM_URL = "https://github.com/lzhoang2801/OpCore-Simplify/archive/refs/heads/main.zip"


def fresh_updater(testcase, **kwargs):
    tmp = tempfile.mkdtemp()
    testcase.addCleanup(shutil.rmtree, tmp, True)
    up = updater.Updater(**kwargs)
    up.temporary_dir = tmp
    return up


class ForkSourceTest(unittest.TestCase):
    def test_download_url_tracks_fork(self):
        self.assertTrue(fresh_updater(self).download_repo_url.startswith(FORK_URL))

    def test_no_upstream_url_anywhere_in_flow(self):
        up = fresh_updater(self)
        self.assertNotIn("lzhoang2801", up.download_repo_url)

    def test_unconfigured_helpers_keep_upstream_values(self):
        self.assertEqual(archive_url(), UPSTREAM_URL)
        self.assertEqual(extracted_dir_name(), "OpCore-Simplify-main")

    def test_explicit_upstream_args_behave_as_before(self):
        up = fresh_updater(self)
        up.github.get_commits = Mock(return_value={
            "commitGroups": [{"commits": [{"oid": "abc123"}]}]
        })
        self.assertEqual(up.get_latest_sha_version(), "abc123")
        up.github.get_commits.assert_called_once_with(
            "lzhoang2801", "OpCore-Simplify", "main"
        )


class TargetDirTest(unittest.TestCase):
    def test_fork_layout_resolves(self):
        up = fresh_updater(self)
        with tempfile.TemporaryDirectory() as tmp:
            up.temporary_dir = tmp
            want = os.path.join(tmp, "OpCore-Simplify-usable-windows")
            os.makedirs(want)
            self.assertEqual(up._find_target_dir(), want)

    def test_legacy_layout_still_resolves(self):
        up = fresh_updater(self)
        with tempfile.TemporaryDirectory() as tmp:
            up.temporary_dir = tmp
            want = os.path.join(tmp, "OpCore-Simplify-main")
            os.makedirs(want)
            self.assertEqual(up._find_target_dir(), want)

    def test_missing_layout_returns_none(self):
        up = fresh_updater(self)
        with tempfile.TemporaryDirectory() as tmp:
            up.temporary_dir = tmp
            self.assertIsNone(up._find_target_dir())


class SkipOnFailureTest(unittest.TestCase):
    def test_failed_lookup_returns_none_and_touches_nothing(self):
        up = fresh_updater(self)
        before = set(os.listdir(up.temporary_dir))
        up.github.get_commits = Mock(side_effect=ValueError("boom"))
        with patch("builtins.print"):
            self.assertIsNone(
                up.get_latest_sha_version(
                    up.update_owner, up.update_repo, up.update_branch
                )
            )
        self.assertEqual(set(os.listdir(up.temporary_dir)), before)


if __name__ == "__main__":
    unittest.main()
