from interfaces import ISubscribeForm
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import re
from zope import schema
from slc.alertservice import AlertMessageFactory as _
from AccessControl import safe_builtins
from zope.component import getUtility
from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.utils import DisplayList
from slc.alertservice.interfaces import ITypesGetter

# Define a valiation method for email addresses
class NotAnEmailAddress(schema.ValidationError):
    __doc__ = _(u"Invalid email address")

check_email = re.compile(r"[a-zA-Z0-9._%-]+@([a-zA-Z0-9-]+\.)*[a-zA-Z]{2,4}").match
def validate_email(value):
    if not check_email(value):
        raise NotAnEmailAddress(value)
    return True

class SubscribeForm(BrowserView):
    implements(ISubscribeForm)
    
    template = ViewPageTemplateFile('subscribe_form.pt')
    
    def __call__(self):
        """ do the subscription """
        
        print "someone called?"
        
        self.request.set('disable_border', True)
        
        postback = True
        form = self.request.form
        submitted = form.get('form.submitted', False)
        save_button = form.get('form.button.Save', None) is not None
        
        if submitted and save_button:
            email = form.get('email', '')
            validate_email(email)
        
        import pdb; pdb.set_trace()
        return self.template()

    def getTestFunction(self):
        """return the 'test' python method available in PageTemplaes """
        return safe_builtins.get('test')


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