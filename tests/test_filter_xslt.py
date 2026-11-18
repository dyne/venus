#!/usr/bin/env python

import shutil
import unittest, xml.dom.minidom
from planet import shell, config

try:
    import libxslt
    LIBXSLT_AVAILABLE = True
except ImportError:
    LIBXSLT_AVAILABLE = shutil.which("xsltproc") is not None

@unittest.skipUnless(
    LIBXSLT_AVAILABLE,
    "libxslt is not available => can't test xslt filters",
)
class XsltFilterTests(unittest.TestCase):

    def test_xslt_filter(self):
        config.load('tests/data/filter/translate.ini')
        testfile = 'tests/data/filter/category-one.xml'

        input = open(testfile).read()
        output = shell.run(config.filters()[0], input, mode="filter")
        dom = xml.dom.minidom.parseString(output)
        catterm = dom.getElementsByTagName('category')[0].getAttribute('term')
        self.assertEqual('OnE', catterm)

    def test_addsearch_filter(self):
        testfile = 'tests/data/filter/index.html'
        filter = 'addsearch.xslt'
        output = shell.run(filter, open(testfile).read(), mode="filter")
        self.assertTrue(output.find('<h2>Search</h2>')>=0)
        self.assertTrue(output.find('<form><input name="q"/></form>')>=0)
        self.assertTrue(output.find(' href="http://planet.intertwingly.net/opensearchdescription.xml"')>=0)
        self.assertTrue(output.find('</script>')>=0)
