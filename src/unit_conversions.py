from math import ceil


def to_units(rss: str) -> int:
    try:
        # if already a number, return it
        return ceil(float(rss))
    except ValueError:
        pass
    if rss[-1] in ['k', 'K']:
        return ceil(float(rss[:-1]) * 1e3)
    elif rss[-1] in ['m', 'M']:
        return ceil(float(rss[:-1]) * 1e6)
    elif rss[-1] in ['b', 'B']:
        return ceil(float(rss[:-1]) * 1e9)
    else:
        raise ValueError(f'RSS value {rss} not understood')
