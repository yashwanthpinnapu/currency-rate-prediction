# -*- coding: utf-8 -*-
"""Final Project

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1M1cPa6q2kecgeWG9O506BKleBluZZME_
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from prophet import Prophet
import plotly.graph_objs as go
from plotly.offline import iplot, init_notebook_mode
import plotly.io as pio
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.offline as po
import pandas as pd
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from pylab import rcParams
from sklearn.metrics import mean_squared_error, mean_absolute_error
import math
import numpy as np
init_notebook_mode(connected=True)
pio.renderers.default = 'colab'

# List of currency pairs with USD
currency_pairs = ['EURUSD=X', 'JPY=X', 'GBPUSD=X', 'CNY=X', 'INR=X']

# Initialize an empty DataFrame to hold all data
all_currency_data = pd.DataFrame()

start_date = '2000-01-01'
end_date = datetime.today().strftime('%Y-%m-%d')

# Fetch data for each currency pair
for pair in currency_pairs:
    data = yf.download(pair, start=start_date, end=end_date, progress=False)
    if not data.empty:
        data['Currency_Pair'] = pair  # Add a column for the currency pair
        all_currency_data = pd.concat([all_currency_data, data], axis=0)

# Define the function to fill NaN with the average of next and previous values
def fill_with_avg_of_neighbors(df):
    for col in df.columns:
        # Only apply to numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            for i in df[col].index[df[col].isnull()]:
                # Get previous and next value
                prev_val = df[col].iloc[max(0, i-1)]
                next_val = df[col].iloc[min(len(df[col]) - 1, i+1)]

                # Calculate the average
                avg_val = (prev_val + next_val) / 2

                # Assign the average value to the null entry
                df.at[i, col] = avg_val
    return df

# Reset the index of the DataFrame
all_currency_data.reset_index(inplace=True)

# Fill NaN values with the average of the next and previous row's values
all_currency_data = fill_with_avg_of_neighbors(all_currency_data)

# Replace values in 'Currency_Pair' column
replacement_dict = {
    'EURUSD=X': 'EUR',
    'JPY=X': 'JPY',
    'GBPUSD=X': 'GBP',
    'CNY=X': 'CNY',
    'INR=X': 'INR'
}

all_currency_data['Currency_Pair'] = all_currency_data['Currency_Pair'].replace(replacement_dict)

# Define the function to fill NaN with the average of next and previous values
def fill_with_avg_of_neighbors(df):
    for col in df.columns:
        # Only apply to numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            for i in df[col].index[df[col].isnull()]:
                # Get previous and next value
                prev_val = df[col].iloc[max(0, i-1)]
                next_val = df[col].iloc[min(len(df[col]) - 1, i+1)]

                # Calculate the average
                avg_val = (prev_val + next_val) / 2

                # Assign the average value to the null entry
                df.at[i, col] = avg_val
    return df


# Fill NaN values with the average of the next and previous row's values
all_currency_data = fill_with_avg_of_neighbors(all_currency_data)

# Colums to format and limit it to 3 digits after the decimal to preserve complexity
columns_to_format = ['Open', 'High', 'Low', 'Close']

# Apply rounding to three decimal places
all_currency_data[columns_to_format] = all_currency_data[columns_to_format].round(4)

#Dropping the volume column that is not useful
all_currency_data.drop(columns = 'Volume', axis =1, inplace = True)

currency_pairs = all_currency_data['Currency_Pair'].unique()


for pair in currency_pairs:
    # Using .loc to ensure changes are made to the original DataFrame
    subset_index = all_currency_data['Currency_Pair'] == pair
    all_currency_data.loc[subset_index, 'Return'] = all_currency_data.loc[subset_index, 'Adj Close'].pct_change()
    all_currency_data.loc[subset_index, 'Volatility'] = (
        all_currency_data.loc[subset_index, 'Return']
        .rolling(window=252)
        .std() * (252 ** 0.5)
    )

# Reset the index of the DataFrame
all_currency_data.reset_index(inplace=True)
all_currency_data.drop(columns = 'index', axis =1, inplace = True)
# Fill NaN values with the average of the next and previous row's values
all_currency_data = fill_with_avg_of_neighbors(all_currency_data)


all_currency_data.fillna(0, inplace=True)
missing_values = all_currency_data.isna().sum()

# check for outliers
def remove_outliers(data):

  Q1 = data['Close'].quantile(0.25)
  Q3 = data['Close'].quantile(0.75)
  IQR = Q3 - Q1

  # Define bounds for what you consider to be an outlier
  lower_bound = Q1 - 1.5 * IQR
  upper_bound = Q3 + 1.5 * IQR

  # Filter out the outliers
  data = data[(data['Close'] >= lower_bound) & (data['Close'] <= upper_bound)]

  return data


df = pd.DataFrame()
all_currency_data_cleaned = pd.DataFrame()

for curr in ['INR','GBP','EUR','CNY']:
  df = remove_outliers(all_currency_data[all_currency_data['Currency_Pair']==curr])

  all_currency_data_cleaned = pd.concat([all_currency_data_cleaned,df], axis = 0)

data = all_currency_data[all_currency_data['Currency_Pair'] == 'JPY']

#Concat the data
all_currency_data_cleaned = pd.concat([all_currency_data_cleaned,data], axis = 0)
def calc_lag (df, lag_days):
  for lag in lag_days:
      df[f'Close_lag_{lag}'] = df['Close'].shift(lag)
  return df

#Calculate moving averages
moving_averages = [10]  # Example window sizes
def calc_ma(df, moving_averages):
  for ma in moving_averages:
    df[f'Close_MA_5'] = df['Close'].shift(1).rolling(window=ma).mean()
  return df



#Calculate the Relative Strength Index (RSI)
def compute_rsi(df, data, window=14):
    delta = data.diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    # Shift the series to exclude the current row from the rolling calculation
    up_shifted = up.shift(1)
    down_shifted = down.shift(1)

    gain = up_shifted.rolling(window=window).mean()
    loss = down_shifted.abs().rolling(window=window).mean()

    RS = gain / loss
    x = 100 - (100 / (1 + RS))
    df['RSI'] = x
    return df

def feature_engg(df, lag_days=[7], moving_averages=[10]):
  df1 = pd.DataFrame()
  df4 = df

  df4 = calc_lag(df4, lag_days)

  df4 = calc_ma(df4, moving_averages)

  df4 = compute_rsi(df4, df4['Close'])

  df1 = pd.concat([df1, df4], axis = 0, ignore_index=False)

  return df1

def EURO(all_currency_data):
  currency_pair = 'EUR'
  data = all_currency_data
  other_df = data[data['Currency_Pair'] == 'GBP'][['Date','Close']]
  other_df['Other_Close'] = other_df['Close']
  other_df.drop('Close', axis =1, inplace = True)


  data = data[data['Currency_Pair'] == currency_pair]
  # Perform a left merge based on the 'ID' column
  data = data.merge(other_df, on='Date', how='left')

  #Fill Missing and null values
  data.loc[data['Other_Close'].isnull(), 'Other_Close'] = data.loc[data['Other_Close'].isnull(), 'Close']
  data = feature_engg(data, [7], [10])

  # Test train split
  data = data[ data['Date'] > '2009-01-01']

  data = data.sort_values(by='Date', ascending=True).reset_index(drop=True)


  # Check if test set is too small
  

  # Prepare the training data for Prophet
  df_train_EUR = pd.DataFrame({
      'ds': pd.to_datetime(data['Date']),
      'y': data['Close'],
      'Open': data['Open'],
      'Close_lag_7' : data['Close_lag_7'],
      'Close_MA_5' : data['Close_MA_5'],
      'RSI' : data['RSI']
  })


  # Define and fit the Prophet model
  model_EUR = Prophet(seasonality_mode = 'multiplicative', weekly_seasonality=True, daily_seasonality =True, yearly_seasonality=True)

  #Adding the regressors
  model_EUR.add_regressor('Open')
  #model_EUR.add_regressor('High')
  #model_EUR.add_regressor('Low')
  #model_EUR.add_regressor('Return')
  #model_EUR.add_regressor('Volatility')
  #model_EUR.add_regressor('Other_Close')
  model_EUR.add_regressor('Close_lag_7')
  model_EUR.add_regressor('Close_MA_5')
  model_EUR.add_regressor('RSI')


  #Fitting the model
  model_EUR.fit(df_train_EUR)



  def generate_future_weekdays(start_date, num_days):
      future_dates = []
      current_date = start_date
      while len(future_dates) < num_days:
          current_date += pd.Timedelta(days=1)
          # Check if it's a weekday (0=Monday, 6=Sunday)
          if current_date.weekday() < 5:
              future_dates.append(current_date)
      return future_dates

  last_date = df_train_EUR['ds'].iloc[-1]
  future_dates = generate_future_weekdays(last_date, 7)
  future = pd.DataFrame({'ds' : future_dates})

  # Assume the last known 'Open' price is the last known 'Close' price
  last_known_open = data['Close'].iloc[-1]

  # DataFrame to store the predictions
  predictions_EUR = pd.DataFrame({
      'Date': future_dates,
      'Close': [0]*len(future_dates),
      'Close_lag_7' : [0]*len(future_dates),
      'Close_MA_5' : [0]*len(future_dates),
      'RSI' : [0]*len(future_dates),
      'High' : [0]*len(future_dates),
      'Low' : [0]*len(future_dates)
    })

  predictions_EUR = pd.concat([data[['Date','Close','Close_lag_7','Close_MA_5', 'RSI', 'High', 'Low']][-200:], predictions_EUR], axis = 0, ignore_index=False,)
  predictions_EUR.reset_index(inplace = True, drop = True)


  # Iteratively predict the next day's 'Close' and set it as the next 'Open'
  for i in range(len(future_dates)):
      # Set the 'Open' price for the current day
      predictions_EUR = feature_engg(predictions_EUR, [7], [10])
      df = predictions_EUR[-(len(future_dates)):]
      df.reset_index(inplace =True, drop = True)
      future.at[i, 'Open'] = last_known_open
      future['RSI'] = df['RSI']
      future['Close_lag_7'] = df['Close_lag_7']
      future['Close_MA_5'] = df['Close_MA_5']

      # Make the prediction for the current day
      forecast = model_EUR.predict(future.iloc[[i]])


      df.at[i, 'Close'] = forecast['yhat'].iloc[0]
      df.at[i, 'High'] = forecast['yhat_upper'].iloc[0]
      df.at[i, 'Low'] = forecast['yhat_lower'].iloc[0]

      predictions_EUR = predictions_EUR[:-(len(future_dates))]
      predictions_EUR = pd.concat([predictions_EUR, df], axis = 0, ignore_index = True)


      # Get the predicted 'Close' price
      predicted_close = forecast['yhat'].iloc[0]

      # Update the last known 'Open' price
      last_known_open = predicted_close

  return predictions_EUR[-20:]

predictions_EUR = EURO(all_currency_data_cleaned)

def GBP(all_currency_data, predictions_EUR):
  currency_pair = 'GBP'
  data = all_currency_data
  other_df = data[data['Currency_Pair'] == 'EUR'][['Date','Close']]
  other_df['Other_Close'] = other_df['Close']
  other_df.drop('Close', axis =1, inplace = True)


  data = data[data['Currency_Pair'] == currency_pair]
  # Perform a left merge based on the 'ID' column
  data = data.merge(other_df, on='Date', how='left')

  #Fill Missing and null values
  data.loc[data['Other_Close'].isnull(), 'Other_Close'] = data.loc[data['Other_Close'].isnull(), 'Close']
  data = feature_engg(data, [7], [10])

  # Test train split
  data = data[ data['Date'] > '2009-01-01']

  data = data.sort_values(by='Date', ascending=True).reset_index(drop=True)

  

  # Prepare the training data for Prophet
  df_train_EUR = pd.DataFrame({
      'ds': pd.to_datetime(data['Date']),
      'y': data['Close'],
      'Open': data['Open'],
      'Close_lag_7' : data['Close_lag_7'],
      'Close_MA_5' : data['Close_MA_5'],
      'RSI' : data['RSI'],
      'Other_Close' : data['Other_Close']
  })


  # Define and fit the Prophet model
  model_EUR = Prophet(seasonality_mode = 'multiplicative', weekly_seasonality=True, daily_seasonality =True, yearly_seasonality=True)

  #Adding the regressors
  model_EUR.add_regressor('Open')
  #model_EUR.add_regressor('High')
  #model_EUR.add_regressor('Low')
  #model_EUR.add_regressor('Return')
  #model_EUR.add_regressor('Volatility')
  model_EUR.add_regressor('Other_Close')
  model_EUR.add_regressor('Close_lag_7')
  model_EUR.add_regressor('Close_MA_5')
  model_EUR.add_regressor('RSI')


  #Fitting the model
  model_EUR.fit(df_train_EUR)



  def generate_future_weekdays(start_date, num_days):
      future_dates = []
      current_date = start_date
      while len(future_dates) < num_days:
          current_date += pd.Timedelta(days=1)
          # Check if it's a weekday (0=Monday, 6=Sunday)
          if current_date.weekday() < 5:
              future_dates.append(current_date)
      return future_dates

  last_date = df_train_EUR['ds'].iloc[-1]
  future_dates = generate_future_weekdays(last_date, 7)
  future = pd.DataFrame({'ds' : future_dates})

  # Assume the last known 'Open' price is the last known 'Close' price
  last_known_open = data['Close'].iloc[-1]
  other_close = predictions_EUR['Close'][-(len(future_dates)):]
  # DataFrame to store the predictions
  predictions_GBP = pd.DataFrame({
      'Date': future_dates,
      'Close': [0]*len(future_dates),
      'Close_lag_7' : [0]*len(future_dates),
      'Close_MA_5' : [0]*len(future_dates),
      'RSI' : [0]*len(future_dates),
      'High' : [0]*len(future_dates),
      'Low' : [0]*len(future_dates),
      'Other_Close' : other_close
    })

  predictions_GBP = pd.concat([data[['Date','Close','Close_lag_7','Close_MA_5', 'RSI', 'High', 'Low', 'Other_Close']][-200:], predictions_GBP], axis = 0, ignore_index=False,)
  predictions_GBP.reset_index(inplace = True, drop = True)


  # Iteratively predict the next day's 'Close' and set it as the next 'Open'
  for i in range(len(future_dates)):
      # Set the 'Open' price for the current day
      predictions_GBP = feature_engg(predictions_GBP, [7], [10])
      df = predictions_GBP[-(len(future_dates)):]
      df.reset_index(inplace =True, drop = True)
      future.at[i, 'Open'] = last_known_open
      future['RSI'] = df['RSI']
      future['Close_lag_7'] = df['Close_lag_7']
      future['Close_MA_5'] = df['Close_MA_5']
      future['Other_Close'] = df['Other_Close']

      # Make the prediction for the current day
      forecast = model_EUR.predict(future.iloc[[i]])


      df.at[i, 'Close'] = forecast['yhat'].iloc[0]
      df.at[i, 'High'] = forecast['yhat_upper'].iloc[0]
      df.at[i, 'Low'] = forecast['yhat_lower'].iloc[0]

      predictions_GBP = predictions_GBP[:-(len(future_dates))]
      predictions_GBP = pd.concat([predictions_GBP, df], axis = 0, ignore_index = True)


      # Get the predicted 'Close' price
      predicted_close = forecast['yhat'].iloc[0]

      # Update the last known 'Open' price
      last_known_open = predicted_close

  return predictions_GBP[-20:]

def JPY(all_currency_data):
  currency_pair = 'JPY'
  data = all_currency_data
  other_df = data[data['Currency_Pair'] == 'GBP'][['Date','Close']]
  other_df['Other_Close'] = other_df['Close']
  other_df.drop('Close', axis =1, inplace = True)


  data = data[data['Currency_Pair'] == currency_pair]
  # Perform a left merge based on the 'ID' column
  data = data.merge(other_df, on='Date', how='left')

  #Fill Missing and null values
  data.loc[data['Other_Close'].isnull(), 'Other_Close'] = data.loc[data['Other_Close'].isnull(), 'Close']

  data = feature_engg(data, [7], [10])
  # Test train split
  data = data[ data['Date'] > '2009-01-01']

  data = data.sort_values(by='Date', ascending=True).reset_index(drop=True)

 
  # Prepare the training data for Prophet
  df_train_EUR = pd.DataFrame({
      'ds': pd.to_datetime(data['Date']),
      'y': data['Close'],
      'Open': data['Open'],
      'Close_lag_7' : data['Close_lag_7'],
      'Close_MA_5' : data['Close_MA_5'],
      'RSI' : data['RSI']
  })


  # Define and fit the Prophet model
  model_EUR = Prophet(seasonality_mode = 'multiplicative', weekly_seasonality=True, daily_seasonality =True, yearly_seasonality=True)

  #Adding the regressors
  model_EUR.add_regressor('Open')
  #model_EUR.add_regressor('High')
  #model_EUR.add_regressor('Low')
  #model_EUR.add_regressor('Return')
  #model_EUR.add_regressor('Volatility')
  #model_EUR.add_regressor('Other_Close')
  model_EUR.add_regressor('Close_lag_7')
  model_EUR.add_regressor('Close_MA_5')
  model_EUR.add_regressor('RSI')


  #Fitting the model
  model_EUR.fit(df_train_EUR)



  def generate_future_weekdays(start_date, num_days):
      future_dates = []
      current_date = start_date
      while len(future_dates) < num_days:
          current_date += pd.Timedelta(days=1)
          # Check if it's a weekday (0=Monday, 6=Sunday)
          if current_date.weekday() < 5:
              future_dates.append(current_date)
      return future_dates

  last_date = df_train_EUR['ds'].iloc[-1]
  future_dates = generate_future_weekdays(last_date, 7)
  future = pd.DataFrame({'ds' : future_dates})

  # Assume the last known 'Open' price is the last known 'Close' price
  last_known_open = data['Close'].iloc[-1]

  # DataFrame to store the predictions
  predictions_EUR = pd.DataFrame({
      'Date': future_dates,
      'Close': [0]*len(future_dates),
      'Close_lag_7' : [0]*len(future_dates),
      'Close_MA_5' : [0]*len(future_dates),
      'RSI' : [0]*len(future_dates),
      'High' : [0]*len(future_dates),
      'Low' : [0]*len(future_dates)
    })

  predictions_EUR = pd.concat([data[['Date','Close','Close_lag_7','Close_MA_5', 'RSI', 'High', 'Low']][-200:], predictions_EUR], axis = 0, ignore_index=False,)
  predictions_EUR.reset_index(inplace = True, drop = True)


  # Iteratively predict the next day's 'Close' and set it as the next 'Open'
  for i in range(len(future_dates)):
      # Set the 'Open' price for the current day
      predictions_EUR = feature_engg(predictions_EUR, [7], [10])
      df = predictions_EUR[-(len(future_dates)):]
      df.reset_index(inplace =True, drop = True)
      future.at[i, 'Open'] = last_known_open
      future['RSI'] = df['RSI']
      future['Close_lag_7'] = df['Close_lag_7']
      future['Close_MA_5'] = df['Close_MA_5']

      # Make the prediction for the current day
      forecast = model_EUR.predict(future.iloc[[i]])


      df.at[i, 'Close'] = forecast['yhat'].iloc[0]
      df.at[i, 'High'] = forecast['yhat_upper'].iloc[0]
      df.at[i, 'Low'] = forecast['yhat_lower'].iloc[0]

      predictions_EUR = predictions_EUR[:-(len(future_dates))]
      predictions_EUR = pd.concat([predictions_EUR, df], axis = 0, ignore_index = True)


      # Get the predicted 'Close' price
      predicted_close = forecast['yhat'].iloc[0]

      # Update the last known 'Open' price
      last_known_open = predicted_close

  return predictions_EUR[-20:]

def INR(all_currency_data):
  currency_pair = 'INR'
  data = all_currency_data
  other_df = data[data['Currency_Pair'] == 'GBP'][['Date','Close']]
  other_df['Other_Close'] = other_df['Close']
  other_df.drop('Close', axis =1, inplace = True)


  data = data[data['Currency_Pair'] == currency_pair]
  # Perform a left merge based on the 'ID' column
  data = data.merge(other_df, on='Date', how='left')

  #Fill Missing and null values
  data.loc[data['Other_Close'].isnull(), 'Other_Close'] = data.loc[data['Other_Close'].isnull(), 'Close']
  data = feature_engg(data, [7], [10])

  # Test train split
  data = data[ data['Date'] > '2009-01-01']

  data = data.sort_values(by='Date', ascending=True).reset_index(drop=True)

  
  # Prepare the training data for Prophet
  df_train_EUR = pd.DataFrame({
      'ds': pd.to_datetime(data['Date']),
      'y': data['Close'],
      'Open': data['Open'],
      'Close_lag_7' : data['Close_lag_7'],
      'Close_MA_5' : data['Close_MA_5'],
      'RSI' : data['RSI']
  })


  # Define and fit the Prophet model
  model_EUR = Prophet(seasonality_mode = 'multiplicative', weekly_seasonality=True, daily_seasonality =True, yearly_seasonality=True)

  #Adding the regressors
  model_EUR.add_regressor('Open')
  #model_EUR.add_regressor('High')
  #model_EUR.add_regressor('Low')
  #model_EUR.add_regressor('Return')
  #model_EUR.add_regressor('Volatility')
  #model_EUR.add_regressor('Other_Close')
  model_EUR.add_regressor('Close_lag_7')
  model_EUR.add_regressor('Close_MA_5')
  model_EUR.add_regressor('RSI')


  #Fitting the model
  model_EUR.fit(df_train_EUR)



  def generate_future_weekdays(start_date, num_days):
      future_dates = []
      current_date = start_date
      while len(future_dates) < num_days:
          current_date += pd.Timedelta(days=1)
          # Check if it's a weekday (0=Monday, 6=Sunday)
          if current_date.weekday() < 5:
              future_dates.append(current_date)
      return future_dates

  last_date = df_train_EUR['ds'].iloc[-1]
  future_dates = generate_future_weekdays(last_date, 7)
  future = pd.DataFrame({'ds' : future_dates})

  # Assume the last known 'Open' price is the last known 'Close' price
  last_known_open = data['Close'].iloc[-1]

  # DataFrame to store the predictions
  predictions_EUR = pd.DataFrame({
      'Date': future_dates,
      'Close': [0]*len(future_dates),
      'Close_lag_7' : [0]*len(future_dates),
      'Close_MA_5' : [0]*len(future_dates),
      'RSI' : [0]*len(future_dates),
      'High' : [0]*len(future_dates),
      'Low' : [0]*len(future_dates)
    })

  predictions_EUR = pd.concat([data[['Date','Close','Close_lag_7','Close_MA_5', 'RSI', 'High', 'Low']][-200:], predictions_EUR], axis = 0, ignore_index=False,)
  predictions_EUR.reset_index(inplace = True, drop = True)


  # Iteratively predict the next day's 'Close' and set it as the next 'Open'
  for i in range(len(future_dates)):
      # Set the 'Open' price for the current day
      predictions_EUR = feature_engg(predictions_EUR, [7], [10])
      df = predictions_EUR[-(len(future_dates)):]
      df.reset_index(inplace =True, drop = True)
      future.at[i, 'Open'] = last_known_open
      future['RSI'] = df['RSI']
      future['Close_lag_7'] = df['Close_lag_7']
      future['Close_MA_5'] = df['Close_MA_5']

      # Make the prediction for the current day
      forecast = model_EUR.predict(future.iloc[[i]])


      df.at[i, 'Close'] = forecast['yhat'].iloc[0]
      df.at[i, 'High'] = forecast['yhat_upper'].iloc[0]
      df.at[i, 'Low'] = forecast['yhat_lower'].iloc[0]

      predictions_EUR = predictions_EUR[:-(len(future_dates))]
      predictions_EUR = pd.concat([predictions_EUR, df], axis = 0, ignore_index = True)


      # Get the predicted 'Close' price
      predicted_close = forecast['yhat'].iloc[0]

      # Update the last known 'Open' price
      last_known_open = predicted_close

  return predictions_EUR[-20:]

def CNY(all_currency_data):
  currency_pair = 'CNY'
  data = all_currency_data
  other_df = data[data['Currency_Pair'] == 'GBP'][['Date','Close']]
  other_df['Other_Close'] = other_df['Close']
  other_df.drop('Close', axis =1, inplace = True)


  data = data[data['Currency_Pair'] == currency_pair]
  # Perform a left merge based on the 'ID' column
  data = data.merge(other_df, on='Date', how='left')

  #Fill Missing and null values
  data.loc[data['Other_Close'].isnull(), 'Other_Close'] = data.loc[data['Other_Close'].isnull(), 'Close']
  data = feature_engg(data, [7], [10])

  # Test train split
  data = data[ data['Date'] > '2009-01-01']

  data = data.sort_values(by='Date', ascending=True).reset_index(drop=True)

  
  # Prepare the training data for Prophet
  df_train_EUR = pd.DataFrame({
      'ds': pd.to_datetime(data['Date']),
      'y': data['Close'],
      'Open': data['Open'],
      'Close_lag_7' : data['Close_lag_7'],
      'Close_MA_5' : data['Close_MA_5'],
      'RSI' : data['RSI']
  })


  # Define and fit the Prophet model
  model_EUR = Prophet(seasonality_mode = 'multiplicative', weekly_seasonality=True, daily_seasonality =True, yearly_seasonality=True)

  #Adding the regressors
  model_EUR.add_regressor('Open')
  #model_EUR.add_regressor('High')
  #model_EUR.add_regressor('Low')
  #model_EUR.add_regressor('Return')
  #model_EUR.add_regressor('Volatility')
  #model_EUR.add_regressor('Other_Close')
  model_EUR.add_regressor('Close_lag_7')
  model_EUR.add_regressor('Close_MA_5')
  model_EUR.add_regressor('RSI')


  #Fitting the model
  model_EUR.fit(df_train_EUR)



  def generate_future_weekdays(start_date, num_days):
      future_dates = []
      current_date = start_date
      while len(future_dates) < num_days:
          current_date += pd.Timedelta(days=1)
          # Check if it's a weekday (0=Monday, 6=Sunday)
          if current_date.weekday() < 5:
              future_dates.append(current_date)
      return future_dates

  last_date = df_train_EUR['ds'].iloc[-1]
  future_dates = generate_future_weekdays(last_date, 7)
  future = pd.DataFrame({'ds' : future_dates})

  # Assume the last known 'Open' price is the last known 'Close' price
  last_known_open = data['Close'].iloc[-1]

  # DataFrame to store the predictions
  predictions_EUR = pd.DataFrame({
      'Date': future_dates,
      'Close': [0]*len(future_dates),
      'Close_lag_7' : [0]*len(future_dates),
      'Close_MA_5' : [0]*len(future_dates),
      'RSI' : [0]*len(future_dates),
      'High' : [0]*len(future_dates),
      'Low' : [0]*len(future_dates)
    })

  predictions_EUR = pd.concat([data[['Date','Close','Close_lag_7','Close_MA_5', 'RSI', 'High', 'Low']][-200:], predictions_EUR], axis = 0, ignore_index=False,)
  predictions_EUR.reset_index(inplace = True, drop = True)


  # Iteratively predict the next day's 'Close' and set it as the next 'Open'
  for i in range(len(future_dates)):
      # Set the 'Open' price for the current day
      predictions_EUR = feature_engg(predictions_EUR, [7], [10])
      df = predictions_EUR[-(len(future_dates)):]
      df.reset_index(inplace =True, drop = True)
      future.at[i, 'Open'] = last_known_open
      future['RSI'] = df['RSI']
      future['Close_lag_7'] = df['Close_lag_7']
      future['Close_MA_5'] = df['Close_MA_5']

      # Make the prediction for the current day
      forecast = model_EUR.predict(future.iloc[[i]])


      df.at[i, 'Close'] = forecast['yhat'].iloc[0]
      df.at[i, 'High'] = forecast['yhat_upper'].iloc[0]
      df.at[i, 'Low'] = forecast['yhat_lower'].iloc[0]

      predictions_EUR = predictions_EUR[:-(len(future_dates))]
      predictions_EUR = pd.concat([predictions_EUR, df], axis = 0, ignore_index = True)


      # Get the predicted 'Close' price
      predicted_close = forecast['yhat'].iloc[0]

      # Update the last known 'Open' price
      last_known_open = predicted_close

  return predictions_EUR[-20:]

#Front End
import altair as alt
import streamlit as st
# Define currency pairs with full country names
currency_pairs = {
    'Euro to USD': 'USDEUR',
    'USD to Japanese Yen': 'USDJPY',
    'British Pound to USD': 'USDGBP',
    'USD to Indian Rupee': 'USDINR',
    'USD to Chinese Yuan': 'USDCNY'
}
chart_container = st.container()

def main():
    st.title('Currency Exchange Rate Prediction')
    
    
    # Display buttons in the sidebar
    selected_currency =st.sidebar.radio("Select Currency", list(currency_pairs.keys()))

    # Display chart in the centered container
    

    if st.button('Generate Prediction'):
        display_chart(selected_currency, currency_pairs[selected_currency])

def display_chart(currency_name, currency_code):
    
    
    if currency_code =="USDEUR":
        forecast = predictions_EUR
    elif currency_code =="USDJPY":
        forecast = JPY(all_currency_data_cleaned)
    elif currency_code =="USDGBP":
        forecast = GBP(all_currency_data_cleaned,predictions_EUR)
    elif currency_code =="USDINR":
        forecast = INR(all_currency_data_cleaned)
    elif currency_code =="USDCNY":
        forecast = CNY(all_currency_data_cleaned)
    print(forecast)
    forecast['status']=forecast['Date'].apply(lambda x: 'future' if pd.to_datetime(x) > datetime.now() else 'past')
    chart_data = pd.DataFrame({
        'Date': forecast['Date'],
        'Predicted Exchange Rate': forecast['Close'],"status":forecast['status']
    })
    
    chart = alt.Chart(chart_data).mark_line().encode(
        x=alt.X('Date'),
        y=alt.Y('Predicted Exchange Rate', scale=alt.Scale(domain=[forecast['Low'].min(), forecast['High'].max()]))
    ,color=alt.Color('status',
                   scale=alt.Scale(
            domain=['future','past'],
            range=['orange','lightblue']))).properties(width=600, height=500).interactive()

    st.subheader(f'Exchange Rate Prediction Chart for {currency_name}')
    st.altair_chart(chart)
    grouped = chart_data.groupby(chart_data.status)
    cd = grouped.get_group("future")
    cd.drop(cd.columns[[2]], axis=1, inplace=True)
    st.dataframe(cd.set_index(cd.columns[0]))

if __name__ == '__main__':
    main()