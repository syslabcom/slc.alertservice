from zope.interface import Interface, Attribute

class ISubscribeForm(Interface):
    """ utility methods for subscription handling """


class ISubscribeHelper(Interface):
    """ a dummy helper class """
    
    def contentSubjectsDL():
        """ get possible subjects as DisplayList """

    def contentTypesDL():
        """ get possible content types as DisplayList """

    def getPersonalAlertId():
        """ returns id under which the notification alert gets saved """

    def getUserSettings():
        """ returns exisitng settings for a given user """