
def initialize(context):
    """Initializer called when used as a Zope 2 product."""
    
    from AccessControl import allow_module
    allow_module('slc.alertservice.utils')
    
    import AlertserviceTool
    tools = (AlertserviceTool.AlertserviceTool, )
    

    
    from Products.CMFPlone.utils import ToolInit
    # Register tools and content
    ToolInit('Alertservice Tool'
             , tools=tools
             , icon='skins/alertservice/alertservice_icon.gif'
             ).initialize( context )


from zope.i18nmessageid import MessageFactory
AlertMessageFactory = MessageFactory('slc.alertservice')
