# config.py
""" write/read parameters from a JSON file """

import json
import os


def write_cf(filename, data):
    """ write dict as json config file """
    with open(filename, 'w') as f:
        json.dump(data, f)


def read_cf(filename, default):
    """ return json file as dict or write default """
    if filename in os.listdir():
        with open(filename, 'r') as f:
            data = json.load(f)
    else:
        print(f'Write default values to: {filename}')
        data = default
        write_cf(filename, data)
    return data
