#!/bin/bash
# kudos to Products.Ploneboard for the base for this file
# ensure that when something is wrong, nothing is broken more than it should...
set -e

# first, create some pot containing anything
i18ndude rebuild-pot --pot lx.tools.pot --create lx.tools --merge manual.pot ..

# finally, update the po files
i18ndude sync --pot lx.tools.pot  `find . -iregex '.*lx.tools\.po$'|grep -v plone`

