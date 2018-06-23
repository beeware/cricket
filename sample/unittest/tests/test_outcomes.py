from unittest import TestCase, skip, expectedFailure


class GoodTests(TestCase):
    def test_passing_item(self):
        pass

    @skip('tra-la-la')
    def test_skipped_item(self):
        pass


class BadTests(TestCase):
    def test_failing_item(self):
        self.fail('Failed!')

    def test_assertion_item(self):
        self.assertEqual(1, 2, 'Who are you kidding?')

    def test_error_item(self):
        raise Exception("this is really bad")

    @expectedFailure
    def test_xfailing_item(self):
        self.fail('This is a known bad')

    @expectedFailure
    def test_upassed_item(self):
        pass

    def test_subtests(self):
        for i in range(0, 6):
            with self.subTest(i=i):
                self.assertEqual(i % 2, 0)
