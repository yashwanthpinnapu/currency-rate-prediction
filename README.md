# Currency Exchange Rate Prediction

## Project Overview

This project predicts the closing exchange rates of major global currencies against the U.S. Dollar (USD). It utilizes time series analysis and the **Facebook Prophet model** to forecast exchange rates for the following currency pairs:

- **British Pound (GBP) to USD**
- **Chinese Yuan (CNY) to USD**
- **Euro (EUR) to USD**
- **Indian Rupee (INR) to USD**
- **Japanese Yen (JPY) to USD**

The project includes **data extraction, preprocessing, feature engineering, model training, evaluation, and a front-end web application built with Streamlit** for easy interaction.

---

## Features

- **Automated Data Collection**: Fetches historical exchange rates using the Yahoo Finance API.
- **Time Series Analysis**: Performs decomposition, volatility analysis, and trend detection.
- **Feature Engineering**: Creates custom features such as lag variables, moving averages, and RSI indicators.
- **Forecasting**: Implements **Prophet** for making 7-day future predictions.
- **Interactive Web Application**: Provides visualizations and real-time currency exchange rate predictions using **Streamlit**.

---

## Project Structure

```
📁 Currency-Rate-Prediction
│── 📄 main.py              # Core script for data processing and modeling
│── 📄 Project Report.pdf   # Detailed documentation of the project
│── 📄 README.md            # Project overview and instructions
│── 📄 requirements.txt     # Required dependencies
```

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/Currency-Rate-Prediction.git
cd Currency-Rate-Prediction
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On MacOS/Linux
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Project

### 1. Run the Prediction Model
Execute the Python script to fetch data, train models, and generate forecasts:

```bash
python main.py
```

### 2. Launch the Web Application
To run the Streamlit-based web app, execute:

```bash
streamlit run main.py
```

This will open the interactive dashboard in your browser.

---

## Model Details

The forecasting model is based on **Facebook Prophet**, which is tuned for:

- **Multiplicative Seasonality** (Yearly, Weekly, Daily)
- **Hyperparameter Tuning** for improved accuracy
- **Feature Engineering** (Lag Features, Moving Averages, RSI)

The model is trained using **90% historical data** and evaluated using **Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and Mean Absolute Percentage Error (MAPE).**

---

## Results

| Currency | MAPE (%) | RMSE | MAE |
|----------|---------|------|------|
| EUR/USD  | 0.08%   | 0.0014 | 0.008 |
| JPY/USD  | 0.87%   | 0.1311 | 0.1114 |
| INR/USD  | 0.05%   | 0.0440 | 0.0394 |
| CNY/USD  | 0.12%   | 0.0101 | 0.0085 |
| GBP/USD  | 0.12%   | 0.0014 | 0.0014 |

**Observations:**
- The model performs well for **INR, EUR, and GBP**, which show clear trends.
- JPY predictions have higher errors due to volatility and lack of a clear trend.

---

