import pandas as pd
import numpy as np
from lmfit.models import StepModel
import os.path

cases = 'https://covid.ourworldindata.org/data/ecdc/total_cases.csv'
deaths = 'https://covid.ourworldindata.org/data/ecdc/total_deaths.csv'
US_cases = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
           "/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
US_deaths = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
            "/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"


def state(s):
    return f'http://covidtracking.com/api/v1/states/{s}/daily.csv'


def date_to_int(s: str):
    padded = [x.zfill(2) for x in s.split('/')]
    return int(''.join([padded[i] for i in [2, 0, 1]]))


def date_to_str(d):
    s = str(d)
    s = [s[i:i + 2] for i in range(0, len(s), 2)]
    s[0] = "20" + s[0]
    return '-'.join(s)


data = dict()
data2 = dict()

preds = dict()

state_data = dict()

US_data = dict()
US_data2 = dict()

population_state = dict()
population_county = dict()


def get_data(date):
    if date in data:
        return data[date]
    elif os.path.isfile(f"assets/cases/df_{date}.csv"):
        df = pd.read_csv(f"assets/cases/df_{date}.csv")
        data[date] = df
    else:
        print('Getting File...')
        df = pd.read_csv(cases)
        df = df.fillna(0)
        if len(df.index) - 1 > date:
            df = df.iloc[:date + 1]
        df.to_csv(f"assets/cases/df_{len(df.index) - 1}.csv")
        data[len(df.index) - 1] = df
    return df


def get_data2(date):
    if date in data2:
        return data2[date]
    elif os.path.isfile(f"assets/deaths/df2_{date}.csv"):
        df = pd.read_csv(f"assets/deaths/df2_{date}.csv")
        data2[date] = df
    else:
        print('Getting File...')
        df = pd.read_csv(deaths)
        df = df.fillna(0)
        if len(df.index) - 1 > date:
            df = df.iloc[:date + 1]
        df.to_csv(f"assets/deaths/df2_{len(df.index) - 1}.csv")
        data2[len(df.index) - 1] = df
    return df


def get_us_data(date):
    if date in US_data:
        df = US_data[date]
        return df
    elif os.path.isfile(f"assets/john_hopkins/cases_{date}.csv"):
        df = pd.read_csv(f"assets/john_hopkins/cases_{date}.csv", index_col=0)
        US_data[date] = df
        return df
    else:
        print("Getting data...")
        df = pd.read_csv(US_cases)
        df.columns.values[11:] = df.columns[11:].map(date_to_int).values
        df = df.T[np.concatenate([np.array([True] * 11), df.T.index[11:] <= date])].T
        US_data[df.columns[-1]] = df
        df.to_csv(f"assets/john_hopkins/cases_{df.columns[-1]}.csv")
        return df


def get_us_data2(date):
    if date in US_data2:
        df2 = US_data2[date]
        return df2
    elif os.path.isfile(f"assets/john_hopkins/deaths_{date}.csv"):
        df2 = pd.read_csv(f"assets/john_hopkins/deaths_{date}.csv", index_col=0)
        US_data2[date] = df2
        return df2
    else:
        print("Getting data...")
        df2 = pd.read_csv(US_deaths)
        df2.columns.values[12:] = df2.columns[12:].map(date_to_int).values
        df2 = df2.T[np.concatenate([np.array([True] * 12), df2.T.index[12:] <= date])].T
        US_data2[df2.columns[-1]] = df2
        df2.to_csv(f"assets/john_hopkins/deaths_{df2.columns[-1]}.csv")
        return df2


def get_state_data2(s: str, date: int):
    s = s.upper()
    if (s, date) in state_data:
        return state_data[(s, date)]
    elif os.path.isfile(f"assets/state/df_{s}_{date}.csv"):
        df = pd.read_csv(f"assets/state/df_{s}_{date}.csv", index_col=0)
        state_data[(s, date)] = df
    else:
        print('Getting File...')
        df = pd.read_csv(state(s))
        df = df[df['date'] >= 20200304]
        df = df[df['date'] <= date]
        df = pd.DataFrame(df.values[::-1], range(len(df.index)), df.columns)
        df = df.fillna(0)
        df.to_csv(f"assets/state/df_{s}_{df['date'].iloc[-1]}.csv")
        state_data[(state, date)] = df
    return df


def get_state_data(s: str, date: int):
    df = get_us_data(date)
    df2 = get_us_data2(date)
    tmp = pd.concat([df[df['Province_State'] == s].sum(), df2[df2['Province_State'] == s].sum()],
                    axis=1)
    tmp.columns = ['Cases', 'Deaths']
    population_state[s] = tmp.iloc[-1, 1]
    return tmp.iloc[11:-1].apply(pd.to_numeric).reset_index()


def get_state_fit(df, tp):
    x, y = df.index.values, df[tp].values
    mod = StepModel(form='logistic')
    pars = mod.guess(y, x=x)
    fit = mod.fit(y, pars, x=x, weights=(1 / (x + 1e-3))[::-1])
    return fit


def get_state_model(s, date, tp):
    df = get_state_data(s, date)
    fit = get_state_fit(df, tp)
    complall = find_end_day(fit, 1)
    x0 = np.array(list(range(0, complall + 1)))
    return dict(zip(x0.tolist(), fit.eval(x=x0).astype('int64').tolist()))


def get_state_options(date):
    global population_state
    df = get_us_data(date)
    df2 = get_us_data2(date)
    tmp = df.groupby('Province_State').sum()
    tmp = tmp.select_dtypes(['number'])
    tmp2 = tmp.iloc[:, -1].sort_values(ascending=False) > 100
    states = tmp2.loc[tmp2].index.values
    min_dates = tmp.iloc[:, 5:].gt(100).T.idxmax().apply(date_to_str)
    population_state = {**population_state, **df2.groupby('Province_State')['Population'].sum().to_dict()}
    return states, min_dates, population_state


def get_county_data(s, county, date):
    df = get_us_data(date)
    df2 = get_us_data2(date)
    tmp = pd.concat([df[(df['Province_State'] == s) & (df['Admin2'] == county)].iloc[0, 11:],
                     df2[(df2['Province_State'] == s) & (df2['Admin2'] == county)].iloc[0, 11:]], axis=1)
    tmp.columns = ['Cases', 'Deaths']
    population_county[', '.join([county, s])] = tmp.iloc[-1, 1]
    return tmp.iloc[:-1].apply(pd.to_numeric).reset_index()


def get_county_fit(df, tp):
    x, y = df.index.values, df[tp].values
    mod = StepModel(form='logistic')
    pars = mod.guess(y, x=x)
    fit = mod.fit(y, pars, x=x, weights=(1 / (x + 1e-3))[::-1])
    return fit


def get_county_model(s, county, date, tp):
    df = get_county_data(s, county, date)
    fit = get_county_fit(df, tp)
    complall = find_end_day(fit, 1)
    x0 = np.array(list(range(0, complall + 1)))
    return dict(zip(x0.tolist(), fit.eval(x=x0).astype('int64').tolist()))


def get_county_options(date):
    df = get_us_data(date)
    


def get_fit(df, country):
    x, y = df[df[country] > 0][country].index.values, df[df[country] > 0][country].values
    mod = StepModel(form='logistic')
    pars = mod.guess(y, x=x)
    fit = mod.fit(y, pars, x=x, weights=(1 / (y + 1e-3))[::-1])
    return fit


def get_model(country, date):
    df = get_data(date)
    fit = get_fit(df, country)
    complall = find_end_day(fit, 1)
    x0 = np.array(list(range(df[df[country] > 0].first_valid_index(), complall + 1)))
    return dict(zip(x0.tolist(), fit.eval(x=x0).astype('int64').tolist()))


def get_death_model(country, date):
    df = get_data2(date)
    fit = get_fit(df, country)
    complall = find_end_day(fit, 1)
    x0 = np.array(list(range(df[df[country] > 0].first_valid_index(), complall + 1)))
    return dict(zip(x0.tolist(), fit.eval(x=x0).astype('int64').tolist()))


def find_end_day(fit, percent):
    goal = int(fit.params['amplitude'].value) * percent
    i = 0
    while True:
        if fit.eval(x=i) >= goal:
            return i
        i += 1


def get_prediction(country, date):
    print(date)
    if date in preds:
        return preds[date][country]
    elif os.path.isfile(f"assets/nn/preds_nn_{date}.csv"):
        df = pd.read_csv(f"assets/nn/preds_nn_{date}.csv", index_col=0)
        preds[date] = df
        return df[country]
    else:
        print("File not created...")
        # pred = make_prediction(df, df.index[-1] + 50)
        # return pred
        return None
