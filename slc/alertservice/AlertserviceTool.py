from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from OFS.Folder import Folder

from Globals import InitializeClass


class AlertserviceTool(PloneBaseTool, Folder):
    """ Manage alert subscriptions """

    id = 'portal_alertservice'
    meta_type = 'Alertservice Tool'
    plone_tool = 1
    toolicon = 'skins/alertservice/alertservice_icon.gif'
    
    __implements__ = (PloneBaseTool.__implements__,)

InitializeClass(AlertserviceTool)