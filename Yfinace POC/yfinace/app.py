from flask import Flask, render_template, request,jsonify
import yfinance as yf
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
from dotenv import load_dotenv,dotenv_values
import json
import os
from dash import Dash, dcc, html, Input, Output

app = Flask(__name__)

load_dotenv()
# STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA','TCS.NS','NSEBANK']
tickers = os.getenv("TICKERS")
STOCK_SYMBOLS = tickers.split(",")


@app.route('/', methods=['GET', 'POST'])
def index():
    selected_stock = request.form.get('stock') or STOCK_SYMBOLS[0]
    chart_style = request.form.get('chart_style') or 'line'
    interval = request.form.get('interval') or '1m'
    chart_json = None

    if request.method == 'POST':
        try:
            chart_json = generate_chart(selected_stock, chart_style, interval)
        except Exception as e:
            chart_json = json.dumps({'error': str(e)})

    return render_template('index.html', 
                           stocks=STOCK_SYMBOLS, 
                           selected_stock=selected_stock, 
                           selected_chart_style=chart_style, 
                           selected_interval=interval, 
                           chart_json=chart_json)

@app.route('/update_chart', methods=['POST'])
def update_chart():
    data = request.json
    stock = data['stock']
    style = data['chart_style']
    interval = data['interval']

    try:
        chart_json = generate_chart(stock, style, interval, update=True)
        return jsonify(chart_json)
    except Exception as e:
        return jsonify({'error': str(e)})

def generate_chart(stock, style, interval, update=False):
    data = yf.download(stock, period='1d', interval=interval)
    if data.empty:
        raise ValueError("No data found for the selected stock and interval")

    data.reset_index(inplace=True)
    if 'Datetime' in data.columns:
        data['Datetime'] = data['Datetime'].dt.tz_localize(None)

    fig = go.Figure()

    if style == 'candlestick':
        fig.add_trace(go.Candlestick(x=data['Datetime'],
                                     open=data['Open'],
                                     high=data['High'],
                                     low=data['Low'],
                                     close=data['Close'],
                                     name='Candlestick'))
    elif style == 'bar':
        fig.add_trace(go.Ohlc(x=data['Datetime'],
                              open=data['Open'],
                              high=data['High'],
                              low=data['Low'],
                              close=data['Close'],
                              name='Bar'))
    elif style == 'line':
        fig.add_trace(go.Scatter(x=data['Datetime'], y=data['Close'], mode='lines', name='Line'))

    fig.update_layout(title=f'{stock} Stock Prices', xaxis_title='Date', yaxis_title='Price')

    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)

    if update:
        return json.loads(graph_json)  
    return graph_json


# go to /dash route to open plotlydash dashboard

dash_app = Dash(__name__, server=app, url_base_pathname='/dash/')

load_dotenv()
# STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA','TCS.NS','NSEBANK']
tickers = os.getenv("TICKERS")
STOCK_SYMBOLS = tickers.split(",")
INTERVALS = ['1m', '2m', '5m', '15m', '30m', '1h', '1d']

dash_app.layout = html.Div([
    html.H1('Stock Price Dashboard', style={'text-align': 'center', 'color': '#333333'}),
    
    html.Div([
        html.Div([
            html.Label('Select stock:', style={'font-weight': 'bold'}),
            dcc.Dropdown(
                id='stock-dropdown',
                options=[{'label': stock, 'value': stock} for stock in STOCK_SYMBOLS],
                value='AAPL'
            ),
        ], style={'width': '25%', 'display': 'inline-block', 'margin-right': '10px'}),
        
        html.Div([
            html.Label('Select interval:', style={'font-weight': 'bold'}),
            dcc.Dropdown(
                id='interval-dropdown',
                options=[{'label': interval, 'value': interval} for interval in INTERVALS],
                value='1m'
            ),
        ], style={'width': '25%', 'display': 'inline-block', 'margin-right': '10px'}),

        html.Div([
        html.Label('Select chart style:', style={'font-weight': 'bold'}),
        dcc.Dropdown(
            id='chart-style-dropdown',
            options=[
                {'label': 'Candlestick', 'value': 'candlestick'},
                {'label': 'Bar', 'value': 'bar'},
                {'label': 'Line', 'value': 'line'}
            ],
            value='candlestick'
        ),
    ], style={'width': '25%', 'display': 'inline-block'}),

    ], style={'margin-bottom': '20px','text-align': 'center'}),
    
   
    dcc.Graph(id='stock-chart', style={'height': '550px','width': '100%'}),
    
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # in milliseconds
        n_intervals=0
    )
    
], style={'max-width': '1500px', 'margin': 'auto', 'font-family': 'Arial, sans-serif'})

@dash_app.callback(
    Output('stock-chart', 'figure'),
    [Input('stock-dropdown', 'value'), 
     Input('interval-dropdown', 'value'),
     Input('chart-style-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_chart(selected_stock, interval, chart_style, n_intervals):
    data = yf.download(selected_stock, period='1d', interval=interval)
    data.reset_index(inplace=True)
    data['Datetime'] = data['Datetime'].dt.tz_localize(None)

    fig = go.Figure()

    if chart_style == 'candlestick':
        fig.add_trace(go.Candlestick(x=data['Datetime'],
                                     open=data['Open'],
                                     high=data['High'],
                                     low=data['Low'],
                                     close=data['Close'],
                                     name='Candlestick'))
    elif chart_style == 'bar':
        fig.add_trace(go.Ohlc(x=data['Datetime'],
                               open=data['Open'],
                               high=data['High'],
                               low=data['Low'],
                               close=data['Close'],
                               name='Bar'))
    elif chart_style == 'line':
        fig.add_trace(go.Scatter(x=data['Datetime'], y=data['Close'], mode='lines', name='Line'))

    fig.update_layout(title=f'{selected_stock} Stock Prices', xaxis_title='Date', yaxis_title='Price')

    return fig


# if __name__ == '__main__':
#     app.run_server(debug=True)


# if __name__ == '__main__':
#     app.run(debug=True)
