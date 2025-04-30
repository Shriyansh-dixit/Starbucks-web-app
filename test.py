import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv("C:/Users/dixit/Desktop/Project 2025/Zentrix/Starbucks/file.env")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

if __name__ == "__main__":
    try:
        db = get_db_connection()
        print("Connected successfully!")
        db.close()
    except mysql.connector.Error as err:
        print(f"Connection failed: {err}")