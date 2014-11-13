# vim: set fileencoding=utf-8 :

import six

if six.PY2:
    from urllib import unquote as unquote_to_bytes
else:
    from urllib.parse import unquote_to_bytes


def url_to_unicode(s):
    # Python 2
    # >>> print(unquote('caf%c3%a9').decode('utf-8'))
    # 'café'
    # >>> print(unquote(u'caf%c3%a9').encode('raw_unicode_escape').decode('utf-8'))
    # 'café'
    #
    # Python 3
    # >>> print(unquote('caf%c3%a9'))
    # 'café'
    # >>> print(unquote_to_bytes(b'caf%c3%a9').decode('utf-8'))
    # 'café'
    #
    # So for consistent results, we need to encode() the incoming string
    # and call unquote (2) or unquote_to_bytes (3) before decode()
    s = s.encode('utf-8')
    s = unquote_to_bytes(s)
    return s.decode('utf-8')
