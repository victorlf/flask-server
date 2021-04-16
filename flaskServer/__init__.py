#!/usr/bin/env python

import sqlite3
import requests
import json
from sqlite3 import Error
from flask import Flask, request, render_template, send_file, make_response, jsonify
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
from datetime import datetime
#from flask import request


#DATABASE = '/var/www/flaskServer/flaskServer/database/measurements.db'
DATABASE = '/home/victor/Documents/CBPF/obras_raras/flaskServer/flaskServer/database/measurements.db'
#DATABASE = '/home/victor/Documents/CBPF/obras_raras/flaskServer/flaskServer/database/measurementsFromServer.db'

app = Flask(__name__)


def makeCon():
    conn=sqlite3.connect(DATABASE)
    curs=conn.cursor()

    return curs

# Retrieve data from database
def getData(sensor=1):
    curs = makeCon()
    #sql = f'SELECT * FROM temp_pres WHERE sensor={sensor} ORDER BY timestamp DESC LIMIT 1'
    sql = f'SELECT * FROM temp_pres_battery WHERE sensor={sensor} ORDER BY timestamp DESC LIMIT 1'
    for row in curs.execute(sql):
        #time = str(row[4])
        battery = row[4]
        time = str(row[5])
        temp = row[2]
        pres = row[3]
        sensor = row[1]
    curs.close()

    return time, battery, temp, pres, sensor


def getHistData (numSamples, sensor=1):
    curs = makeCon()
    #sql = f'SELECT * FROM temp_pres WHERE sensor={sensor} ORDER BY timestamp DESC LIMIT '
    sql = f'SELECT * FROM temp_pres_battery WHERE sensor={sensor} ORDER BY timestamp DESC LIMIT '
    sql = sql + str(numSamples)
    #curs.execute("SELECT * FROM temp_pres ORDER BY timestamp DESC LIMIT "+str(numSamples))
    curs.execute(sql)
    data = curs.fetchall()
    dates = []
    temps = []
    press = []
    for row in reversed(data):
        #dates.append(row[4])
        dates.append(row[5])
        temps.append(row[2])
        press.append(row[3])
    curs.close()

    return dates, temps, press


def maxRowsTable(sensor):
    curs = makeCon()
    #for row in curs.execute(f"select COUNT(temperature) from  temp_pres  WHERE sensor={sensor}"):
    for row in curs.execute(f"select COUNT(temperature) from  temp_pres_battery  WHERE sensor={sensor}"):
        maxNumberRows=row[0]
    curs.close()

    numSamples = maxNumberRows

    if (numSamples > 101):
        numSamples = 100

    return numSamples

# Get sample frequency in minutes
def freqSample():
    times, temps, pres = getHistData (numSamples=2)
    fmt = '%Y-%m-%d %H:%M:%S'
    tstamp0 = datetime.strptime(times[0], fmt)
    tstamp1 = datetime.strptime(times[1], fmt)
    freq = tstamp1-tstamp0
    freq = int(round(freq.total_seconds()))
    return (freq)

# Define and initialize global variables
global numSamples
numSamples = maxRowsTable(1)


global freqSamples
freqSamples = freqSample()
#freqSamples = 10

global rangeTime
rangeTime = 100

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    header['Access-Control-Allow-Methods'] = 'OPTIONS, HEAD, GET, POST, DELETE, PUT'
    return response

@app.route('/get_one_value_each/<sensor>')
def get_one_value_each(sensor):
    time, battery, temp, pres, sensor = getData(sensor)
    return jsonify({"temp": temp, "pres": pres, "battery": battery, "time": time})

@app.route('/get_array_values/temp/<sensor>')
def get_array_values_temp(sensor):
    #sensor = 2
    numSamples = maxRowsTable(sensor)
    times, temps, press = getHistData(numSamples=numSamples, sensor=sensor)
    ys = temps
    print(ys)
    xs = list(range(numSamples))
    print(xs)


    #return render_template('test.html', xs=xs, ys=ys)
    return jsonify({"temps": temps, "numSamples": xs})

@app.route('/get_array_values/pres/<sensor>')
def get_array_values_pres(sensor):
    #sensor = 2
    numSamples = maxRowsTable(sensor)
    times, temps, press = getHistData(numSamples=numSamples, sensor=sensor)
    ys = press
    print(ys)
    xs = list(range(numSamples))
    print(xs)


    #return render_template('test.html', xs=xs, ys=ys)
    return jsonify({"temps": press, "numSamples": xs})


@app.route('/monitor')
def index():	
	time, temp, pres, sensor = getData()
	templateData = {
		'time': time,
		'temp': temp,
		'pres': pres,
	}

	return render_template('monitor.html', templateData=templateData)


@app.route('/monitor2', methods=['GET'])
def index2():	
	time, temp, pres, sensor = getData()
	templateData = {
		'time': time,
		'temp': temp,
		'pres': pres,
        #'numSamples' : numSamples
        'freq' : freqSamples,
        'rangeTime'	: rangeTime,
	}

	return render_template('monitor2.html', templateData=templateData)


@app.route('/monitor2', methods=['POST'])
def my_form_post():
    global numSamples
    global freqSamples
    global rangeTime
    #numSamples = int (request.form['numSamples'])
    rangeTime = int (request.form['rangeTime'])
    if (rangeTime < freqSamples):
        rangeTime = freqSamples + 1
    numSamples = rangeTime//freqSamples
    numMaxSamples = maxRowsTable()
    if (numSamples > numMaxSamples):
        numSamples = (numMaxSamples-1)
    time, temp, pres = getData()
    templateData = {
        'time'	: time,
        'temp'	: temp,
        'pres'	: pres,
        'freq' : freqSamples,
        'rangeTime'	: rangeTime
	}

    return render_template('monitor2.html', templateData=templateData)

@app.route('/monitor3')
def index3():	
	time, temp, pres, sensor = getData()
	templateData1 = {
		'time': time,
		'temp': temp,
		'pres': pres,
        #'numSamples' : numSamples
        'freq' : freqSamples,
        'rangeTime'	: rangeTime,
        'sensor' : sensor
	}

	time, temp, pres, sensor = getData(2)
	templateData2 = {
		'time': time,
		'temp': temp,
		'pres': pres,
        #'numSamples' : numSamples
        'freq' : freqSamples,
        'rangeTime'	: rangeTime,
        'sensor' : sensor
	}
	
	return render_template('monitor3.html', templateData1=templateData1, templateData2=templateData2)


@app.route('/plot/temp/<sensor>')
def plot_temp(sensor):
	numSamples = maxRowsTable(sensor)
	times, temps, press = getHistData(numSamples=numSamples, sensor=sensor)
	ys = temps
	fig = Figure()
	axis = fig.add_subplot(1, 1, 1)
	axis.set_title("Temperature [°C]")
	axis.set_xlabel("Samples")
	axis.grid(True)
	xs = range(numSamples)
	axis.plot(xs, ys)
	canvas = FigureCanvas(fig)
	output = io.BytesIO()
	canvas.print_png(output)
	response = make_response(output.getvalue())
	response.mimetype = 'image/png'

	return response


@app.route('/plot/pres/<sensor>')
def plot_pres(sensor):
	numSamples = maxRowsTable(sensor)
	times, temps, press = getHistData(numSamples=numSamples, sensor=sensor)
	ys = press
	fig = Figure()
	axis = fig.add_subplot(1, 1, 1)
	axis.set_title("Pressure [hPa]")
	axis.set_xlabel("Samples")
	axis.grid(True)
	xs = range(numSamples)
	axis.plot(xs, ys)
	canvas = FigureCanvas(fig)
	output = io.BytesIO()
	canvas.print_png(output)
	response = make_response(output.getvalue())
	response.mimetype = 'image/png'

	return response


@app.route('/postjson', methods = ['POST'])
def postJsonHandler():
    print (request.is_json)
    content = request.get_json()
    print (content)
    #print('JSON posted')

    try:
        sensor = content['sensor']
        temp = content['temperature']
        pres = content['pressure']
        volt = content['voltage']
        #print(float(volt))
        battery = int((float(volt) / 5) * 100)
        #battery = 90

        print(sensor)

        #con = sqlite3.connect('database/temperature.db')
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            #cur.execute("INSERT INTO temp_pres (sensor, temperature, pressure, timestamp) Values (?, ?, ?, datetime('now', 'localtime'))", (sensor, temp, pres))
            cur.execute("INSERT INTO temp_pres_battery (sensor, temperature, pressure, battery, timestamp) Values (?, ?, ?, ?, datetime('now', 'localtime'))", (sensor, temp, pres, battery))

            con.commit()
            con.close()
        print("Record successfully added")
        return True
    except:
        #con.rollback()
        print("error in insert operation")
        return "error in insert operation"

    #print(200)



if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=8090)
    app.run(host='0.0.0.0', port=5000)
