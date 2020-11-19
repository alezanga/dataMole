# -*- coding: utf-8 -*-

import json
import os
from dataMole import rootdir

with open(os.path.join(rootdir, 'dataMole/config/dataviews.json'), 'r') as config:
    d = json.load(config)
    __config__ = d['config']
    __classes__ = d['classes']
