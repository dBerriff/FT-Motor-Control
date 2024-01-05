# config.py
""" write/read parameters from a JSON file """

import json
import os


class ConfigFile:
    """ write and read json config files """
    def __init__(self, filename, default):
        self.filename = filename
        self.default = default

    def write_cf(self, data):
        """ write dict as json config file """
        with open(self.filename, 'w') as f:
            json.dump(data, f)

    def read_cf(self):
        """ return config data json dict from file
            - calling code checks is_config() """
        if self.is_file(self.filename):
            with open(self.filename, 'r') as f:
                data = json.load(f)
        else:
            print('Write default config file')
            data = self.default
            self.write_cf(data)
        return data

    @staticmethod
    def is_file(f):
        """ check if config file exists """
        return f in os.listdir()

