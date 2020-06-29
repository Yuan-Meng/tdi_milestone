### Import libraries 

# Flask libraries 
from flask import Flask, render_template,request,redirect

# Data accessing 
import requests
import io
from alpha_vantage.timeseries import TimeSeries

# Data handling 
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
from datetime import datetime
from dateutil.parser import parse

# Bokeh libraries 
from bokeh.io import curdoc
from bokeh.layouts import row, column, gridplot
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import PreText, Select
from bokeh.plotting import figure, show, output_file
from bokeh.embed import components,file_html

# Other libraries 
import time
import os
from os.path import dirname, join 

### Flask app 

# Initialize the Flask app
app = Flask(__name__)
app.vars={}

# Get stock data from Alpha Advantage

def get_monthly_closing(ticker):
    """Obtaining and cleaning monthly closing prices of a given stock"""

    # Credentials
    key = "KE59ELWQ1XLDO5ZR"
    ts = TimeSeries(key, output_format="pandas", indexing_type="integer")

    # Query by ticker
    data, meta_data = ts.get_monthly_adjusted(symbol=ticker.upper())

    # Only keep relevant columns
    prices = data[["index", "4. close", "5. adjusted close"]]

    # Rename columns
    prices.rename(
        columns={
            "index": "date",
            "4. close": "monthly_close",
            "5. adjusted close": "monthly_close_adjusted",
        },
        inplace=True,
    )

    # Convert dates from strings to datetime objects
    prices["date"] = prices["date"].apply(lambda x: parse(str(x)))

    # Return ticker and stock data
    return prices

def get_feature(ticker):
    mydata = get_monthly_closing(ticker)
    feature = mydata.columns[0:-1].values.tolist()
    return feature

# feature_names = mydata.columns[1:-1].values.tolist()
def create_figure(mydata, current_feature_name):
    ticker = np.array(mydata[current_feature_name])
    ticker_dates = np.array(mydata['date'])

    window_size = 30
    window = np.ones(window_size)/float(window_size)
    ticker_avg = np.convolve(ticker, window, 'same')

    p = figure(x_axis_type="datetime", title="%s Monthly Closing Prices" % current_feature_name)
    p.grid.grid_line_alpha = 0
    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = '%s Price' % current_feature_name
    p.ygrid.band_fill_color = "green"
    p.ygrid.band_fill_alpha = 0.1

    p.circle(ticker_dates, ticker, size=4, legend='%s' % current_feature_name,
              color='darkgrey', alpha=0.2)

    p.line(ticker_dates, ticker_avg, legend='avg', color='navy')
    p.legend.location = "top_left"
    return p


@app.route("/index", methods=['GET','POST'])    

def index():
    
    if request.method == 'GET':
        return render_template('Search.html')
        
    else:
        #request was a POST
        app.vars['symbol'] = request.form['ticker']
        mydata = get_monthly_closing(app.vars['symbol'])

        feature_names = get_feature(app.vars['symbol'])

        current_feature_name = request.args.get("feature_name")

        if current_feature_name == None:
            current_feature_name = "monthly_close"
        
        plot = create_figure(mydata, current_feature_name)

        script, div = components(plot)       
        return render_template('Plot.html', script=script, div=div)
       
@app.route('/', methods=['GET','POST'])
def main():
    return redirect('/index')

if __name__== "__main__":

    app.run(port=33508, debug = True)