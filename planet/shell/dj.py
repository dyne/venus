import os.path
import urllib.parse
import datetime

from . import tmpl
from planet import config

def DjangoPlanetDate(value):
    return datetime.datetime(*value[:6])

# remap PlanetDate to be a datetime, so Django template authors can use 
# the "date" filter on these values
tmpl.PlanetDate = DjangoPlanetDate

def run(script, doc, output_file=None, options={}):
    """process a Django template file"""

    # this is needed to use the Django template system as standalone
    import django
    from django.conf import settings
    from django.template.backends.django import DjangoTemplates

    if not settings.configured:
        settings.configure()
        django.setup()

    backend = DjangoTemplates({
        'NAME': 'django',
        'DIRS': [os.path.dirname(script)],
        'APP_DIRS': False,
        'OPTIONS': {
            'autoescape': config.django_autoescape() == 'on',
            'debug': True,
        },
    })

    # set up the Django context by using the default htmltmpl 
    # datatype converters
    context = dict(tmpl.template_info(doc))
    context['Config'] = config.planet_options()
    t = backend.get_template(script)

    if output_file:
        reluri = os.path.splitext(os.path.basename(output_file))[0]
        context['url'] = urllib.parse.urljoin(config.link(),reluri)
        f = open(output_file, 'w')
        ss = t.render(context)
        if isinstance(ss,str): ss=ss.encode('utf-8')
        f.write(ss)
        f.close()
    else:
        # @@this is useful for testing purposes, but does it 
        # belong here?
        return t.render(context)
