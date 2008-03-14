from interfaces import ISubscribeHelper
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import re
from zope import schema
import AccessControl
from slc.alertservice import AlertMessageFactory as _
from AccessControl import safe_builtins
from zope.component import getUtility
from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.utils import DisplayList
from slc.alertservice.interfaces import ITypesGetter

class SubscribeHelper(BrowserView):
    implements(ISubscribeHelper)

    security = AccessControl.ClassSecurityInfo()

    security.declarePublic('contentSubjectsDL')
    def contentSubjectsDL(self):
        """ see interface"""
        pvt = getToolByName(self, 'portal_vocabularies', '')
        VOCAB = getattr(pvt, 'Subcategory', '')
        vd = VOCAB.getVocabularyDict(self)
        toplevel = [(k, vd[k][0]) for k in vd.keys()]
        DL = DisplayList(toplevel)
        return DL

    security.declarePublic('contentTypesDL')
    def contentTypesDL(self):
        """ return valid types to select """
        util = getUtility(ITypesGetter, name="alertservice.typesgetter")
        return util(self)