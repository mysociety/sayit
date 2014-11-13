from __future__ import division


def rel_calc(n):
    """Calculate the colour-specific bit, given a colour hex-string."""
    n = int(n, 16) / 255
    if n <= 0.03928:
        n = n / 12.92
    else:
        n = ((n + 0.055) / 1.055) ** 2.4
    return n


def relative_luminance(h):
    """Calculate the relative luminance of a colour, given in rrggbb hex."""
    r = rel_calc(h[0:2])
    g = rel_calc(h[2:4])
    b = rel_calc(h[4:6])
    l = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return l


def contrast_ratio(l1, l2):
    """Given two relative luminances, calculate their contrast ratio."""
    return (l1 + 0.05) / (l2 + 0.05)


# Test contrast against white (L1 = 1)
# Using http://www.w3.org/TR/WCAG20/#relativeluminancedef
# l = relative_luminance(hex_colour)
# cr = contrast_ratio(1, l)
# if cr < 1.02: # Only care about the palest of pale
#     return 'cccccc'
# return hex_colour
