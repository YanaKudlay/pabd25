import argparse
from flask import Flask, render_template, request, jsonify
from logging.config import dictConfig
import joblib
import numpy as np

# Настройка логирования
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

# Путь к модели по умолчанию
DEFAULT_MODEL_PATH = "models/decision_tree_reg_1.pkl"
model = None

def format_price(price: float) -> str:
    """Форматирует цену в строку вида 'X млн Y тыс'"""
    millions = int(price // 1_000_000)
    thousands = int((price % 1_000_000) // 1_000)
    return f"{millions} млн {thousands} тыс"

# Загрузка модели
def load_model(path):
    global model
    try:
        model = joblib.load(path)
        app.logger.info(f"Model loaded from {path}")
    except Exception as e:
        app.logger.error(f"Failed to load model: {e}")
        model = None

# Главная страница с формой
@app.route("/")
def index():
    return render_template("index.html")

# Обработка POST-запроса с данными формы
@app.route("/api/numbers", methods=["POST"])
def process_numbers():
    data = request.get_json()
    app.logger.info(f"Request data: {data}")

    try:
        total_meters = float(data["area"])
        floors_count = int(data["total_floors"])
        rooms = int(data["rooms"])
        floor = int(data["floor"])

        rooms_1 = rooms == 1
        rooms_2 = rooms == 2
        rooms_3 = rooms == 3
        first_floor = floor == 1
        last_floor = floor == floors_count

        if model is None:
            raise RuntimeError("Model is not loaded")

        price_pred = model.predict(
            [[
                total_meters,
                floors_count,
                rooms_1,
                rooms_2,
                rooms_3,
                first_floor,
                last_floor,
            ]]
        )[0]

        price_str = format_price(price_pred)
        app.logger.info(f"Predicted price: {price_str}")

        return jsonify({"status": "success", "price": price_str})

    except (ValueError, KeyError) as e:
        app.logger.error(f"Error parsing input data: {e}")
        return jsonify({"status": "error", "message": "Ошибка парсинга данных"}), 400
    except Exception as e:
        app.logger.error(f"Prediction error: {e}")
        return jsonify({"status": "error", "message": "Ошибка при предсказании"}), 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app for price prediction")
    parser.add_argument(
        "-m", "--model", default=DEFAULT_MODEL_PATH, help="Path to the model file"
    )
    args = parser.parse_args()

    load_model(args.model)
    app.run(debug=True)
