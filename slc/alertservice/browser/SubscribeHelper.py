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
from slc.alertservice.interfaces import ISubjectGetter
from slc.alertservice.interfaces import ITypesGetter

from ZTUtils import b2a, a2b

class SubscribeHelper(BrowserView):
    implements(ISubscribeHelper)

    security = AccessControl.ClassSecurityInfo()

    security.declarePublic('contentSubjectsDL')
    def contentSubjectsDL(self):
        """ return subjects for selection """
        util = getUtility(ISubjectGetter, name="alertservice.subjectgetter")
        return util(self)
#        pvt = getToolByName(self, 'portal_vocabularies', '')
#        VOCAB = getattr(pvt, 'Subcategory', '')
#        vd = VOCAB.getVocabularyDict(self)
#        toplevel = [(k, vd[k][0]) for k in vd.keys()]
#        DL = DisplayList(toplevel)
#        return DL

    security.declarePublic('contentTypesDL')
    def contentTypesDL(self):
        """ return valid types to select """
        util = getUtility(ITypesGetter, name="alertservice.typesgetter")
        return util(self)


    def getPersonalAlertId(self):
        """ returns id under which the notification alert gets saved """
        # simple hardcoded string
        return "personalization_alert"

    def getUserResults(self):
        """ returns the user's profile based on parameters passed in the REQUEST """
        alert_tool = getToolByName(self.context, 'portal_alertservice')
        profile = alert_tool.getUserProfile()
        if profile:
            return alert_tool.showAllResultsForProfile(self.context.REQUEST.get('s', ''))
        return []


    def getUserSettings(self):
        """ returns exisitng settings for a given user """
        alert_tool = getToolByName(self.context, 'portal_alertservice')
        profile = alert_tool.getUserProfile()
        settings = profile.get(self.getPersonalAlertId(), {}).get('settings', {})
        return settings