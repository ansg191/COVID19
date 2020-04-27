import pandas as pd
import numpy as np
from lmfit.models import StepModel
import os.path

cases = 'https://covid.ourworldindata.org/data/ecdc/total_cases.csv'
deaths = 'https://covid.ourworldindata.org/data/ecdc/total_deaths.csv'

data = dict()
data2 = dict()


def get_data(date):
    if date in data:
        return data[date]
    elif os.path.isfile(f"assets/df_{date}.csv"):
        df = pd.read_csv(f"assets/df_{date}.csv")
        data[date] = df
    else:
        print('Getting File...')
        df = pd.read_csv(cases)
        df = df.fillna(0)
        if len(df.index) - 1 > date:
            df = df.iloc[:date + 1]
        df.to_csv(f"assets/df_{len(df.index) - 1}.csv")
        data[len(df.index) - 1] = df
    return df


def get_data2(date):
    if date in data2:
        return data2[date]
    elif os.path.isfile(f"assets/df2_{date}.csv"):
        df = pd.read_csv(f"assets/df2_{date}.csv")
        data2[date] = df
    else:
        print('Getting File...')
        df = pd.read_csv(deaths)
        df = df.fillna(0)
        if len(df.index) - 1 > date:
            df = df.iloc[:date + 1]
        df.to_csv(f"assets/df2_{len(df.index) - 1}.csv")
        data2[len(df.index) - 1] = df
    return df


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
