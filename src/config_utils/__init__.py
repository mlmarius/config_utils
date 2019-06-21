from __future__ import annotations

import configparser
import os
from abc import ABC, abstractmethod
from typing import List, Callable, Dict, Union, Tuple, Any, Set


class ConfigOption:

    def __init__(self, name: str, default=None, value=None, processor: Callable = None, section: str = None,
                 description: str = None):
        self.name = name
        self._processor = processor or (lambda x: x)
        self.default = default
        self.section = section
        self.value = value
        self.description = description

    def process(self, value):
        return self._processor(value)

    def __hash__(self):
        return hash((self.name, self.section))

    def __eq__(self, other: ConfigOption):
        return self.section == other.section and self.name == other.name

    def __str__(self):
        return self.name


class BaseConfig(ABC):

    def __init__(self):
        self.readers = []

    @abstractmethod
    def __getitem__(self, searched: Union[Tuple[str, str], ConfigOption]) -> Any:
        pass

    @abstractmethod
    def options(self) -> Set[ConfigOption]:
        pass


class Config(BaseConfig):
    def __init__(self, options: List[ConfigOption], readers: List[BaseConfig] = None):
        self._options: Set[ConfigOption] = set(options) or set()
        self.readers = readers or []

    @property
    def options(self) -> Set[ConfigOption]:
        output = set() ^ self._options
        for reader in self.readers:
            output ^= reader.options
        return output

    def __add__(self, other: BaseConfig):
        return Config(
            options=self.options ^ other.options,
            readers=self.readers + other.readers
        )
        # self.readers.append(other.readers)

    def get_option(self, name: str, section: str = None) -> ConfigOption:
        for option in self.options:
            if option.name == name and option.section == section:
                return option
        else:
            raise ValueError(f'Undefined option {name}')

    def __getitem__(self, item: Union[str, Tuple[str, str], ConfigOption]) -> Any:

        if not isinstance(item, ConfigOption):
            if isinstance(item, str):
                item = self.get_option(item, None)
            elif isinstance(item, tuple):
                name, section = item
                item = self.get_option(name, section)

        if item.value is not None:
            return item.value

        for reader in self.readers:
            try:
                return item.process(reader[item])
            except ConfigError:
                continue

        if item.default is not None:
            return item.process(item.default)

        raise ValueError(f'Undefined value {item.name}')

    def cache(self) -> Dict[str, Union[str, bool, int, float]]:
        # @todo return a result that can also include sections
        output = {}
        for option in self.options:
            output[option.name] = option.value
        return output


class ConfigError(Exception):
    pass


class BaseConfigReader(BaseConfig):
    @property
    def options(self) -> Set[ConfigOption]:
        return set()


class EnvConfigReader(BaseConfigReader):

    def __init__(self, prefix=None):
        super().__init__()
        self._prefix = prefix or ''

    def _env_name(self, name: str) -> str:
        return (self._prefix + name).upper()

    def __getitem__(self, searched: ConfigOption) -> Any:
        try:
            return os.environ[self._env_name(searched.name)]
        except KeyError:
            raise ConfigError()


class IniConfigReader(BaseConfigReader):
    def __init__(self, filepath: str, section: str = None, sections: List[str] = None):
        with open(filepath, 'rt') as f:
            self._config = configparser.ConfigParser()
            self._config.read_file(f)

        if sections is not None:
            self._sections = sections
        elif section is not None:
            self._sections = [section]
        else:
            raise Exception('Need to configure ONLY one of "section" or "sections"')

    def __getitem__(self, searched: ConfigOption):
        for section in self._sections:
            try:
                return self._config[section][searched.name]
            except KeyError:
                continue
        else:
            raise ConfigError()
