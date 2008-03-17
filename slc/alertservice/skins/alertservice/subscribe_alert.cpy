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
from Products.CMFCore.utils import getToolByName
request = context.REQUEST
error = ''
from slc.alertservice import AlertMessageFactory as _

alerttool = getToolByName(context, 'portal_alertservice')
reg_tool=getToolByName(context, 'portal_registration')


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
error = alerttool.handleSubscription(request)

error = error.strip()

if error=='':
    return state.set(status='success', context=context, portal_status_message='Subscription successful.')
else:
    return state.set(status='failure', context=context, portal_status_message='Please correct the indicated errors. %s' % [error])

