from Products.Five.testbrowser import Browser
from Products.CMFCore.utils import getToolByName
import unittest

from zope.testing import doctestunit
from zope.component import testing
from Testing import ZopeTestCase as ztc
from Testing.ZopeTestCase import utils

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Products.PloneTestCase.setup import portal_owner, default_password

import slc.alertservice

def startZServer(browser=None):
    host, port = utils.startZServer()
    if browser:
        print browser.url.replace('nohost', '%s:%s' % (host, port))

def getBrowser(url):
    browser = Browser()
    browser.open(url)
    browser.getControl(name='__ac_name').value = portal_owner
    browser.getControl(name='__ac_password').value = default_password
    browser.getControl(name='submit').click()
    return browser

class TestCase(ptc.FunctionalTestCase):
    class layer(PloneSite):
        @classmethod
        def setUp(cls):
            import Globals
            Globals.DevelopmentMode = True
            ztc.installProduct('PrintingMailHost')

            ztc.installProduct('PlacelessTranslationService')
            ptc.setupPloneSite(products=['slc.alertservice'])
            fiveconfigure.debug_mode = True
            zcml.load_config('configure.zcml',
                             slc.alertservice)
            import Products.PlacelessTranslationService
            zcml.load_config('configure.zcml', Products.PlacelessTranslationService)
            fiveconfigure.debug_mode = False
            ztc.installPackage('Products.PlacelessTranslationService', quiet=True)
            ztc.installPackage('slc.alertservice')
            PloneSite.setUp()

        @classmethod
        def tearDown(cls):
            pass
        


class BasicTests(TestCase):
    def setUp(self):
        super(BasicTests, self).setUp()
        self.browser = getBrowser(self.portal.absolute_url())
        getToolByName(self, 'portal_properties').site_properties.notification_email_from_address = 'info@syslab.com' 

    def test_alertRegistrationWorks(self):
        url = self.portal.absolute_url() + '/subscribe_form'
        self.browser.open(url)
        self.browser.getControl('email').value = 'info@syslab.com'
        self.browser.getControl('Create alert').click()
        self.assertTrue('Subscription successful' in self.browser.contents)
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BasicTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
