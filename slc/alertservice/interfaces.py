from zope.interface import Interface

class ISubjectGetter(Interface):
    """A utility capable of providing possible subjects for an alert
    """
    
    def __call__(context):
        """Return DisplayList of subjects
        """


class ITypesGetter(Interface):
    """A utility capable of providing possible types for an alert
    """
    
    def __call__(context):
        """Return DisplayList of types
        """