import pandas as pd
import numpy as np
from lmfit.models import StepModel
import os.path
import subprocess as sp

cases = 'https://covid.ourworldindata.org/data/ecdc/total_cases.csv'
deaths = 'https://covid.ourworldindata.org/data/ecdc/total_deaths.csv'
john_hopkins = "https://github.com/CSSEGISandData/COVID-19.git"
repo_location = "assets/john_hopkins"


def create_git():
    pop = sp.Popen(f"sudo git init; sudo git pull {john_hopkins} master", cwd=repo_location, shell=True)
    pop.wait()
    pop.kill()


def update_git():
    if os.path.isdir(repo_location + "/.git"):
        pop = sp.Popen("sudo git fetch --all; sudo git reset --hard origin/master", cwd=repo_location, shell=True)
        pop.wait()
        pop.kill()
    else:
        create_git()


def state(s):
    return f'http://covidtracking.com/api/v1/states/{s}/daily.csv'


data = dict()
data2 = dict()
preds = dict()

state_data = dict()

update_git()


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


def get_state_data(s: str, date: int):
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


def get_state_fit(df, tp):
    x, y = df.index.values, df[tp].values
    mod = StepModel(form='logistic')
    pars = mod.guess(y, x=x)
    fit = mod.fit(y, pars, x=x, weights=(1 / (y + 1e-3))[::-1])
    return fit


def get_state_model(s, date, tp):
    df = get_state_data(s, date)
    fit = get_state_fit(df, tp)
    complall = find_end_day(fit, 1)
    x0 = np.array(list(range(0, complall + 1)))
    return dict(zip(x0.tolist(), fit.eval(x=x0).astype('int64').tolist()))


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
