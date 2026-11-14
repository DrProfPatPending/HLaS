import unittest

from core.content_scopes import normalize_content_scope


class ContentScopeNormalizationTests(unittest.TestCase):
    def test_defaults_missing_and_unknown_values_to_home(self):
        for value in (None, '', 'unknown'):
            with self.subTest(value=value):
                self.assertEqual(normalize_content_scope(value), 'home')

    def test_normalizes_health_and_safety_aliases(self):
        for value in ('health-safety', 'health_safety', 'Health-Safety', 'healthandsafety', 'hs'):
            with self.subTest(value=value):
                self.assertEqual(normalize_content_scope(value), 'health-safety')

    def test_all_is_only_available_for_collection_queries(self):
        self.assertEqual(normalize_content_scope('all'), 'home')
        self.assertEqual(normalize_content_scope('all', allow_all=True), 'all')


if __name__ == '__main__':
    unittest.main()