#!venv/bin/python

import os, re, json

from flask import Flask, request
from flask_restful import Resource, Api
from json import dumps
from flask_jsonpify import jsonify
from flask import render_template
from boxes import *

app = Flask(__name__)
api = Api(app)

def get_logs(date, severity, box):
    
    DATESTAMP_RE = r'(\w+\s+\d+)'   
    TIMESTAMP_RE = r'(\d+:\d+:\d+)' 
    DEVICE_IP_RE = r'(\S+)'       
    ERROR_SEVERITY_RE = r'<local7.(\S+)>'
    ERROR_CODE_RE = r':\s+%(\S+):'                
    ERROR_MESSAGE_RE = r'(.*)'     
    COLUMN_DELIMITER_RE = r'\s+' 
    PADDING_RE = r'\s?(?:\d+\s+\w+\s+\d+\s+\d+:\d+:\d+\s+\w+)?'

    keys = ['datestamp', 'timestamp', 'error_severity', 'device', 'error_code', 'error_message']
    result_log = []
    datestamp = str(date)
    year = datestamp[0:4]
    month = datestamp[4:6]
    day = datestamp[-2:]
    filename = datestamp + '.log'
    ip_address_list = [ip for ip,name in boxes.iteritems() if name == box]
    ip_address = ip_address_list[0]
    workdir = '/var/log/cisco/' + year + '/' + month + '/' + ip_address + '/'
    filepath = workdir + filename

    SYSLOG_RE = (
        DATESTAMP_RE + COLUMN_DELIMITER_RE +
        TIMESTAMP_RE + COLUMN_DELIMITER_RE +
        ERROR_SEVERITY_RE + COLUMN_DELIMITER_RE +
        DEVICE_IP_RE + COLUMN_DELIMITER_RE + PADDING_RE +
        ERROR_CODE_RE + COLUMN_DELIMITER_RE +
        ERROR_MESSAGE_RE)

    if os.path.isfile(filepath):
	with open(filepath, mode = 'r') as syslog:
	    log_lines = syslog.readlines()
	    for line in reversed(log_lines):
		matched  = re.match(SYSLOG_RE, line)
		if not matched:
		    continue
		values = matched.groups()
		result = dict(zip(keys, values))
		result['device'] = boxes[result['device']]
		
		if severity == 'all':
		    result_log.append(result)
		elif result['error_severity'] == severity and result['device'] == box:
		    result_log.append(result)
		else:
		    pass
    return result_log
                        
class Syslog(Resource):
    def get(self):
        date = request.args.get('date') 
        severity = request.args.get('severity')
        box = request.args.get('box')
        log = {"data": get_logs(date, severity, box)}

        #return render_template('logs.html', logs = logs)
        return jsonify(log)

api.add_resource(Syslog, '/syslog') # Route_1

if __name__ == '__main__':
    app.run(host="217.73.28.16", port=5002)
