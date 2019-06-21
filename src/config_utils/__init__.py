from __future__ import annotations

import os
from typing import List, Callable, Dict, Union


class ConfigOption:

    def __init__(self, name: str, default=None, value=None, processor: Callable = None, env_prefix: str = None,
                 description: str = None):
        self.name = name
        self._processor = processor or (lambda x: x)
        self._default = default
        self._value = value
        self.env_prefix = env_prefix
        self.description = description

    @property
    def env_name(self):
        if self.env_prefix:
            return self.env_prefix.upper() + self.name.upper()
        return self.name.upper()

    def __str__(self):
        return f"{self.name} - {self.description}"

    @property
    def value(self):
        if self._value is not None:
            return self._processor(self._value)
        if self.env_name is not None:
            try:
                return self._processor(os.environ[self.env_name])
            except KeyError:
                if self._default is not None:
                    return self._processor(self._default)
        raise ValueError(f"Could not get value of {self.name}")


class Config:

    def __init__(self, options: List[ConfigOption] = None, env_prefix=None):
        self.env_prefix = env_prefix or ''
        self.options = {}
        if options is not None:
            for option in options:
                # add our prefix to the options that do not have an option prefix
                if option.env_prefix is None \
                        and option.env_prefix is not False \
                        and env_prefix is not None:
                    option.env_prefix = env_prefix

                self.options[option.name] = option

    def __contains__(self, item):
        return item in self.options

    def __add__(self, other: Config):
        return Config({**self.options, **other.options}.values())

    def __getitem__(self, item):
        if item not in self:
            raise ValueError(f"Option {item} is not configured")
        return self.options.get(item).value

    def cache(self) -> Dict[str, Union[str, bool, int, float]]:
        output = {}
        for option in self.options.values():
            output[option.name] = option.value
        return output
