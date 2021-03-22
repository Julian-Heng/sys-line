#!/usr/bin/env python3

from abc import ABC, abstractmethod
from logging import getLogger, DEBUG
from functools import lru_cache

from sys_line.tools.storage import Storage
from sys_line.tools.utils import percent, round_trim


LOG = getLogger(__name__)


class AbstractPlugin(ABC):

    def __init__(self, domain_name, default_options):
        super(AbstractPlugin, self).__init__()

        self.domain_name = domain_name
        self.default_options = default_options

    @property
    @lru_cache(maxsize=1)
    def _option_types(self):
        return namespace_types_as_dict(self.default_options)

    @property
    @lru_cache(maxsize=1)
    def _valid_info(self):
        def check(i):
            reserved = ["query", "all_info"]
            return (
                not i.startswith("_")
                and i not in reserved
                and callable(getattr(self, i))
            )

        info = list(filter(check, dir(self)))
        LOG.debug("valid info for '%s': %s", self.domain_name, info)
        return info

    def query(self, info, options_string):
        LOG.debug("querying domain '%s' for info '%s'", self.domain_name, info)
        LOG.debug("options string: %s", options_string)

        if info not in self._valid_info:
            msg = f"info name '{info}' is not in domain"
            raise RuntimeError(msg)

        if options_string is None:
            LOG.debug("options string is empty, using default options")
            options = self.default_options
        else:
            LOG.debug("parsing options string '%s'", options_string)
            options = self._parse_options(info, options_string)

        if LOG.isEnabledFor(DEBUG):
            msg = (
                f"begin querying domain '{self.domain_name}' for info '{info}'"
            )

            LOG.debug("=" * len(msg))
            LOG.debug(msg)
            LOG.debug("=" * len(msg))

        val = self._query(info, options)

        if LOG.isEnabledFor(DEBUG):
            msg = f"query result for '{self.domain_name}.{info}': '{val}'"
            LOG.debug("=" * len(msg))
            LOG.debug(msg)
            LOG.debug("=" * len(msg))

        return val

    def _query(self, info, options):
        return getattr(self, info)(options)

    def _parse_options(self, info, option_string):
        options = deepcopy(self.default_options)
        option_types = self._option_types
        for o in filter(len, map(trim_string, option_string.split(","))):
            k, v = (o.split("=", 1) + [None, None])[:2]

            LOG.debug("option_key=%s, option_value=%s", k, v)

            try:
                LOG.debug("getting type for option '%s'", k)
                option_type = reduce(dict.__getitem__, [info, k], option_types)
                LOG.debug("type for option '%s' is '%s'", k,
                          option_type.__name__)
            except (KeyError, TypeError):
                LOG.debug(
                    "option '%s' does not exist, passing it to handler...",
                    k
                )

                try:
                    if v is None:
                        self._handle_missing_option_value(options, info, o)
                        LOG.debug("option successfully handled")
                        continue
                except NotImplementedError:
                    pass

                msg = f"no such option in domain: {o}"
                raise RuntimeError(msg)

            if v is None and option_type is bool:
                v = True

            if k == "prefix" and v not in Storage.PREFIXES:
                msg = f"invalid value for prefix: {v}"
                raise RuntimeError(msg)

            try:
                setattr(getattr(options, info), k, option_type(v))
            except ValueError:
                msg = (
                    f"invalid type for option '{k}': "
                    f"expecting {option_type.__name__}, "
                    f"got {type(v).__name__}"
                )
                raise RuntimeError(msg)

        return options

    def _handle_missing_option_value(self, options, info, option_name):
        raise NotImplementedError()

    def all_info(self):
        for i in self._valid_info:
            yield i, self.query(i, None)

    @staticmethod
    def _post_import_hook(plugin):
        return plugin


class AbstractMultipleValuesPlugin(AbstractPlugin):

    def _query(self, info, options):
        val = super(AbstractMultipleValuesPlugin, self)._query(info, options)
        if not isinstance(val, dict):
            return None

        if hasattr(options, "index"):
            key = options.index
        else:
            key = next(iter(val.keys()), None)

        return val.get(key, None)

    def _handle_missing_option_value(self, options, info, option_name):
        setattr(options, "index", option_name)


class AbstractStoragePlugin(AbstractPlugin):

    @abstractmethod
    def _used(self):
        pass

    def used(self, options=None):
        if options is None:
            options = self.default_options

        value, prefix = self._used()
        if value is None or prefix is None:
            used = Storage(value=0, prefix="B", rounding="0")
        else:
            used = Storage(value=value, prefix=prefix,
                           rounding=options.used.round)
            used.prefix = options.used.prefix

        return used

    @abstractmethod
    def _total(self):
        pass

    def total(self, options=None):
        if options is None:
            options = self.default_options

        value, prefix = self._total()

        if value is None or prefix is None:
            total = Storage(value=0, prefix="B", rounding="0")
        else:
            total = Storage(value=value, prefix=prefix,
                            rounding=options.total.round)
            total.prefix = options.total.prefix

        return total

    def percent(self, options=None):
        if options is None:
            options = self.default_options

        used = self.used(options)
        total = self.total(options)
        perc = percent(used.bytes, total.bytes)
        if perc is None:
            perc = str(0.0)
        else:
            perc = round_trim(perc, options.percent.round)

        return perc
