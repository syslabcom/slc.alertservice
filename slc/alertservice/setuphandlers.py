from Products.CMFCore.utils import getToolByName



def setupVarious(context):
    
    # Ordinarily, GenericSetup handlers check for the existence of XML files.
    # Here, we are not parsing an XML file, but we use this text file as a 
    # flag to check that we actually meant for this import step to be run.
    # The file is found in profiles/default.
    
    if context.readDataFile('slc.alertservice_various.txt') is None:
        return
    
    site=context.getSite()
    
    # add the Alertservice Tool
    site.manage_addProduct['slc.alertservice'].manage_addTool(type='Alertservice Tool')
