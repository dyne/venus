from configparser import ConfigParser
import csv

# input = csv, output = ConfigParser
def csv2config(input, config=None):

    if not hasattr(input, 'read'):
        input = csv.StringIO(input)

    if not config:
        config = ConfigParser(interpolation=None)

    reader = csv.DictReader(input)
    for row in reader:
        section = row[reader.fieldnames[0]]
        if not config.has_section(section):
            config.add_section(section)
        for name, value in row.items():
            if value and name != reader.fieldnames[0]:
                config.set(section, name, value) 

    return config

if __name__ == "__main__":
    # small main program which converts CSV into config.ini format
    import sys, urllib.request, urllib.parse, urllib.error
    config = ConfigParser(interpolation=None)
    for input in sys.argv[1:]:
        csv2config(urllib.request.urlopen(input), config)
    config.write(sys.stdout)
