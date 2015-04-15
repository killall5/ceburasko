_default_order_ = 'id'


def set_default_order(order_by):
    global _default_order_
    _default_order_ = order_by


def to_order_dict(order_by):
    res = {}
    for order in order_by.split(','):
        if not order:
            continue
        if order[0] == '-':
            key = order[1:]
            res[key] = {
                'dir': 'desc',
                'rev': key
            }
        else:
            key = order
            res[key] = {
                'dir': 'asc',
                'rev': '-' + order,
            }
    return res


def to_order_by(order_dict):
    order_by = []
    for key, order in order_dict.items():
        if order['dir'] == 'asc':
            order_by.append(key)
        else:
            order_by.append('-' + key)
    return ','.join(order_by)


def add_order(request):
    try:
        order_by = request.GET['order']
    except KeyError as e:
        order_by = _default_order_
    return {
        'order': to_order_dict(order_by),
    }