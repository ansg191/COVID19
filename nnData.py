from tensorflow.keras.models import load_model

from data import *

model = load_model('model_01')
preds = dict()


def make_predictions(df: pd.DataFrame, end_day=150, minimum=0):
    a = df.describe().loc['max']
    current_day = len(df.index)
    predictions = pd.DataFrame(columns=a[a > minimum].index.values, index=range(current_day, end_day + 1))
    i = 1
    for country in predictions.columns:
        new_x = df[country].values
        for j in range(current_day, end_day + 1):
            new_x = np.append(new_x, model.predict(new_x[-4:].reshape((-1, 4))).astype('int64').flatten()[0])
            predictions[country][j] = new_x[-1]
        print(f"\t{i}) {country}: {df[country].values[-1]}")
        i += 1
    return predictions


def make_prediction(df: pd.Series, end_day=150):
    current_day = df.index[-1] + 1
    predictions = pd.Series(index=range(current_day, end_day + 1))
    new_x = df.values
    for j in range(current_day, end_day + 1):
        new_x = np.append(new_x, model.predict(new_x[-4:].reshape((-1, 4))).astype('int64').flatten()[0])
        predictions[j] = new_x[-1]
    return predictions


def pred_to_file(day, end_day=150, minimum=0):
    df = get_data(day)
    file = f"assets/nn/preds_nn_{len(df.index) - 1}.csv"
    preds = make_predictions(df, end_day=end_day, minimum=minimum)
    preds.to_csv(file)
    print(f'\nWrote to {file}')


def pred_to_file2(day, extra_days=50, minimum=0):
    df = get_data(day)
    file = f"assets/nn/preds_nn_{len(df.index) - 1}.csv"
    preds = make_predictions(df, end_day=len(df.index) - 1 + extra_days, minimum=minimum)
    preds.to_csv(file)
    print(f'\nWrote to {file}')


def get_prediction(df, country, date):
    if date in preds:
        return preds[country]
    elif os.path.isfile(f"assets/nn/preds_nn_{date}.csv"):
        df = pd.read_csv(f"assets/nn/preds_nn_{date}.csv")
        preds[date] = df
    else:
        print("File not created...")
        pred = make_prediction(df, df.index[-1] + 50)
        preds[date] = pred
        return pred
