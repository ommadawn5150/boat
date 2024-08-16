import os
import json

def set_values(gl):
    '''
        put global variables to this function as gl
    '''
    current = os.path.abspath(os.path.dirname(__file__))
    dirname = os.path.abspath(os.path.join(current, os.pardir)) + '/'
    
    with open(current + '/config.json') as f:
        config = json.load(f)
    for key in config:
        if key == 'dir':
            for k in config[key]:
                gl[k] = dirname + config[key][k]
        else:
            for k in config[key]:
                gl[k] = config[key][k]
    return True