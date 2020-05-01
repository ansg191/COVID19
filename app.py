from flask import Flask, render_template, jsonify, request
from datetime import datetime

from nnData import *
from data import *

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/world/model')
def model():
    country = request.args.get('country', 'United States', type=str)
    return render_template('model.html', country=country)


@app.route('/world/nn')
def nn():
    country = request.args.get('country', 'United States', type=str)
    date = (datetime.today() - datetime(2019, 12, 31)).days
    df = get_data(date)
    df = df[df[country] > 0][country]
    fit = get_prediction(df, country, date)
    return render_template('nn.html',
                           country=country,
                           data= df,
                           fit=fit)


@app.route('/_get_country_cases')
def cases_json():
    country = request.args.get('country', 'United States', type=str)
    date = request.args.get('date', type=int)
    df = get_data(date)
    return jsonify(df[df[country] > 0][country].to_dict())


@app.route('/_get_lmfit_cases')
def lmfit_json():
    country = request.args.get('country', 'United States', type=str)
    date = request.args.get('date', type=int)
    fit = get_model(country, date)
    return jsonify(fit)


@app.route('/_get_country_options')
def country_options():
    date = request.args.get('date', type=int)
    df = get_data(date)
    df = df.drop('Unnamed: 0', axis=1, errors='ignore')
    a = df.describe().loc['max']
    indexes = df.iloc[:, 1:].gt(100).idxmax()
    result = df['date'][indexes]
    result.index = indexes.index
    return jsonify(countries=a[a > 100].sort_values(ascending=False).index.values.tolist(), min_date=result.to_dict())


@app.route('/_get_country_deaths')
def country_deaths():
    country = request.args.get('country', 'United States', type=str)
    date = request.args.get('date', type=int)
    df = get_data2(date)
    return jsonify(df[df[country] > 0][country].to_dict())


@app.route('/_get_lmfit_deaths')
def model_deaths():
    country = request.args.get('country', 'United States', type=str)
    date = request.args.get('date', type=int)
    fit = get_death_model(country, date)
    return jsonify(fit)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
