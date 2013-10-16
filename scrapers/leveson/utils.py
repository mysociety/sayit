import re

def prettify(s):
    s = s.title()
    s = s.replace(' Of ', ' of ').replace('Dac ', 'DAC ') \
         .replace('Qc', 'QC').replace('Ds ', 'DS ')
    # Deal with the McNames
    s = re.sub('Mc[a-z]', lambda mo: mo.group(0)[:-1] + mo.group(0)[-1].upper(), s)
    s = s.replace('Maclennan', 'MacLennan')
    # Remove middle names
    s = re.sub('^(DAC|DS|Dr|Miss|Mrs|Mr|Ms|Baroness|Lord|Professor|Sir) (\S+ )(?:\S+ )+?(\S+)((?: QC)?)$', r'\1 \2\3\4', s)
    if s != 'David Allen Green':
        s = re.sub('^(?!DAC|DS|Dr|Miss|Mrs|Mr|Ms|Baroness|Lord|Professor|Sir)(\S+) \S+ (\S+)', r'\1 \2', s)
    return s
