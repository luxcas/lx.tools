from  lx.tools.testing import LX_TOOLS_FUNCTIONAL_TESTING
from plone.testing import layered
import robotsuite
import unittest


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(robotsuite.RobotTestSuite("robot_test.txt"),
                layer=LX_TOOLS_FUNCTIONAL_TESTING)
    ])
    return suite