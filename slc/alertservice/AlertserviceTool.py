from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from OFS.Folder import Folder
import AccessControl
from DateTime import DateTime
from Products.BTreeFolder2.BTreeFolder2 import manage_addBTreeFolder, BTreeFolder2, BTreeFolder2Base
from Products.ZCatalog.ZCatalog import ZCatalog
from slc.alertservice.NotificationProfile import NotificationProfile

from Globals import InitializeClass


class AlertserviceTool(PloneBaseTool, Folder):
    """ Manage alert subscriptions """

    id = 'portal_alertservice'
    meta_type = 'Alertservice Tool'
    plone_tool = 1
    toolicon = 'skins/alertservice/alertservice_icon.gif'
    
    __implements__ = (PloneBaseTool.__implements__,)

    security = AccessControl.ClassSecurityInfo()
    
    def __init__(self, id='portal_alertservice'):
        " "
        self.id = id

#        # BTreeFolder for alerts
#        id_alerts = "alerts"
#        a = BTreeFolder2(id_alerts)
#        a.title = 'Alerts'
#        self._setObject(id_alerts, a)
#        self.id_alerts = id_alerts

        # BTreeFolder for notifications
        id_nprofiles = "nprofiles"
        n = BTreeFolder2(id_nprofiles)
        n.title = 'Notifications'
        self._setObject(id_nprofiles, n)
        self.id_nprofiles = id_nprofiles

        # Adding Catalog support
        c=ZCatalog('AlertCatalog', 'Alert Catalog', self)
        self._setObject('AlertCatalog', c)
        zcat = getattr(self, 'AlertCatalog')

        schema = zcat.schema()
        indices = [
          ('id', 'FieldIndex'),
          ('getMemberUserName', 'FieldIndex'),
          ('getEventTypes', 'KeywordIndex'),
          ('getSchedule', 'FieldIndex'),
          ('getEMail', 'FieldIndex'),
          ('getObjectID', 'FieldIndex'),
          ('getObjectURL', 'FieldIndex'),
          ('getObjectOID', 'FieldIndex')
          ]
        for (i, t) in indices:
          if i not in zcat.indexes():
              zcat.manage_addIndex(i, t)
          if i not in schema:
              zcat.manage_addColumn(i)



    def generateSearchMap(self, notification_period, limit, searchmap):
        """
            Completes the given catalog query searchmap using the current date
        """
        try:
            notification_period = int(notification_period)
        except:
            notification_period = 7
        modified = DateTime()-notification_period

        try:
            limit = int(limit)
        except:
            limit = 0

        searchmap['modified'] = {'query': modified, 'range':'min'}
        searchmap['notification_period'] = notification_period
        searchmap['limit'] = limit

        return searchmap


    def existsNotificationProfile(self, memberUserName=None):
        """
            Returns True if a notification profile exists for a given member,
            and False otherwise.
        """
        #memberUserName = self.checkMemberUserName(memberUserName)
        nfolder = getattr(self, self.id_nprofiles)
        if memberUserName is None or not nfolder.has_key(memberUserName):
            return False
        return True


    def getNotificationProfile(self, memberUserName=None):
        """
            Returns the notification profile for a given member.
        """
        #memberUserName = self.checkMemberUserName(memberUserName)
        if memberUserName is None:
            return None

        nfolder = getattr(self, self.id_nprofiles)
        nprofile = nfolder.get(memberUserName, None)
        return nprofile


    def createNotificationProfile(self, memberUserName=None):
        """
            Create a new notification profile
        """
        #memberUserName = self.checkMemberUserName(memberUserName)
        if memberUserName is None:
            return None

        nfolder = getattr(self, self.id_nprofiles)

        # if no profile exists, create a new one
        if not nfolder.has_key(memberUserName):
            np = NotificationProfile(memberUserName)
            nfolder._setObject(memberUserName, np)

        nprofile = nfolder.get(memberUserName, None)
        return nprofile


    def deleteNotificationProfile(self, memberUserName):
        """
            Deletes the notification profile for the given member name
        """
        nfolder = getattr(self, self.id_nprofiles)
        if nfolder.has_key(memberUserName):
            nfolder._delObject(memberUserName)


    def getNotificationById(self, memberUserName=None, id=None):
        """
            Returns the notification by id for the given member, if it exists
        """
        nprofile = self.getNotificationProfile(memberUserName)
        if nprofile is None:
            return {}

        return nprofile.getNotification(id)


    security.declarePublic('manage_deleteNotifications')
    def manage_deleteNotifications(self, memberUserName=None, ids=[]):
        """
            Delete notifications with given ids from the member's notification profile
        """
        #memberUserName = self.checkMemberUserName(memberUserName)
        np = self.getNotificationProfile(memberUserName)
        if not np:
            return

        if not getattr(ids, 'append', None):
            ids = [ids]

        for id in ids:
            np.delNotification(id)

        # if the notification profile is now empty, delete it
        if np.isEmpty():
            self.deleteNotificationProfile(memberUserName)


    def sendConfirmationMessage(self, profile_id):
        """ sends a confirmation out to the user to agree to the change of his profile """
        from utils import decodeEmail
        email = decodeEmail(profile_id)
        from_addr = self.portal_properties.site_properties.email_from_address
        to = '%s <%s>' % (email, email)
        subject = "Click to confirm your Alert"
        origin_host = self.REQUEST['SERVER_URL']
        np = self.getNotificationProfile(profile_id)
        url_params = dict(origin_host=origin_host, tool=self.id, profile_id=profile_id, key=np._getSecretKey())
        verify_url="%(origin_host)s/%(tool)s/verify_alert?s=%(profile_id)s&k=%(key)s" % url_params
        remove_url="%(origin_host)s/%(tool)s/remove_alert?s=%(profile_id)s&k=%(key)s" % url_params
        body = self.alert_confirm_email_template(email=email, verify_url=verify_url, remove_url=remove_url,  origin_host=origin_host)
        mh = self.MailHost
        try:
            charset = getToolByName(self, 'portal_properties').site_properties.default_charset
        except Exception,e:
            charset = "utf-8"
        try:
            mh.secureSend( message=body, mto=email, mfrom=from_addr, subject=subject, subtype="plain", charset=charset)
        except:
            return "Could not send the confirmation email!"
        return ''

    def verify_alert(self, s, k):
        """ If an inactive profile exists with that ID, it gets switched to active """
        np = self.getNotificationProfile(s)
        if k != np._getSecretKey():
            msg = "This url is not valid, no alert found"
            return self.alertservice_feedback_view(msg=msg)
        N = np._notifications
        changed = 0
        for key in N.keys():
            if N[key]['active'] != 1:
                N[key]['active'] = 1
                changed = 1
        if changed == 1:
            np._notifications = N
            msg = "Your alert is now activated."
        else:
            msg = "Your alert has already been activated."
        return self.alertservice_feedback_view(msg=msg)

    def remove_alert(self, s, k):
        """ if a profile exists with that ID, it gets removed """
        np = self.getNotificationProfile(s)
        if np:
            if k != np._getSecretKey():
                msg = "This url is not valid, no alert found"
            else:
                self.deleteNotificationProfile(s)
                msg = "Your alert has been removed."
        else:
            msg = "There is no such alert."

        return self.alertservice_feedback_view(msg=msg)

InitializeClass(AlertserviceTool)