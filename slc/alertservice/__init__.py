
def initialize(context):
    """Initializer called when used as a Zope 2 product."""
    
    import AlertserviceTool
    tools = (AlertserviceTool.AlertserviceTool, )
    
    from Products.CMFPlone.utils import ToolInit
    # Register tools and content
    ToolInit('Alertservice Tool'
             , tools=tools
             , icon='skins/alertservice/alertservice_icon.gif'
             ).initialize( context )
