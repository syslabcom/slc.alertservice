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

from ZTUtils import b2a, a2b

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



    def encodeEmail(self, email):
        if email is None:
            return None
        email = email.strip()
        code = b2a(email)
        while (code[0]=='_' or code[-1]=='_'):
            email = email+" "
            code = b2a(email)
        return code
    
    def decodeEmail(self, code):
        if code is None:
            return None
        email = a2b(code)
        email = email.strip()
        return email