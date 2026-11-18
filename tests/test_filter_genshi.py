#!/usr/bin/env python

import unittest, xml.dom.minidom
from planet import shell, config

try:
    import genshi
    GENSHI_AVAILABLE = True
except:
    GENSHI_AVAILABLE = False

@unittest.skipUnless(
    GENSHI_AVAILABLE,
    "Genshi is not available => can't test genshi filters"
)
class GenshiFilterTests(unittest.TestCase):

    def test_addsearch_filter(self):
        testfile = 'tests/data/filter/index.html'
        filter = 'addsearch.genshi'
        output = shell.run(filter, open(testfile).read(), mode="filter")
        self.assertTrue(output.find('<h2>Search</h2>')>=0)
        self.assertTrue(output.find('<form><input name="q"/></form>')>=0)
        self.assertTrue(output.find(' href="http://planet.intertwingly.net/opensearchdescription.xml"')>=0)
        self.assertTrue(output.find('</script>')>=0)
