from flask import Flask, render_template, request, jsonify
from logging.config import dictConfig
import joblib  # Для загрузки модели
import os
import numpy as np

# Логгирование
dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "service/flask.log",
                "formatter": "default",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["console", "file"]},
    }
)

app = Flask(__name__)

# === Загрузка модели ===
MODEL_PATH = '/Users/yanak/Projects/pabd25/models/linear_regression_model2.pkl'
model = None

try:
    model = joblib.load(MODEL_PATH)
    app.logger.info("Model loaded successfully.")
except Exception as e:
    app.logger.error(f"Failed to load model: {e}")

# === Вспомогательная функция предсказания ===
def predict_price(area: int) -> str:
    if model:
        input_data = np.array([[area]])
        prediction = model.predict(input_data)
        price = round(float(prediction[0]), 2)  # исходная цена
        millions = int(price // 1_000_000)
        thousands = int((price % 1_000_000) // 1_000)
        return f"{millions} млн {thousands} тыс"
    else:
        raise RuntimeError("Model is not loaded")

# === Маршруты ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/numbers', methods=['POST'])
def process_numbers():
    data = request.get_json()
    app.logger.info(f'Request data: {data}')

    try:
        filled_area = int(data['area'])
        predicted_price = predict_price(filled_area)
        app.logger.info(f'Predicted price: {predicted_price}')
        return jsonify({'Цена квартиры': predicted_price})
    except Exception as e:
        app.logger.error(f"Error during prediction: {e}")
        return jsonify({'error': 'Ошибка при обработке данных'}), 500

if __name__ == '__main__':
    app.run(debug=True)
