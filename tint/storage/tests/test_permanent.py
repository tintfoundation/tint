from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks

from tint.storage.permanent import ObservableStorage


class ObservableStorageTest(unittest.TestCase):
    def setUp(self):
        self.storage = ObservableStorage()


    @inlineCallbacks
    def test_subscribeValue(self):
        results = []

        def func(key, value):
            results.append((key, value))
        key = "/a/key"
        self.storage.subscribe(key, "value", func)
        value = yield self.storage.publishChange(key + "/", 1, True)
        self.assertEqual(value, 1)

        value = yield self.storage.publishChange(key, 2, False)
        self.assertEqual(value, 2)

        value = yield self.storage.publishChange(key + "/another", 3, False)
        self.assertEqual(value, 3)

        self.assertEqual(results, [(key, 1), (key, 2)])


    @inlineCallbacks
    def test_subscribeChildAdd(self):
        results = []

        def func(key, value):
            results.append((key, value))
        key = "/a/key"
        self.storage.subscribe(key, "child_added", func)
        value = yield self.storage.publishChange(key + "/child", 1, False)
        self.assertEqual(value, 1)
        self.assertEqual(results, [(key + "/child", 1)])

        # not a new child
        value = yield self.storage.publishChange(key + "/child", 2, True)
        self.assertEqual(value, 2)
        self.assertEqual(results, [(key + "/child", 1)])

        # a grandchild
        value = yield self.storage.publishChange(key + "/child/grand", 2, False)
        self.assertEqual(value, 2)
        self.assertEqual(results, [(key + "/child", 1), (key + "/child/grand", 2)])


    @inlineCallbacks
    def test_subscribeChildModify(self):
        results = []

        def func(key, value):
            results.append((key, value))
        key = "/a/key"
        self.storage.subscribe(key, "child_changed", func)
        value = yield self.storage.publishChange(key + "/child", 1, True)
        self.assertEqual(value, 1)
        self.assertEqual(results, [(key + "/child", 1)])

        # not a new child
        value = yield self.storage.publishChange(key + "/child", 2, False)
        self.assertEqual(value, 2)
        self.assertEqual(results, [(key + "/child", 1)])

        # a grandchild
        value = yield self.storage.publishChange(key + "/child/grand", 2, True)
        self.assertEqual(value, 2)
        self.assertEqual(results, [(key + "/child", 1), (key + "/child/grand", 2)])
