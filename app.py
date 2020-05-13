from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime

# from nnData import *
from data import *

app = Flask(__name__)


@app.route('/')
def hello_world():
    return redirect(url_for('model'))


@app.route('/world/model')
def model():
    country = request.args.get('country', 'United States', type=str)
    date = request.args.get('date', (datetime.today() - datetime(2019, 12, 31)).days, type=int)
    df = get_data(date)
    fit = get_model(country, date)
    return render_template('model.html', country=country,
                           data=df[df[country] > 0][country].to_dict(),
                           fit=fit,
                           date=date)


@app.route('/world/nn')
def nn():
    country = request.args.get('country', 'United States', type=str)
    date = request.args.get('date', (datetime.today() - datetime(2019, 12, 31)).days, type=int)
    df = get_data(date)
    df = df[df[country] > 0][country]
    fit = get_prediction(country, date)
    if fit is None:
        return render_template('nn.html',
                               country=country,
                               data=df.to_dict(),
                               fit=dict(),
                               date=date)
    return render_template('nn.html',
                           country=country,
                           data=df.to_dict(),
                           fit=fit.to_dict(),
                           date=date)


@app.route('/state/model')
def state_model():
    s = request.args.get('state', 'CA', type=str)
    date = request.args.get('date', int(datetime.today().strftime("%Y%m%d")), type=int)
    df = get_state_data(s, date)
    fit = get_state_model(s, date, 'positive')
    return render_template('state_model.html', country=s,
                           data=df['positive'].to_dict(),
                           fit=fit,
                           date=date)


@app.route('/state/_cases')
def state_cases():
    s = request.args.get('state', 'CA', type=str)
    date = request.args.get('date', int(datetime.today().strftime("%Y%m%d")), type=int)
    df = get_state_data(s, date)
    return jsonify(df['positive'].to_dict())


@app.route('/state/_deaths')
def state_deaths():
    s = request.args.get('state', 'CA', type=str)
    date = request.args.get('date', int(datetime.today().strftime("%Y%m%d")), type=int)
    df = get_state_data(s, date)
    return jsonify(df['death'].to_dict())


@app.route('/state/_lmfit_cases')
def cases_lmfit():
    s = request.args.get('state', 'CA', type=str)
    date = request.args.get('date', int(datetime.today().strftime("%Y%m%d")), type=int)
    fit = get_state_model(s, date, 'positive')
    return jsonify(fit)


@app.route('/state/_lmfit_deaths')
def deaths_lmfit():
    s = request.args.get('state', 'CA', type=str)
    date = request.args.get('date', int(datetime.today().strftime("%Y%m%d")), type=int)
    fit = get_state_model(s, date, 'death')
    return jsonify(fit)


@app.route('/state/_options')
def state_options():
    date = request.args.get('date', int(datetime.today().strftime("%Y%m%d")), type=int)
    df = pd.read_csv('https://covidtracking.com/api/v1/states/daily.csv')
    df = df[df['date'] >= 20200304]
    df = df[df['date'] <= date]
    df = pd.DataFrame(df.values[::-1], df.index, df.columns)
    df = df.fillna(0)
    indexes = dict()
    for s in df.groupby('state').groups.keys():
        sdf = df[df['state'] == s][df[df['state'] == s]['positive'] > 100]
        if len(sdf.index) != 0:
            tmp = str(sdf['date'].iloc[0])
            indexes[s] = '-'.join([tmp[:4], tmp[4:6], tmp[6:]])
    return jsonify(countries=list(indexes.keys()), min_date=indexes)


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


@app.route('/_get_nn_cases')
def nn_json():
    country = request.args.get('country', 'United States', type=str)
    date = request.args.get('date', type=int)
    fit = get_prediction(country, date)
    if fit is not None:
        return jsonify(data=fit.to_dict(), success=True)
    return jsonify(data={}, success=False)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
