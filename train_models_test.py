import pandas as pd
import numpy as np
import seaborn as sn
import joblib
import sklearn.ensemble as ens
from numbers import Number
from time import time, sleep
from ta import momentum as mo
from ta import volume as vo
from ta import trend as tr
from sklearn import preprocessing as pp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support as score
from sklearn.metrics import accuracy_score as acs


# ROC de Y em relação a X
def change(x, y):
    if len(x) == len(y):
        change_arr = []
        for i in range(0, len(x)):
            if isinstance(x[i], Number) and isinstance(y[i], Number):
                change_arr.append(((y[i] - x[i]) / x[i]) * 100)
            else:
                change_arr.append('NaN')

        return change_arr
    else:
        print(f"Error: x length {len(x)}, y length {len(y)}")


def build_df(hist_data):
    # print(change([1, 2],[2, 1])) # [100.0, -50.0] Yn > Xn se valor positivo
    trend_window = 10
    slice_start = 50
    slice_plus = 0

    roc = mo.roc(hist_data['Close'], window=25)
    rsi = mo.rsi(hist_data['Close'])
    stochrsi = mo.stochrsi(hist_data['Close'])
    stochrsi_d = mo.stochrsi_d(hist_data['Close'])
    stochrsi_k = mo.stochrsi_k(hist_data['Close'])
    tsi = mo.tsi(hist_data['Close'])
    tsi_signal = tr.ema_indicator(tsi, window=13)
    macd = tr.macd(hist_data['Close'])
    macd_diff = tr.macd_diff(hist_data['Close'])
    macd_signal = tr.macd_signal(hist_data['Close'])
    stoch = mo.stoch(hist_data['High'], hist_data['Low'], hist_data['Close'])
    ema_w8 = tr.ema_indicator(hist_data['Close'], window=8)
    ema_w20 = tr.ema_indicator(hist_data['Close'], window=20)
    sma_w13 = tr.sma_indicator(hist_data['Close'], window=13)
    sma_w25 = tr.sma_indicator(hist_data['Close'], window=25)
    roc_close_ema_w8 = change(ema_w8, hist_data['Close'])
    roc_ema_w8_ema_w20 = change(ema_w20, ema_w8)
    roc_close_ema_w20 = change(ema_w20, hist_data['Close'])
    roc_close_sma_w13 = change(sma_w13, hist_data['Close'])
    roc_sma_w13_sma_w25 = change(sma_w25, sma_w13)
    roc_close_sma_w25 = change(sma_w25, hist_data['Close'])

    trend = mo.roc(hist_data['Close'], window=trend_window).map(
        lambda n: 'HIGH' if n > 0 else 'LOW')

    df = pd.DataFrame({
        'close': np.array(list(hist_data['Close'][slice_start:-(trend_window + slice_plus)])),
        # 'roc': np.array(list(roc[slice_start:-(trend_window + slice_plus)])),
        'rsi': np.array(list(rsi[slice_start:-(trend_window + slice_plus)])),
        # 'stoch': np.array(list(stoch[slice_start:-(trend_window + slice_plus)])),
        # 'stochrsi': np.array(list(stochrsi[slice_start:-(trend_window + slice_plus)])),
        # 'stochrsi_d': np.array(list(stochrsi_d[slice_start:-(trend_window + slice_plus)])),
        # 'stochrsi_k': np.array(list(stochrsi_k[slice_start:-(trend_window + slice_plus)])),
        'macd': np.array(list(macd[slice_start:-(trend_window + slice_plus)])),
        'macd_diff': np.array(list(macd_diff[slice_start:-(trend_window + slice_plus)])),
        'macd_signal': np.array(list(macd_signal[slice_start:-(trend_window + slice_plus)])),
        'tsi': np.array(list(tsi[slice_start:-(trend_window + slice_plus)])),
        'tsi_signal': np.array(list(tsi_signal[slice_start:-(trend_window + slice_plus)])),
        'ema_w8': np.array(list(ema_w8[slice_start:-trend_window])),
        'ema_w20': np.array(list(ema_w20[slice_start:-trend_window])),

        # 'roc_close_ema_w8': np.array(list(roc_close_ema_w8[slice_start:-(trend_window + slice_plus)])),
        # 'roc_ema_w8_ema_w20': np.array(list(roc_ema_w8_ema_w20[slice_start:-(trend_window + slice_plus)])),
        # 'roc_close_ema_w20': np.array(list(roc_close_ema_w20[slice_start:-(trend_window + slice_plus)])),
        # 'roc_close_sma_w13': np.array(list(roc_close_sma_w13[slice_start:-(trend_window + slice_plus)])),
        # 'roc_sma_w13_sma_w25': np.array(list(roc_sma_w13_sma_w25[slice_start:-(trend_window + slice_plus)])),
        # 'roc_close_sma_w25': np.array(list(roc_close_sma_w25[slice_start:-(trend_window + slice_plus)])),
        'trend': np.array(list(trend[(slice_start + trend_window)::]))
    })

    return df


year = 31536000
period1 = round(time() - (year * 2))
period2 = round(time())
list_assets = pd.read_csv('data/markets_list.csv')
pr = {'symbol': [], 'acc': []}
nr = {'symbol': [], 'acc': []}

for i in list_assets.values:
    sleep(5)
    try:
        hist_data = pd.read_csv(
            f'https://query1.finance.yahoo.com/v7/finance/download/{i[0]}?period1={period1}&period2={period2}&interval=1d&events=history&includeAdjustedClose=true')
        df = build_df(hist_data)

        train = df.iloc[0:-5,0::].sample(frac=1)
        test = df.iloc[-5::,0::]

        x_train = train.iloc[:,0:-1]
        y_train = train.iloc[:,-1]

        x_test = test.iloc[:,0:-1]
        y_test = test.iloc[:,-1].values

        rf = ens.AdaBoostClassifier(n_estimators=800, learning_rate=1.0)
        rf_model = rf.fit(x_train, y_train)
        y_pred = rf_model.predict(x_test)

        corr_pred = 0
        wrong_pred = 0
        for j in list(range(0, len(y_pred))):
            if y_pred[j] == 'LOW' and y_test[j] == 'LOW':
                corr_pred = corr_pred + 1
            elif y_pred[j] == 'HIGH' and y_test[j] == 'HIGH':
                corr_pred = corr_pred + 1
            else:
                wrong_pred = wrong_pred + 1

        acc = corr_pred / len(y_pred)

        if acc >= 0.75:
            pr['symbol'].append(i[0])
            pr['acc'].append(acc)
        else:
            nr['symbol'].append(i[0])
            nr['acc'].append(acc)
    except:
        nr['symbol'].append(i[0])
        nr['acc'].append('Erro404')


pd.DataFrame({'symbol': np.array(pr['symbol']), 'acc': np.array(
        pr['acc'])}).to_csv('results/positive_results.csv', index=False)
pd.DataFrame({'symbol': np.array(nr['symbol']), 'acc': np.array(
    nr['acc'])}).to_csv('results/negative_results.csv', index=False)
