import re

name_fixes = {
    # The boss man
    'Court': 'Lord Justice Leveson',
    'The Chairman': 'Lord Justice Leveson',
    'The Judge': 'Lord Justice Leveson',
    'Lord Leveson': 'Lord Justice Leveson',
    'The Technician': 'Technician',
    # Hard to spell
    'Mr Patry Hoskins': 'Ms Patry Hoskins',
    'Mrs Patry Hoskins': 'Ms Patry Hoskins',
    'Ms Patry-Hoskins': 'Ms Patry Hoskins',
    'Ms Decoulous': 'Ms Decoulos',
    'Ms Michaolos': 'Ms Michalos',
    'Mer Sherborne': 'Mr Sherborne',
    'Lord Hunt of Wirrell': 'Lord Hunt of Wirral',
    # Different name used in different places
    'Mr Davies': 'Mr Rhodri Davies',
    'David James Fletcher Lord Hunt of Wirral': 'Lord Hunt of Wirral',
    'Ms Young': 'Ms Elizabeth Young',
    'Professor Tasioulas': 'Professor John Tasioulas',
    'Ms Pickles': 'Ms Anne Pickles',
    'Ms Nixon': 'Ms Rosie Nixon',
    'Mr McLellan': 'Mr John McLellan',
    'Mr Lyons': 'Mr Darryn Lyons',
    'Mrs Llewellyn': 'Mrs Catherine Llewellyn',
    'Dr Moore': 'Dr Martin Moore',
    'Dr Unger': 'Dr Steven Unger',
    'Mr Adam Smith': 'Mr Adam Smith',
    'Mr Cunningham': 'Mr Mike Cunningham',
    'Ms Stanistreet': 'Ms Michelle Stanistreet',
    'Mr Rusbridger': 'Mr Alan Rusbridger',
    'Mr Russell': 'Mr Jonathan Russell',
    'Mr Julian Pike': 'Mr Julian Pike',
    'Ms Bird': 'Ms Joanne Bird',
    'Professor Barnett': 'Professor Steven Barnett',
    'Ms Susan Akers': 'DAC Sue Akers',
    'Dr John Vincent Cable': 'Dr Vincent Cable',
    'Lord Guy Vaughan Black': 'Lord Black of Brentwood',
    'Hjk': 'HJK',
}

def title_with_corrections(s):
    s = s.title()
    s = s.replace(' Of ', ' of ').replace(' And ', ' and ').replace('Dac ', 'DAC ') \
         .replace('Qc', 'QC').replace('Ds ', 'DS ')
    # Deal with the McNames
    s = re.sub('Mc[a-z]', lambda mo: mo.group(0)[:-1] + mo.group(0)[-1].upper(), s)
    s = s.replace('Maclennan', 'MacLennan')
    return s

def fix_name(name):
    name = title_with_corrections(name)
    name = name_fixes.get(name, name)
    # More than one name given, or Lord name that doesn't include full name
    if ' and ' in name or (' of ' in name and ',' not in name):
        return name
    # Remove middle names
    if 'David Allen Green' not in name:
        name = re.sub('^(DAC|DS|Dr|Miss|Mrs|Mr|Ms|Baroness|Lord|Professor|Sir) (\S+ )(?:\S+ )+?(\S+)((?: QC)?)$', r'\1 \2\3\4', name)
        name = re.sub('^(?!DAC|DS|Dr|Miss|Mrs|Mr|Ms|Baroness|Lord|Professor|Sir)(\S+) \S+ (\S+)', r'\1 \2', name)
    return name
