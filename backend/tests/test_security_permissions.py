import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from security.permissions import has_permission


class CommitteePermissionsTests(unittest.TestCase):
    def test_committee_can_list_club_members(self):
        self.assertTrue(has_permission({'committee'}, 'member.club.list'))

    def test_committee_cannot_modify_club_members(self):
        self.assertFalse(has_permission({'committee'}, 'member.club.update'))
        self.assertFalse(has_permission({'committee'}, 'member.club.create'))
        self.assertFalse(has_permission({'committee'}, 'member.club.delete'))


if __name__ == '__main__':
    unittest.main()
