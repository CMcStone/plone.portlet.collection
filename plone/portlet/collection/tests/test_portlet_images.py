from zope.component import getUtility, getMultiAdapter

from plone.portlets.interfaces import IPortletType
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignment
from plone.portlets.interfaces import IPortletDataProvider
from plone.portlets.interfaces import IPortletRenderer

from plone.app.portlets.storage import PortletAssignmentMapping

from plone.portlet.collection import images

from plone.portlet.collection.tests.base import TestCase


from Products.CMFCore.utils import getToolByName


class TestPortlet(TestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))

    def testPortletTypeRegistered(self):
        portlet = getUtility(IPortletType,
            name='plone.portlet.collection.Images')
        self.assertEquals(portlet.addview, 'plone.portlet.collection.Images')

    def testInterfaces(self):
        portlet = images.Assignment(header=u"title")
        self.failUnless(IPortletAssignment.providedBy(portlet))
        self.failUnless(IPortletDataProvider.providedBy(portlet.data))

    def testInvokeAddview(self):
        portlet = getUtility(IPortletType,
            name='plone.portlet.collection.Images')
        mapping = self.portal.restrictedTraverse(
            '++contextportlets++plone.leftcolumn')
        for m in mapping.keys():
            del mapping[m]
        addview = mapping.restrictedTraverse('+/' + portlet.addview)

        addview.createAndAdd(data={'header': u"test title"})

        self.assertEquals(len(mapping), 1)
        self.failUnless(isinstance(mapping.values()[0], images.Assignment))

    def testInvokeEditView(self):
        mapping = PortletAssignmentMapping()
        request = self.folder.REQUEST

        mapping['foo'] = images.Assignment(header=u"title")
        editview = getMultiAdapter((mapping['foo'], request), name='edit')
        self.failUnless(isinstance(editview, images.EditForm))

    def testRenderer(self):
        context = self.folder
        request = self.folder.REQUEST
        view = self.folder.restrictedTraverse('@@plone')
        manager = getUtility(IPortletManager, name='plone.rightcolumn',
            context=self.portal)
        assignment = images.Assignment(header=u"title")

        renderer = getMultiAdapter(
            (context, request, view, manager, assignment), IPortletRenderer)
        self.failUnless(isinstance(renderer, images.Renderer))


class TestRenderer(TestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))

    def renderer(self, context=None, request=None, view=None, manager=None,
        assignment=None):
        context = context or self.folder
        request = request or self.folder.REQUEST
        view = view or self.folder.restrictedTraverse('@@plone')
        manager = manager or getUtility(IPortletManager,
            name='plone.rightcolumn', context=self.portal)
        assignment = assignment or images.Assignment(header=u"title")

        return getMultiAdapter((context, request, view, manager, assignment),
            IPortletRenderer)

    def test_render(self):
        r = self.renderer(context=self.portal,
            assignment=images.Assignment(header=u"title"))
        r = r.__of__(self.folder)
        r.update()
        output = r.render()

        # this test failed due to changed behavior. We'll not output anything
        # if the portlet does not point to a collection

        #self.failUnless('title' in output)
        #self.failUnless('<b>text</b>' in output)


class TestImagesQuery(TestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))
        #make a collection
        self.collection = self._createType(self.folder, 'Topic', 'collection')

    def _createType(self, context, portal_type, id, **kwargs):
        """Helper method to create a new type
        """
        ttool = getToolByName(context, 'portal_types')
        cat = self.portal.portal_catalog

        fti = ttool.getTypeInfo(portal_type)
        fti.constructInstance(context, id, **kwargs)
        obj = getattr(context.aq_inner.aq_explicit, id)
        cat.indexObject(obj)
        return obj

    def renderer(self, context=None, request=None, view=None, manager=None,
        assignment=None):
        context = context or self.folder
        request = request or self.folder.REQUEST
        view = view or self.folder.restrictedTraverse('@@plone')
        manager = manager or getUtility(IPortletManager,
            name='plone.leftcolumn', context=self.portal)
        assignment = assignment
        return getMultiAdapter((context, request, view, manager, assignment),
            IPortletRenderer)

    def testSimpleQuery(self):
        # set up our collection to search for Folders
        crit = self.folder.collection.addCriterion('portal_type',
            'ATSimpleStringCriterion')
        crit.setValue('Folder')

        # add a few folders
        for i in range(6):
            self.folder.invokeFactory('Folder', 'folder_%s'%i)
            getattr(self.folder, 'folder_%s'%i).reindexObject()

        # the folders are returned by the topic
        collection_num_items = len(self.folder.collection.queryCatalog())
        # We better have some folders
        self.failUnless(collection_num_items >= 6)

        mapping = PortletAssignmentMapping()
        request = self.folder.REQUEST
        mapping['foo'] = images.Assignment(header=u"title",
            target_collection='/Members/test_user_1_/collection')
        collectionrenderer = self.renderer(context=None, request=None,
            view=None, manager=None, assignment=mapping['foo'])

        # we want the portlet to return us the same results as the collection
        self.assertEquals(collection_num_items,
            len(collectionrenderer.results()))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPortlet))
    suite.addTest(makeSuite(TestRenderer))
    suite.addTest(makeSuite(TestImagesQuery))
    return suite