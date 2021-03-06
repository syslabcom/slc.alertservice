import sha
from Acquisition import aq_base, aq_parent, aq_inner
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
from Globals import InitializeClass, DTMLFile
from OFS.SimpleItem import SimpleItem

class NotificationProfile(SimpleItem):
    " a lightweight object for storing a member's notification profile "

    meta_type = "NotificationProfile"
    security = ClassSecurityInfo()

    id_counter = 0


    _notifications = {}

    def __init__(self, id):
        self.id = id
        self.id_counter = 0
        self._notifications = {}


    def addNotification(self, searchmap, id=None):
        " add a notification with a newly created id "
        if not id:
            id = self._generateId()

        self._edit(id, searchmap)


    def editNotification(self, id, searchmap):
        " edit an existing notification "
        if self._notifications.has_key(id):
            self._edit(id, searchmap)

    def _persistSearchmap(self, id, searchmap):
        ntf = self._notifications
        ntf[id] = searchmap
        self._notifications = ntf

    def _edit(self, id, searchmap):
        " do the actual editing "
        ntf = self._notifications
        ntf[id] = searchmap
        self._notifications = ntf
        keybase = "%s:%s" %(id, DateTime().ISO())
        self._secretKey = sha.new(keybase).hexdigest()

    def _getSecretKey(self):
        """ returns the secret key to avoid misuse if someone knows the users email """
        return self._secretKey

    def delNotification(self, id):
        " delete a notification "
        if self._notifications.has_key(id):
            ntf = self._notifications
            del ntf[id]
            self._notifications = ntf


    def getNotification(self, id):
        " returns a notification by id "
        if self._notifications.has_key(id):
            return self._notifications[id]
        return {}

    def getNotifications(self):
        " returns the notifications-mapping with all notifications"
        return self._notifications

    def listNotifications(self):
        " returns a list of all notifications "
        return self._notifications.values()


    def isEmpty(self):
        " are any notifications stored in this profile "
        return len(self._notifications.keys()) == 0


    def _generateId(self):
        " generate a unique internal id "
        self.id_counter +=1
        return str(self.id_counter)


InitializeClass(NotificationProfile)
