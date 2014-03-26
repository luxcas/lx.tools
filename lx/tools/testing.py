from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from plone.testing import z2

from zope.configuration import xmlconfig


class LxtoolsLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import lx.tools
        xmlconfig.file(
            'configure.zcml',
            lx.tools,
            context=configurationContext
        )

        # Install products that use an old-style initialize() function
        #z2.installProduct(app, 'Products.PloneFormGen')

#    def tearDownZope(self, app):
#        # Uninstall products installed above
#        z2.uninstallProduct(app, 'Products.PloneFormGen')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'lx.tools:default')

LX_TOOLS_FIXTURE = LxtoolsLayer()
LX_TOOLS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(LX_TOOLS_FIXTURE,),
    name="LxtoolsLayer:Integration"
)
LX_TOOLS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(LX_TOOLS_FIXTURE, z2.ZSERVER_FIXTURE),
    name="LxtoolsLayer:Functional"
)
