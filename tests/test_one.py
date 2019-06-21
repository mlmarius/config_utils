import os

import pytest

from config_utils import Config, EnvConfigReader, IniConfigReader, ConfigOption


def test_one():
    os.environ['OPTION2'] = '33'
    os.environ['OPTION3'] = 'spam'

    config1 = Config(
        options=[
            # Option with a default value. Found nowhere else
            ConfigOption('option1', 1),

            # Option with a specified value, overriden in environment.
            # Should return specified balue
            ConfigOption('option2', value=2, processor=int),

            # this one has a default value and an environment value
            # it should return the environment value
            ConfigOption('option3', 3)
        ],
        readers=[
            EnvConfigReader()
        ]
    )

    assert config1['option1'] == 1, 'You only had 1 job: return the default value of the option'
    assert config1['option2'] == 2, 'This item had a hardcoded value. Where is it?'
    assert config1['option3'] == 'spam', 'We should have received the environment value'

    config2 = Config(
        options=[
            # we are overwriting a config option from the previous config
            ConfigOption('option3', value='cat'),
            ConfigOption('option4', 4)
        ],
        readers=[
            IniConfigReader('tests/config.ini', sections=['bitbucket.org', 'topsecret.server.com'])
        ]
    )

    # we are merging 2 configs
    # if an option is defined in both
    # the config2 will overwrite config1's option
    config3 = config1 + config2

    assert config2['option3'] == 'cat', 'This option should have been overridden after the merge'
    assert config3['option4'] == 4

    # should raise value error because we tried to access an option
    # that is not defined in the config
    with pytest.raises(ValueError):
        assert config3['User'] == 'hg'

    # make new config defining the User option
    config4 = config3 + Config([
        ConfigOption('User'),

        # test if configparser picks up stuff in the DEFAULT
        # config section
        ConfigOption('ForwardX11'),

        # define an option that is in the second section
        # from our scanned sections list
        ConfigOption('Port'),

        ConfigOption('Undefined')
    ])

    assert config4['User'] == 'hg'

    # Carefull! Even if you define searching in multiple sections,
    # once a value is not found in the first section, then it will
    # be searched in the DEFAULT section
    assert config4['ForwardX11'] == 'yes'

    # This item is found in our second searched list.
    # It will only be returned if the first section does not have it
    # AND if it is not defined in the DEFAULT section
    assert config4['Port'] == '50022'

    # We raise ValueError if the option is defined
    # but we can't find its value
    with pytest.raises(ValueError):
        assert config4['Undefined']


def test_ini_reader():
    reader = IniConfigReader('tests/config.ini', sections=['bitbucket.org', 'topsecret.server.com'])
    assert reader._config.sections() == ['bitbucket.org', 'topsecret.server.com']
