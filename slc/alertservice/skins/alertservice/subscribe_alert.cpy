## Controller Python Script "subscribe_alert"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=Subscribe to alerts by user email address
##
from Products.AdvancedQuery import Le, Ge, In, Eq, And, Or
from Products.CMFCore.utils import getToolByName
request = context.REQUEST
error = ''
from osha.policy.utils import logit
from slc.alertservice import AlertMessageFactory as _
helper = context.restrictedTraverse("@@subscribe_helper")
from slc.alertservice.utils import encodeEmail

alerttool = getToolByName(context, 'portal_alertservice')
now = DateTime()
ppath = context.portal_url.getPortalPath()
reg_tool=context.portal_registration

PERSONAL_ALERT_ID = helper.getPersonalAlertId()

# retrieving alert settings
if request.has_key('form.button.Save'):
    email = request.get('email', '')
    if reg_tool.isValidEmail(email):
        pass
    else:
        msg = _(u'You did not enter a valid email address.')
        state.setError('email', 
                        msg,
                       'invalid_email')
        return state.set(status='emailfailure', context=context, portal_status_message='Please correct the indicated errors.')



# Subscribing to a new alert
settings = {}
settings['Subject'] = subjects = request.get('Subject', [])
settings['schedule'] = schedule = request.get('schedule', '30')
settings['limit'] = limit = request.get('limit', '25')
settings['alert_title'] = alert_title = 'EU-OSHA Web Alert - %s' % ", ".join(subjects)
settings['email'] = email = request.get('email', '')
settings['portal_type'] = portal_type = request.get('portal_type', 'all')
settings['preferredLanguages'] = preferredLanguages = request.get('Language', ['en'])

logit('portal_type', portal_type)

b2a_email = encodeEmail(email)


OType = list()
if portal_type =='all':
    OType = helper.contentTypesDL().keys()
    logit('OType:', OType)
else:
    if not getattr(portal_type, 'append', None):
        OType = [portal_type]
    else:
        OType = portal_type

if 'en' not in preferredLanguages :
    preferredLanguages.append('en')
preferredLanguages = tuple(preferredLanguages)


searchmap = {}
searchmap['settings'] = settings
searchmap['id'] = PERSONAL_ALERT_ID
searchmap['title'] = alert_title
searchmap['active'] = 0
searchmap['Language'] = []
searchmap['Subject'] = subjects
#searchmap['path'] = []
#searchmap['topics'] = []
#searchmap['site_position'] = []


# manually create the advanced query
query = Eq('review_state', 'published')
if OType:
    query = query &  In('portal_type', OType)
    searchmap['portal_type'] = OType

if preferredLanguages:
    query = query & In('Language', preferredLanguages)
    searchmap['Language'] = {'query': preferredLanguages}


#query = query

#searchmap['path'] = {'query': searchmap['path']}

searchmap['advanced_query'] = query



smap = alerttool.generateSearchMap( notification_period=schedule
                                         , limit = limit
                                         , searchmap = searchmap
                                         )



if alerttool.existsNotificationProfile(b2a_email):
    np = alerttool.getNotificationProfile(b2a_email)
else:
    np = alerttool.createNotificationProfile(b2a_email)
    
logit([alerttool.existsNotificationProfile(b2a_email)])
logit('\nnp:\n', np)

# see if an alert exists by that id
alert = np.getNotification(PERSONAL_ALERT_ID)

if alert:
    np.editNotification(id=PERSONAL_ALERT_ID, searchmap=smap)
else:
    np.addNotification(id=PERSONAL_ALERT_ID, searchmap=smap)

# If alert is added as inactive successfully, send an email out to the user to confirm
error += alerttool.sendConfirmationMessage(b2a_email)

# Subscribe to oshmail if user has requested this
if request.get('oshmail', 0):
    context.subscribeOSHMail(emailaddress=email)

error = error.strip()

if error=='':
    return state.set(status='success', context=context, portal_status_message='Subscription successful.', settings=settings)
else:
    return state.set(status='failure', context=context, portal_status_message='Please correct the indicated errors. %s' % [error])

