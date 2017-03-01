"""
Configuration
"""
_pycharm_edit_ = False

if _pycharm_edit_:
    from www import config_default
else:
    import config_default


__author__ = 'fjzhang'


class Dict(dict):
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


def merge(defaults, override):
    """
    合并默认配置和覆盖配置
    :param defaults: 默认配置
    :param override: 覆盖配置
    :return:
    """
    r = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(k, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = defaults[k]
    return r


def toDict(d):
    D = Dict()
    for k, v in d.items():
        D[k] = toDict(k) if isinstance(k, dict) else v
    return D


configs = config_default.configs
try:
    from www import config_override
    # import config_override

    configs = merge(configs, config_override.configs)
except ImportError:
    pass

configs = toDict(configs)
