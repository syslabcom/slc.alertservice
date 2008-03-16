from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from plone.app.controlpanel.search import ISearchSchema
from Products.Archetypes.utils import DisplayList

from slc.alertservice import AlertMessageFactory as _

from slc.alertservice.interfaces import ISubjectGetter
from slc.alertservice.interfaces import ITypesGetter



class SubjectGetter(object):
    implements(ISubjectGetter)

    def __call__(self, context):
        pc = getToolByName(context, 'portal_catalog')
        subjects = pc.uniqueValuesFor('Subject')
        DL = DisplayList()
        for subj in subjects:
            DL.add(subj, subj)

        return DL


class TypesGetter(object):

    def __call__(self, context):
        urltool = getToolByName(context, 'portal_url')
        siteroot = urltool.getPortalObject()
        seach_types = ISearchSchema(siteroot).get_types_not_searched()
        DL = DisplayList()
        for st in seach_types:
            DL.add(st, st)

        return DL