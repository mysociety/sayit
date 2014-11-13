digits = "0123456789abcdefghjkmnpqrstvwxyz"


class MistypedIDException(Exception):
    pass


def int_to_base32(i):
    """Converts an integer to a base32 string"""
    enc = ''
    while i >= 32:
        i, mod = divmod(i, 32)
        enc = digits[mod] + enc
    enc = digits[i] + enc
    return enc


def base32_to_int(s):
    """Convert a base 32 string to an integer"""
    mistyped = False
    if s.find('o') > -1 or s.find('i') > -1 or s.find('l') > -1:
        s = s.replace('o', '0').replace('i', '1').replace('l', '1')
        mistyped = True
    decoded = 0
    multi = 1
    while len(s) > 0:
        decoded += multi * digits.index(s[-1:])
        multi = multi * 32
        s = s[:-1]
    if mistyped:
        raise MistypedIDException(decoded)
    return decoded
