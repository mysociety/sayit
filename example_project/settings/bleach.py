BLEACH_ALLOWED_TAGS = [
    'a', 'abbr', 'b', 'i', 'u', 'span', 'sub', 'sup', 'br',
    'p',
    'ol', 'ul', 'li',
    'table', 'caption', 'tr', 'th', 'td',
]

BLEACH_ALLOWED_ATTRIBUTES = {
    '*': ['id', 'title'],  # class, style
    'a': ['href'],
    'li': ['value'],
}
