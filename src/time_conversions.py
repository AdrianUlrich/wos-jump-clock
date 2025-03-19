from math import ceil


def to_minutes(duration: str):
    duration = duration.replace('D', 'd')
    duration = duration.replace('H', 'h')
    duration = duration.replace('M', 'm')
    duration = duration.replace('S', 's')
    days, _, duration = duration.strip().rpartition('d')
    hours, _, duration = duration.strip().rpartition('h')
    minutes, _, duration = duration.strip().rpartition('m')
    seconds, _, _ = duration.strip().rpartition('s')
    if seconds:  # can't be an int
        return float(days or '0') * 24 * 60 + float(hours or '0') * 60 + float(minutes or '0') + float(seconds) / 60
    return int(days or '0') * 24 * 60 + int(hours or '0') * 60 + int(minutes or '0')

def from_minutes(minutes: int):
    if isinstance(minutes, float):
        minutes = ceil(minutes)
    days, minutes = divmod(minutes, 24 * 60)
    hours, minutes = divmod(minutes, 60)
    parts = [f'{days}d' if days else '', f'{hours}h' if hours else '', f'{minutes}m' if minutes else '']
    return ' '.join(x for x in parts if x)

if __name__ == '__main__':
    print(f'{to_minutes('1d')=}')
    print(f'{to_minutes('1d 2h')=}')
    print(f'{to_minutes('1d 2h 3m')=}')
    print(f'{from_minutes(1563)=}')
    print(f'{from_minutes(60)=}')
    print(f'{from_minutes(1440)=}')
    
    