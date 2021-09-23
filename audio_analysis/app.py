#!/usr/bin/env python3
import flask
import subprocess
from flask_cors import CORS, cross_origin
from s2t import analyse

app = flask.Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

"""Analyze API"""
@app.route('/analyse', methods=['POST'])
@cross_origin()
def analyse_():      
	par = flask.request.json
	print(par)
	response, status_code = analyse(par)
	
	return response, status_code
	
if __name__ == "__main__":
	app.run(host="0.0.0.0", port=3500,debug=True)
