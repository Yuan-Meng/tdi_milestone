### 1. Import libraries 

# Flask libraries 
from flask import Flask, render_template, request, redirect

# Data accessing 
from alpha_vantage.timeseries import TimeSeries
import pickle

# Data handling 
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
from datetime import datetime
from dateutil.parser import parse
import math

# Bokeh libraries 
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, show, output_file
from bokeh.embed import components, file_html

### 2. Get data

# Get stock data from Alpha Advantage
def get_monthly_closing(ticker):

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
    return ticker, prices

# Load ticker lookup table
with open("data/lookup.pkl", "rb") as file:
    lookup = pickle.load(file)  

# Get company name from ticker
def get_name(ticker):
    ticker = ticker.upper()
    company = lookup.loc[lookup["Ticker"] == ticker, "Name"].item()
    return company  

# Plot with Bokeh 
def create_figure(stock, prices):

    # Prepare data for plotting
    prices_cds = ColumnDataSource(prices)

    # Upper limit of y-axis
    max_close = (  
        math.floor(
            max(prices["monthly_close"].max(), prices["monthly_close_adjusted"].max())
        )
        + 100  # Leave some space above
    )

    # Company name
    company = get_name(stock.upper())  # Company name
    
    # Create an empty canvas
    fig = figure(
        title=f"Monthly Closing Prices of {stock.upper()} ({company})",
        plot_height=400,
        plot_width=700,
        x_axis_type="datetime",
        x_axis_label="Date",
        y_axis_label="Price (USD)",
        x_minor_ticks=2,
        y_range=(0, max_close),
    )

    # Add monthly closing prices
    fig.line(
        x="date",
        y="monthly_close",
        source=prices_cds,
        color="gray",
        line_width=1,
        legend_label="Unadjusted",
    )

    # Add adjusted monthly closing prices
    fig.line(
        x="date",
        y="monthly_close_adjusted",
        source=prices_cds,
        color="blue",
        line_width=1,
        legend_label="Adjusted",
    )

    # Put the legend in the upper left corner
    fig.legend.location = "top_left"

    return fig 

### Build Flask app 

# Initialize the Flask app
app = Flask(__name__, template_folder="templates")
app.vars={}

# Set up the main route
@app.route("/index", methods=['GET','POST'])    

def index():
    
    if request.method == 'GET':
        return render_template('Search.html')
        
    else:
        # request.method == 'POST'
        app.vars['symbol'] = request.form['ticker']

        stock, prices = get_monthly_closing(app.vars['symbol'])
        
        plot = create_figure(stock, prices)

        script, div = components(plot)  

        return render_template('Plot.html', script=script, div=div)
       
@app.route('/', methods=['GET','POST'])
def main():
    return redirect('/index')

if __name__== "__main__":

    app.run(port=33508, debug = True)