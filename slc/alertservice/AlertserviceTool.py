from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from OFS.Folder import Folder
import AccessControl, os
from DateTime import DateTime
from Products.BTreeFolder2.BTreeFolder2 import manage_addBTreeFolder, BTreeFolder2, BTreeFolder2Base
from Products.ZCatalog.ZCatalog import ZCatalog
from slc.alertservice.NotificationProfile import NotificationProfile
from utils import encodeEmail, decodeEmail
from Products.CMFCore.utils import getToolByName
from Products.AdvancedQuery import Le, Ge, In, Eq, And, Or
from slc.alertservice.config import triggerkey
from slc.alertservice import AlertMessageFactory as _
from zope.i18n import translate
import zLOG
import transaction
from zope.component import getMultiAdapter

from Globals import InitializeClass


def getTriggerkey():
    return triggerkey


DO_LOG = True

def log( *kwargs):
    " log something "
    if DO_LOG:
        try:
            mesg = ''
            for kwarg in kwargs:
                mesg += str(kwarg) + ' '
            print mesg
            zLOG.LOG('AlertService', zLOG.INFO,
              mesg)
        except:
            print [kwargs]

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


        # BTreeFolder for notifications
        id_nprofiles = "nprofiles"
        n = BTreeFolder2(id_nprofiles)
        n.title = 'Notifications'
        self._setObject(id_nprofiles, n)
        self.id_nprofiles = id_nprofiles



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


    def handleSubscription(self, request=None, doNotSendConfirmation=False):
        """ do the necessary steps for creating a subscription 
        doNotSendConfirmation: this param can be used for scripted adding of nprofiles"""
        if request is None:
            request = self.REQUEST

        error = ''
        helper = self.restrictedTraverse("@@subscribe_helper")
        PERSONAL_ALERT_ID = helper.getPersonalAlertId()

        settings = dict()
        settings['Subject'] = subjects = request.get('Subject', [])
        settings['schedule'] = schedule = request.get('schedule', '30')
        settings['limit'] = limit =  request.get('limit', '25')
        settings['alert_title'] = 'Web Alert - %s' % ", ".join(subjects)
        settings['email'] = request.get('email', '')
        settings['portal_type'] = portal_type = request.get('portal_type', 'all')
        settings['preferredLanguages'] = preferredLanguages = request.get('Language', ['en'])

        b2a_email = encodeEmail(settings['email'])

        have_publications = False
        OType = list()
        if portal_type =='all' or portal_type==['all']:
            OType = helper.contentTypesDL().keys()
        else:
            if not getattr(portal_type, 'append', None):
                OType = [x for x in [portal_type] ]
            else:
                OType = [x for x in portal_type]
        if 'Publication' in OType:
            have_publications = True

        # English is always searched for
        if 'en' not in preferredLanguages :
            preferredLanguages.append('en')
        # Language neutral is always searched for
        if '' not in preferredLanguages:
            preferredLanguages.append('')
        preferredLanguages = tuple(preferredLanguages)

        searchmap = {}
        searchmap['settings'] = settings
        searchmap['id'] = PERSONAL_ALERT_ID
        searchmap['title'] = settings['alert_title']
        searchmap['active'] = 0
        searchmap['Language'] = []
        searchmap['Subject'] = []

        # manually create the advanced query
        query = Eq('review_state', 'published')
        if OType:
            if have_publications:
                OType.remove('Publication')
                query = query & Or( 
                    In('portal_type', OType), 
                    And(
                        In('portal_type', 'File'), In('object_provides', 'slc.publications.interfaces.IPublicationEnhanced')
                        ) 
                ) 
            else:
                query = query & In('portal_type', OType)
            searchmap['portal_type'] = portal_type

        if preferredLanguages:
            query = query & In('Language', preferredLanguages)
            searchmap['Language'] =  preferredLanguages

        if subjects:
            query = query & In('Subject', subjects)

#        if have_publications:
#            query = query & In('object_provides', 'slc.publications.interfaces.IPublicationEnhanced')

#        log('my final query:', query)
        searchmap['advanced_query'] = query
        
        smap = self.generateSearchMap( notification_period=schedule
                                                 , limit = limit
                                                 , searchmap = searchmap
                                                 )

        if self.existsNotificationProfile(b2a_email):
            np = self.getNotificationProfile(b2a_email)
        else:
            np = self.createNotificationProfile(b2a_email)
        
        # see if an alert exists by that id
        alert = np.getNotification(PERSONAL_ALERT_ID)
        
        if alert:
            np.editNotification(id=PERSONAL_ALERT_ID, searchmap=smap)
        else:
            np.addNotification(id=PERSONAL_ALERT_ID, searchmap=smap)
        
        if not doNotSendConfirmation:
            # If alert is added as inactive successfully, send an email out to the user to confirm
            error += self.sendConfirmationMessage(b2a_email)
            
        return error


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
        
        email = decodeEmail(profile_id)
        sp = self.portal_properties.site_properties
        from_addr = getattr(sp, 'notification_email_from_address', getattr(sp, 'email_from_address'))
        to = '%s <%s>' % (email, email)
        plt = getToolByName(self, 'portal_languages')
        lang = plt.getPreferredLanguage()
        subject_msg = _(u'click_to_confirm', default=u"Click to confirm your Alert")
        subject = translate(subject_msg, target_language=lang)
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

    def verify_alert(self, s=None, k=None):
        """ If an inactive profile exists with that ID, it gets switched to active """
        np = self.getNotificationProfile(s)
        if np is None:
            msg = _(u'no_alert_found', default=u"No alert was found. Please create a new alert.")
            return self.alertservice_feedback_view(msg=msg)
        if k != np._getSecretKey():
            msg = _(u'url_not_valid', default=u"This url is not valid, no alert found")
            return self.alertservice_feedback_view(msg=msg)
        N = np._notifications
        changed = 0
        for key in N.keys():
            if N[key]['active'] != 1:
                N[key]['active'] = 1
                changed = 1
        if changed == 1:
            np._notifications = N
            msg = _(u'alert_activated', default=u"Your alert is now activated.")
        else:
            msg = _(u'alert_already_activated', default=u"Your alert has already been activated.")
        return self.alertservice_feedback_view(msg=msg)

    def remove_alert(self, s=None, k=None):
        """ if a profile exists with that ID, it gets removed """
        np = self.getNotificationProfile(s)
        if np:
            if k != np._getSecretKey():
                msg = _(u'url_not_valid', default=u"This url is not valid, no alert found")
            else:
                self.deleteNotificationProfile(s)
                msg = _(u'alert_removed', default=u"Your alert has been removed.")
        else:
            msg = _(u"There is no such alert.")

        return self.alertservice_feedback_view(msg=msg)

    def getUserProfile(self):
        """ fetches user settings, if s and k are given, returns None otherwise """
        REQUEST = self.REQUEST
        s = REQUEST.get('s', '')
        k = REQUEST.get('k', '')
#        log( "Have s and k", s, k)
        if not (s and k):
            return {}
        np = self.getNotificationProfile(s)
        if np:
            if k != np._getSecretKey():
                return {}
            else:
                return np.getNotifications()
        else:
            return {}

    ###############################################################################################
    ##
    ## Trigger and send methods
    ##
    ###############################################################################################

    security.declarePublic('triggerGeneralNotification')
    def triggerGeneralNotification(self):
        " triggers the notification of all users which have a notification profile "
        request = self.REQUEST
        tk = request.get('tk', '')
        if tk != getTriggerkey():
            return "Illegal triggerkey supplied"
        now = request.get('now', 0)
        maxnumber = request.get('maxnumber', 0)
        ids = request.get('ids', [])
        log("\n\ntriggerGeneralNotification")
        profile_ids = self.nprofiles.objectIds()
        log("profiles", len(profile_ids))
        count = 0
        for profile_id in profile_ids:
            count += self.generateNotification(profile_id=profile_id, now=now, 
                maxnumber=maxnumber, current_count=count, ids=ids)
            if  count % 25 == 0:
                log("%d emails sent so far" %count)
                transaction.commit()
            if maxnumber>0 and count>=maxnumber:
                log("triggerGeneralNotification:: breaking because count(%d) >= max(%d)" %(count,maxnumber) )
                break
        log("number of Mails sent: %d" %count)
        return "number of Mails sent: %d" %count


    def showAllResultsForProfile(self, profile_id=None):
        """ Return all results for a certain profile, to be displayed in the browser, not sent in an alert """
        if profile_id is None:
            return []

        email = decodeEmail(profile_id)
        notification_profile = self.getNotificationProfile(profile_id)
        fullname = email

        if (email is None) or (notification_profile is None):
            return 0

        currentDateTime = DateTime()
        notifications = notification_profile.getNotifications()
        keys = notifications.keys()
        for k in keys:
            searchmap = notifications.get(k)
            sm = searchmap.copy()
            period = int(sm.get('notification_period', 0))
            oldrun = sm.get('lastrun', None)
            eff = currentDateTime - period
            if oldrun and isinstance(oldrun, DateTime) and oldrun < eff:
                eff = oldrun
            sm['effective'] = {'query': eff, 'range':'min'}
            results = self.generateNotificationResults(sm, fullname, pure_results=True)
            return results


    def generateNotification(self, profile_id=None, now=0, maxnumber=0, current_count=0, ids=[]):
        """ generates a notification email for a search result based on a preselected set of catalog queries """
        if profile_id is None:
            return 0
#        log( "In generateNotification", profile_id)

        
#        log( "generateNotification. maxnumber: %d, current_count: %d" %(maxnumber, current_count))
        email = decodeEmail(profile_id)
        notification_profile = self.getNotificationProfile(profile_id)
        fullname = email

        if (email is None) or (notification_profile is None):
            return 0

        origin_host = self.REQUEST['SERVER_URL']
        url_tool = getToolByName(self, 'portal_url')
        portal = url_tool.getPortalObject()
        mh = getToolByName(self, 'MailHost')
        props_tool = getToolByName(self, 'portal_properties')
        mfrom = getattr(props_tool, 'notification_email_from_address', getattr(props_tool, 'email_from_address'))
        subj_msg = _(u'notification_from', default=u"Notification from")
        subject = "%s %s" %(translate(subj_msg), origin_host)

        mail_sent = 0

        currentDateTime = DateTime()
        notifications = notification_profile.getNotifications()
        secretkey = notification_profile._getSecretKey()
        # if ids was passed, only send those notifications specified
        keys=[]
        if len(ids)>0:
            keys = [x for x in ids if notifications.has_key(x)]

        # no valid keys were passed, so get all
        if len(keys)==0:
            keys = notifications.keys()

#        log( "Keys to process:", keys)
        for k in keys:
            searchmap = notifications.get(k)
            active = int(searchmap.get('active', 0))
            if not active:
#                log( "Continuing because profile %s in inactive" %k)
                continue
            period = int(searchmap.get('notification_period', 0))
            lastrun = searchmap.get('lastrun', DateTime(0))

            # Notify only if 'period' has passed since last notification run
            # or notification is forced via 'run'
            perioddelta = float(period)-0.1 
            # it doesnt matter if period is slightly less because we run the script only once a day anyway.
            if (currentDateTime < lastrun+perioddelta) and now==0:
#                log( "continuing because of lastrun period", currentDateTime, lastrun+perioddelta)
                continue

            # Update the lastrun attribute, setting it to the current DateTime
            oldrun = searchmap.get('lastrun', None)
            searchmap['lastrun'] = currentDateTime

            # update the 'effective' parameter with the current DateTime minus period,
            # or with the old lastrun date, if it lies before it.
            eff = currentDateTime - period
            if oldrun and isinstance(oldrun, DateTime) and oldrun < eff:
                eff = oldrun
            searchmap['effective'] = {'query': eff, 'range':'min'}

            # Generate the Mailbody
            result_keywords = self.generateNotificationResults(searchmap, fullname)
#            log('I just called generateNotificationResults. My results are:\n', result_keywords)
            if result_keywords is None: # No search results for this time
#                log( "continuing because text is none")
                continue
            # Everything is fine, we found results,
            # we have stepped over the period of waiting, letz send
            msubject = ''
            if hasattr(portal, 'generateAlertServiceMailSubject'):
                try:
                    msubject = portal.generateAlertServiceMailSubject(searchmap)
                except:
                    msubject = ''
            if msubject and type(msubject)==type(''):
                subject=msubject

            try:
                charset = props_tool.site_properties.default_charset
            except Exception,e:
                charset = "utf-8"
            url_params = dict(origin_host=origin_host, tool=self.id, profile_id=profile_id, key=secretkey)
            result_keywords['edit_url'] = "%(origin_host)s/subscribe_form?s=%(profile_id)s&k=%(key)s" % url_params
            result_keywords['remove_url'] = "%(origin_host)s/%(tool)s/remove_alert?s=%(profile_id)s&k=%(key)s" % url_params
            result_keywords['more_url'] = "%(origin_host)s/show_all_alert_results?s=%(profile_id)s&k=%(key)s" % url_params
            
            body = self.alert_notification_template(**result_keywords)
            try:
                mh.secureSend(message=body, mto=email, mfrom=mfrom, 
                    subject=subject, subtype="html", charset=charset)
            except Exception, why:
                import pdb; pdb.set_trace()
#                log( "Could not send the confirmation email!")
                return mail_sent
                
#            self.portal_utilities.send_mail( variables = variables,
#                                            template = "alert_notification_template",
#                                            mailhost = "MailHost",
#                                            validate_to_address = 0,
#                                            convert_to_html = 0,
#                                            **result_keywords
#                                          )

            mail_sent += 1
            current_count+=1

            # persist the changes to the notification
            #XXX
            notification_profile._persistSearchmap(k, searchmap)

            if maxnumber>0 and current_count>=maxnumber:
#                 print "generateNotification: breaking because count (%d) >= max(%d)" %(current_count, maxnumber)
                break
        
        return mail_sent




    security.declarePublic('generateNotificationResults')
    def generateNotificationResults(self, searchmap, fullname, pure_results=False):
        " computes results for a given profile "
        searchmap = searchmap.copy()
#        log( "\n----generateNotificationResults:", searchmap)
        pc = getToolByName(self, 'portal_catalog')
        if hasattr(pc, 'getZCatalog'):
            pc = pc.getZCatalog()
        purl = getToolByName(self, 'portal_url').getPortalPath()

        origin_host = self.REQUEST['SERVER_URL']

        notification_id = searchmap.get('title', '')
        notification_date = DateTime()
        limit = searchmap.get('limit', 0)

        if searchmap.has_key('lastrun'):
            del searchmap['lastrun']
        if searchmap.has_key('title'):
            del searchmap['title']
        if searchmap.has_key('active'):
            del searchmap['active']
        if searchmap.has_key('id'):
            del searchmap['id']
        if searchmap.has_key('limit'):
            del searchmap['limit']

        notification_period = searchmap['notification_period']
        notification_period = int(notification_period)
        del searchmap['notification_period']

        effective = searchmap.get('effective', {}).get('query', '')
        results = []
        query = searchmap['advanced_query']

        now = DateTime()
        # discard items that are expired
        query = query & Ge('effective', effective) & ~ Le('expires', now)
        # discard items that aren't effective yet
        query = query & ~ Ge('effective', now)

        # discard unwanted content
        exclude_paths = self.getProperty('exclude_paths')
        if exclude_paths:
            exclude_paths = [x for x in exclude_paths if x.strip()!='']
            exclude_paths = [x[1:] for x in exclude_paths if x.startswith('/')]
            if len(exclude_paths):
                portal_state = getMultiAdapter((self, self.REQUEST), name=u'plone_portal_state')
                navigation_root_path = portal_state.navigation_root_path()
                unwanted =[os.path.join(navigation_root_path, xp) for xp in exclude_paths]
                query = query & ~In('path', unwanted)
#        log('\n advanced_query: ', query)

        results = pc.evalAdvancedQuery(query, (('effective','desc'),))

        if pure_results:
            return results

        numresults = len(results)
#        log('I have %d results' %numresults)

        if 0 < limit < numresults:
            results = results[:limit]

        if len(results)==0:
#            log( "ALERT: No Searchresults for user", fullname)
            return None

        md = self.portal_membership

        result_keywords = { 'results' : results,
                                             'numresults' : numresults,
                                             'siteurl' : origin_host,
                                             'notification_period' : notification_period,
                                             'user_name' : fullname,
                                             'effective' : effective,
                                             'topic' : '',
                                             'notification_id' : notification_id,
                                             'notification_date' :notification_date,
                                             'searchmap' : searchmap
                                          }

        return result_keywords


    security.declarePublic('notification_order_results')
    def notification_order_results(self, results):
        """ order the results for the notification email"""
        RESMAP = dict()

        for R in results:
          T = R.portal_type
          if T == 'OSH_Link': T = 'Link'
          if T == 'File': T = 'Publication'
          mylist = RESMAP.get(T, list())
          mylist.append(R)
          RESMAP[T] = mylist
        return RESMAP

InitializeClass(AlertserviceTool)