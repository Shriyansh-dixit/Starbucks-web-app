import csv
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv("C:/Users/dixit/Desktop/Project 2025/Zentrix/Starbucks/file.env")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="starbucks"  # Hardcode for now, update .env later
    )

csv_files = {
    "Drinks.csv": "drink",
    "Food_items.csv": "food_item",
    "Merchandise.csv": "merchandise",
    "Coffee_at_home.csv": "coffee_at_home",
    "Ready_to_eat.csv": "ready_to_eat"
}

def load_csv_to_db():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE menu")

    for file_name, item_type in csv_files.items():
        try:
            with open(file_name, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    serial_code = row.get('code') or row.get('Code')
                    item_name = row.get('item_name') or row.get('Item_name')
                    price_raw = row.get('price') or row.get('Price')

                    if price_raw is None or price_raw.strip() == "":
                        print(f"Skipping row in {file_name}: Missing or empty price for {item_name}")
                        continue
                    try:
                        price = float(price_raw)
                    except ValueError:
                        print(f"Skipping row in {file_name}: Invalid price '{price_raw}' for {item_name}")
                        continue

                    category = row.get('category') or row.get('Category')
                    calories_raw = row.get('Calories Per Serve', None)
                    print(f"{file_name} - Calories raw: {calories_raw}")  # Debug output
                    calories_per_serve = None if calories_raw == '' else calories_raw
                    if calories_per_serve is not None:
                        try:
                            calories_per_serve = int(float(calories_raw))  # Convert to int, handle floats
                        except (ValueError, TypeError):
                            print(f"Skipping row in {file_name}: Invalid calories '{calories_raw}' for {item_name}")
                            continue
                    serving_size = row.get('Serving Size', None)

                    cursor.execute(
                        """
                        INSERT INTO menu (serial_code, item_name, price, item_type, category, calories_per_serve, serving_size)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            item_name=%s, price=%s, item_type=%s, category=%s, calories_per_serve=%s, serving_size=%s
                        """,
                        (serial_code, item_name, price, item_type, category, calories_per_serve, serving_size,
                         item_name, price, item_type, category, calories_per_serve, serving_size)
                    )
            print(f"Loaded {file_name} with item_type '{item_type}' successfully!")
        except FileNotFoundError:
            print(f"Error: {file_name} not found!")
        except Exception as e:
            print(f"Error loading {file_name}: {e}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    db.commit()
    cursor.close()
    db.close()

if __name__ == "__main__":
    load_csv_to_db()