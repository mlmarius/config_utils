import pytest

from config_utils import Config, ConfigOption


def test_simple():
    config = Config([
        ConfigOption('OPTION1', 2),
        ConfigOption('OPTION2', 15),
        ConfigOption('OPTION3'),
    ])
    assert config['OPTION1'] is 2
    assert config.options['OPTION1'].env_prefix == None
    assert config.options['OPTION1'].env_name == 'OPTION1'

    assert config['OPTION2'] == 15

    # should raise an exception when trying to access options that
    # have no value, no defaults and not env variables defining them
    with pytest.raises(ValueError):
        config['OPTION3']

    config = Config([
        ConfigOption('OPTION1', 2),
        ConfigOption('OPTION2', 15),
    ])

    assert config.cache() == {'OPTION1': 2, 'OPTION2': 15}


def test_with_prefix():
    config1 = Config([
        ConfigOption('OPTION1', 2),
        ConfigOption('OPTION2', 15),
    ], env_prefix='APP_')

    assert config1.env_prefix == 'APP_'
    assert config1.options['OPTION1'].env_prefix == 'APP_'
    assert config1.options['OPTION1'].env_name == 'APP_OPTION1'

    config2 = Config([
        ConfigOption('OPTION2', 20),
        ConfigOption('OPTION3', 30),
    ], env_prefix='APP1_')

    config_total = config1 + config2

    assert config_total.cache() == {'OPTION1': 2, 'OPTION2': 20, 'OPTION3': 30}
