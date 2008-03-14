from zope.interface import Interface, Attribute

class ISubscribeForm(Interface):
    """ utility methods for subscription handling """


class ISubscribeHelper(Interface):
    """ a dummy helper class """
    
    def contentSubjectsDL():
        """ get possible subjects as DisplayList """

    def contentTypesDL():
        """ get possible content types as DisplayList """