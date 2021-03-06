import unittest
import panglery.pangler

class TestPangler(unittest.TestCase):
    def test_basic_event(self):
        p = panglery.Pangler()
        self.fired = False

        @p.subscribe(event='test')
        def test_hook(p):
            self.fired = True

        p.trigger(event='test')
        self.assert_(self.fired)

    def test_basic_event_without_decorator(self):
        p = panglery.Pangler()
        self.fired = False

        def test_hook(p):
            self.fired = True
        p.subscribe(test_hook, event='test')

        p.trigger(event='test')
        self.assert_(self.fired)

    def test_hooking_nothing(self):
        p = panglery.Pangler()
        self.assertRaises(ValueError, p.subscribe, lambda: None)

    def test_triggering_nothing(self):
        p = panglery.Pangler()
        self.assertRaises(ValueError, p.trigger)

    def test_receiving_parameters(self):
        p = panglery.Pangler()
        self.fired = False

        @p.subscribe(needs=['test'])
        def test_hook(p, test):
            self.assertEqual(test, 'testval')
            self.fired = True

        p.trigger(test='testval')
        self.assert_(self.fired)

    def test_modifying_parameters(self):
        p = panglery.Pangler()
        self.fired = False

        @p.subscribe(modifies=['foo'])
        def foo_hook(p, foo):
            return {'foo': foo * 2}

        @p.subscribe(needs=['foo'])
        def foo_hook2(p, foo):
            self.assertEqual(foo, 6)
            self.fired = True

        p.trigger(foo=3)
        self.assert_(self.fired)

    def test_unsubscribe(self):
        p = panglery.Pangler()
        self.fired = False

        @p.subscribe(event='test')
        def test_hook(p):
            self.fired = True

        p.unsubscribe(test_hook, event='test')
        p.trigger(event='test')
        self.assertFalse(self.fired)

    def test_unsubscribe_no_such_subscriber(self):
        p = panglery.Pangler()
        self.assertRaises(
            panglery.pangler.NoSuchHook, p.unsubscribe, lambda : None)

    def test_binding(self):
        self.fired = False
        class TestClass(object):
            p = panglery.Pangler()
            datum = 'foo'

            @p.subscribe(event='test')
            def test_hook(self2, p):
                self.assertEqual(self2.datum, 'foo')
                self.fired = True

        inst = TestClass()
        inst.p.trigger(event='test')
        self.assert_(self.fired)

    def test_descriptor_binding_store(self):
        class TestClass(object):
            p = panglery.Pangler()

        inst = TestClass()
        self.assert_(inst.p is inst.p)

    def test_from_store(self):
        class TestClass(object):
            p = panglery.Pangler()
            p2 = panglery.Pangler('p2')

        inst = TestClass()
        self.assertRaises(KeyError, panglery.Pangler.from_store, inst)
        self.assertRaises(KeyError, panglery.Pangler.from_store, inst, 'p2')
        p = inst.p
        self.assert_(panglery.Pangler.from_store(inst) is p)
        p2 = inst.p2
        self.assert_(panglery.Pangler.from_store(inst, 'p2') is p2)

    def test_binding_with_ids(self):
        class TestClass(object):
            p1 = panglery.Pangler('p1')
            p2 = panglery.Pangler('p2')

        inst = TestClass()
        self.assert_(inst.p1 is inst.p1)
        self.assert_(inst.p2 is inst.p2)
        self.assert_(inst.p1 is not inst.p2)

    def test_disabling_persisting(self):
        class TestClass(object):
            p = panglery.Pangler(None)

        inst = TestClass()
        self.assert_(inst.p is not inst.p)

    def test_binding_methods(self):
        class TestClass(object):
            pass

        p = panglery.Pangler()
        inst = TestClass()
        self.assert_(p.bind(inst) is not p.bind(inst))
        self.assert_(p.stored_bind(inst) is p.stored_bind(inst))

    def test_binding_uses_weakrefs(self):
        class TestClass(object):
            p = panglery.Pangler()
            @p.subscribe(event='spam')
            def spam_event(self2, p):
                self.assert_(False, 'this should never be called')

        inst = TestClass()
        p = inst.p
        del inst
        self.assertRaises(panglery.pangler.InstanceDead,
            p.trigger, event='spam')

    def test_clone(self):
        p = panglery.Pangler()
        self.fired = False

        @p.subscribe(event='test')
        def test_hook(p):
            self.fired = True

        p2 = p.clone()
        p2.trigger(event='test')
        self.assert_(self.fired)

    def test_clone_subclassing(self):
        class TestPangler(panglery.Pangler):
            pass

        p = TestPangler()
        p2 = p.clone()
        self.assert_(isinstance(p2, TestPangler))

    def test_unrelated_events(self):
        p = panglery.Pangler()
        self.fired = 0

        @p.subscribe(event='test1')
        def test1_hook(p):
            self.fired |= 1

        @p.subscribe(event='test2')
        def test2_hook(p):
            self.fired |= 2

        @p.subscribe(needs=['foo'])
        def foo_hook(p, foo):
            self.fired |= 4

        p.trigger(event='test1')
        self.assertEqual(self.fired, 1)

        self.fired = 0
        p.trigger(event='test2')
        self.assertEqual(self.fired, 2)

        self.fired = 0
        p.trigger(event='test3', foo='bar')
        self.assertEqual(self.fired, 4)

    def test_combining(self):
        self.fired = 0

        p = panglery.Pangler()
        @p.subscribe(event='test')
        def test_hook(p):
            self.fired |= 1

        p2 = panglery.Pangler()
        @p2.subscribe(event='test')
        def test_hook2(p):
            self.fired |= 2

        p3 = p.combine(p2)
        p3.trigger(event='test')
        self.assertEqual(self.fired, 3)

    def test_pretriggers(self):
        self.triggered = []
        self.fired = 0

        def pretrigger1(event):
            self.triggered.append(event)

        def pretrigger2(event):
            self.fired += 1

        p = panglery.Pangler()
        p.pretriggers.append(pretrigger1)
        p.pretriggers.append(pretrigger2)

        p.trigger(event='test1')
        p.trigger(event='test2', foo='bar')

        self.assertEqual(self.triggered, [{'event' : 'test1'},
                                          {'event' : 'test2', 'foo' : 'bar'}])
        self.assertEqual(self.fired, 2)

    def test_combining_pretriggers(self):
        self.fired = 0

        p = panglery.Pangler()
        def pretrigger1(event):
            self.fired |= 1

        p.pretriggers.append(pretrigger1)

        p2 = panglery.Pangler()
        def pretrigger2(event):
            self.fired |= 2

        p2.pretriggers.append(pretrigger2)

        p3 = p.combine(p2)
        p3.trigger(event='test')
        self.assertEqual(self.fired, 3)

class TestPanglerAggregate(unittest.TestCase):
    def test_subclass_binding(self):
        self.fired = 0

        class TestClassA(object):
            hooks = panglery.Pangler()
            p = panglery.PanglerAggregate('hooks')

            @hooks.subscribe(event='test')
            def test_hookA(_, p):
                self.fired |= 1

        class TestClassB(TestClassA):
            hooks = panglery.Pangler()

            @hooks.subscribe(event='test')
            def test_hookB(_, p):
                self.fired |= 2

        class TestClassC(TestClassA):
            hooks = panglery.Pangler()

            @hooks.subscribe(event='test')
            def test_hookC(_, p):
                self.fired |= 4

        class TestClassD(TestClassB, TestClassC):
            hooks = panglery.Pangler()

            @hooks.subscribe(event='test')
            def test_hookD(_, p):
                self.fired |= 8

        inst = TestClassD()
        inst.p().trigger(event='test')
        self.assertEqual(self.fired, 15)

        self.fired = 0
        inst = TestClassB()
        inst.p().trigger(event='test')
        self.assertEqual(self.fired, 3)

    def test_unbound_aggregate(self):
        agg = panglery.PanglerAggregate()
        class TestClass(object):
            p = agg
        self.assertEqual(TestClass.p, agg)
        self.assertEqual(TestClass().p, agg)

    def test_aggregate_binding_store(self):
        class TestClass(object):
            p = panglery.PanglerAggregate('hooks')

        inst = TestClass()
        self.assert_(inst.p() is inst.p())

    def test_disabling_aggregate_binding_store(self):
        class TestClass(object):
            p = panglery.PanglerAggregate('hooks', None)

        inst = TestClass()
        self.assert_(inst.p() is not inst.p())

    def test_aggregate_id(self):
        class TestClass(object):
            hooks = panglery.Pangler()
            p = panglery.PanglerAggregate('hooks')

        inst = TestClass()
        self.assert_(inst.p() is not inst.hooks)

class DeprecatedAPITest(unittest.TestCase):
    """
    Tests if the deprecated API works.
    """
    def _test_add_hook(self, attach_hook):
        p = panglery.Pangler()
        self.fired = False

        attach_hook(p)
        p.trigger(event='test')

        self.assertTrue(self.fired)

    def test_add_hook_decorator(self):
        def attach_hook(p):
            @p.add_hook(event='test')
            def hook(p):
                self.fired = True

        self._test_add_hook(attach_hook)

    def test_add_hook_direct(self):
        def attach_hook(p):
            def hook(p):
                self.fired = True
            p.add_hook(hook, event='test')

        self._test_add_hook(attach_hook)
