import json

with open('data_preprocessor/gui/panels/config.json', 'r') as config:
    d = json.load(config)
    __config__ = d['config']
    __modules__ = d['modules']
