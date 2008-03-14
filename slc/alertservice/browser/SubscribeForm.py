from interfaces import ISubscribeForm
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from zope.component import getUtility
from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.utils import DisplayList
from slc.alertservice.interfaces import ITypesGetter

class SubscribeForm(BrowserView):
    implements(ISubscribeForm)
    
    template = ViewPageTemplateFile('subscribe_form.pt')
    
    def __call__(self):
        """ do the subscription """
        import pdb; pdb.set_trace()
        print "someone called?"
        
        self.request.set('disable_border', True)
        
        return self.template()
    
    def contentSubjectsDL(self):
        """ see interface"""
        pvt = getToolByName(self, 'portal_vocabularies', '')
        VOCAB = getattr(pvt, 'Subcategory', '')
        vd = VOCAB.getVocabularyDict(self)
        toplevel = [(k, vd[k][0]) for k in vd.keys()]
        DL = DisplayList(toplevel)
        return DL

    def contentTypesDL(self):
        """ return valid types to select """
        util = getUtility(ITypesGetter, name="alertservice.typesgetter")
        return util(self)