# -*- coding: utf-8 -*-

import json

with open('dataMole/config/dataviews.json', 'r') as config:
    d = json.load(config)
    __config__ = d['config']
    __classes__ = d['classes']
