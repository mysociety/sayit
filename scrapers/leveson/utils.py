import re

def prettify(s):
    s = s.title()
    s = s.replace('Dac', 'DAC').replace('Qc', 'QC')
    # Deal with the McNames
    s = re.sub('Mc[a-z]', lambda mo: mo.group(0)[:-1] + mo.group(0)[-1].upper(), s)
    return s
