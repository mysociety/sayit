name_fixes = {
}

def fix_name(name):
    name = name.upper()
    return name_fixes.get(name, name)
