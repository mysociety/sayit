def prettify(s):
    s = s.title()
    s = s.replace('Dct-', 'DCT-').replace('Tfi-', 'TF1-').replace('Tf1-', 'TF1-')
    return s
