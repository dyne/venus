from configparser import ConfigParser

inheritable_options = [ 'online_accounts' ]

def load_accounts(config, section):
    accounts = {}
    if(config.has_option(section, 'online_accounts')):
        values = config.get(section, 'online_accounts')
        for account_map in values.split('\n'):
            try:
                homepage, map = account_map.split('|')
                accounts[homepage] = map
            except:
                pass

    return accounts

def load_model(rdf, base_uri):
    from urllib.parse import urlparse
    from xml.sax import SAXParseException

    from rdflib import Graph

    if isinstance(rdf, Graph):
        return rdf

    if hasattr(rdf, 'read'):
        rdf = rdf.read()

    model = Graph()

    # XXX: Redland RDF used to keep relative references alone whin a relative
    # base URI is given. This is to emulate that behaviour.
    public_id = base_uri if urlparse(base_uri).scheme else None
    try:
        model.parse(data=rdf, publicID=public_id, format='xml')
    except SAXParseException:
        # XXX: Redland RDF has kept the parse state before an error has
        # happened.
        pass

    return model

# input = foaf, output = ConfigParser
def foaf2config(rdf, config, subject=None, section=None):

    if not config or not config.sections():
        return

    # there should be only be 1 section
    if not section: section = config.sections().pop()

    try:
        from rdflib import Namespace, URIRef, Literal
    except:
        return

    # account mappings, none by default
    # form: accounts = {url to service homepage (as found in FOAF)}|{URI template}\n*
    # example: http://del.icio.us/|http://del.icio.us/rss/{foaf:accountName}
    accounts = load_accounts(config, section)

    depth = 0

    if(config.has_option(section, 'depth')):
        depth = config.getint(section, 'depth')

    model = load_model(rdf, section)

    dc   = Namespace('http://purl.org/dc/elements/1.1/')
    foaf = Namespace('http://xmlns.com/foaf/0.1/')
    rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
    rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    rss = Namespace('http://purl.org/rss/1.0/')

    for person, _, weblog in model.triples((subject, foaf.weblog, None)):
        # title is required (at the moment)
        title = model.value(person, foaf.name)
        if not title: title = model.value(weblog, dc.title)
        if not title: 
            continue

        # blog is optional
        feed = model.value(weblog, rdfs.seeAlso)
        if feed and rss.channel == model.value(feed, rdf.type):
            feed = str(feed)
            if not config.has_section(feed):
                config.add_section(feed)
                config.set(feed, 'name', str(title))

        # now look for OnlineAccounts for the same person
        if accounts.keys():
            for _, _, account in model.triples((person, foaf.holdsAccount, None)):
                rdfaccthome = model.value(account, foaf.accountServiceHomepage)
                rdfacctname = model.value(account, foaf.accountName)

                if not rdfaccthome or not rdfacctname: continue

                if not isinstance(rdfaccthome, URIRef) or str(rdfaccthome) not in accounts: continue

                if not isinstance(rdfacctname, Literal): continue

                rdfacctname = str(rdfacctname)
                rdfaccthome = str(rdfaccthome)

                # shorten feed title a bit
                try:
                    servicetitle = rdfaccthome.replace('http://','').split('/')[0]
                except:
                    servicetitle = rdfaccthome

                feed = accounts[rdfaccthome].replace("{foaf:accountName}", rdfacctname)
                if not config.has_section(feed):
                    config.add_section(feed)
                    config.set(feed, 'name', "%s (%s)" % (title, servicetitle))

        if depth > 0:

            # now the fun part, let's go after more friends
            for _, _, friend in model.triples((person, foaf.knows, None)):
                # let's be safe
                if isinstance(friend, Literal): continue
                
                seeAlso = model.value(friend, rdfs.seeAlso)

                # nothing to see
                if not isinstance(seeAlso, URIRef): continue

                seeAlso = str(seeAlso)

                if not config.has_section(seeAlso):
                    config.add_section(seeAlso)
                    copy_options(config, section, seeAlso, 
                            { 'content_type' : 'foaf', 
                              'depth' : str(depth - 1) })
                try:
                    from planet.config import downloadReadingList
                    downloadReadingList(seeAlso, config,
                        lambda data, subconfig : friend2config(model, friend, seeAlso, subconfig, data), 
                        False)
                except:
                    pass

    return

def copy_options(config, parent_section, child_section, overrides = {}):
    global inheritable_options
    for option in [x for x in config.options(parent_section) if x in inheritable_options]:
        if option not in overrides:
            config.set(child_section, option, config.get(parent_section, option))

    for option, value in overrides.items():
        config.set(child_section, option, value)


def friend2config(friend_model, friend, seeAlso, subconfig, data):

    try:
        from rdflib import Namespace, URIRef
    except:
        return

    dc   = Namespace('http://purl.org/dc/elements/1.1/')
    foaf = Namespace('http://xmlns.com/foaf/0.1/')
    rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')

    # FOAF InverseFunctionalProperties
    ifps = [foaf.mbox, foaf.mbox_sha1sum, foaf.jabberID, foaf.aimChatID, 
        foaf.icqChatID, foaf.yahooChatID, foaf.msnChatID, foaf.homepage, foaf.weblog]

    model = load_model(data, seeAlso)

    for samefriend, _, _ in model.triples((None, rdf.type, foaf.Person)):
        # maybe they have the same uri
        if isinstance(friend, URIRef) and isinstance(samefriend, URIRef) and friend == samefriend:
            foaf2config(model, subconfig, samefriend)
            return

        for ifp in ifps:
            prop = model.value(samefriend, ifp)
            if prop and prop == friend_model.value(friend, ifp):
                foaf2config(model, subconfig, samefriend)
                return

if __name__ == "__main__":
    import sys, urllib.request, urllib.parse, urllib.error
    config = ConfigParser(interpolation=None)

    for uri in sys.argv[1:]:
        config.add_section(uri)
        foaf2config(urllib.request.urlopen(uri), config, section=uri)
        config.remove_section(uri)

    config.write(sys.stdout)
