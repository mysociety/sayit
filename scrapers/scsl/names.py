name_fixes = {
    'THE ACCUSED': 'CHARLES GHANKAY TAYLOR',
}

def fix_name(name):
    name = name.upper()
    return name_fixes.get(name, name)
