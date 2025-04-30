import csv
import mysql.connector
from flask import Blueprint, request, jsonify, render_template, flash, Response
from dotenv import load_dotenv
import os
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv("C:/Users/dixit/Desktop/Project 2025/Zentrix/Starbucks/file.env")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="starbucks"
    )

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch categories (item_type values)
    cursor.execute("SELECT DISTINCT item_type FROM menu")
    categories = [row['item_type'] for row in cursor.fetchall()]
    print("Categories fetched:", categories)

    # Get date from query parameter or default to today
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    # Fetch recent orders for the selected date (default: last 10)
    cursor.execute(
        "SELECT * FROM orders WHERE order_date = %s ORDER BY order_time DESC, id DESC LIMIT 10",
        (selected_date,)
    )
    recent_orders = cursor.fetchall()

    if request.method == 'POST':
        items = request.form.getlist('items[]')
        if not items:
            flash("Please add at least one item!", "error")
        else:
            try:
                order_date = datetime.now().strftime('%Y-%m-%d')
                order_time = datetime.now().strftime('%H:%M:%S')
                group_id = int(datetime.now().timestamp())  # Unique group ID based on timestamp
                success_count = 0

                for item_str in items:
                    serial_code, quantity = item_str.split(':')
                    quantity = int(quantity)

                    cursor.execute(
                        "SELECT item_name, price, item_type FROM menu WHERE serial_code = %s",
                        (serial_code,)
                    )
                    item = cursor.fetchone()

                    if not item:
                        flash(f"Invalid serial code: {serial_code}", "error")
                        continue

                    for _ in range(quantity):
                        cursor.execute(
                            "INSERT INTO orders (serial_code, item_name, price, item_type, order_date, order_time, group_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (serial_code, item['item_name'], item['price'], item['item_type'], order_date, order_time, group_id)
                        )
                        success_count += 1

                db.commit()
                if success_count > 0:
                    flash(f"Added {success_count} item(s) successfully!", "success")
                    # Refresh recent orders for the current date
                    cursor.execute(
                        "SELECT * FROM orders WHERE order_date = %s ORDER BY order_time DESC, id DESC LIMIT 10",
                        (order_date,)
                    )
                    recent_orders = cursor.fetchall()

            except mysql.connector.Error as e:
                db.rollback()
                flash(f"Database error: {e}", "error")

    cursor.close()
    db.close()
    return render_template('test_index.html', categories=categories, recent_orders=recent_orders, selected_date=selected_date)

@bp.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    sql = "SELECT serial_code, item_name FROM menu WHERE serial_code REGEXP %s"
    params = [f".*{''.join(map(lambda x: f'[{x}]', query))}.*"]
    if category:
        sql += " AND item_type = %s"
        params.append(category)

    cursor.execute(sql, params)
    suggestions = [{"serial_code": row['serial_code'], "item_name": row['item_name']} for row in cursor.fetchall()]
    cursor.close()
    db.close()
    return jsonify(suggestions)

@bp.route('/api/orders_by_date', methods=['GET'])
def orders_by_date():
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Date is required"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM orders WHERE order_date = %s ORDER BY order_time DESC, id DESC LIMIT 10",
        (date,)
    )
    orders = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(orders)

@bp.route('/api/download_orders_pdf', methods=['GET'])
def download_orders_pdf():
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Date is required"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM orders WHERE order_date = %s ORDER BY order_time DESC, id DESC",
        (date,)
    )
    orders = cursor.fetchall()
    cursor.close()
    db.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Orders for {date}", styles['Heading1']))
    story.append(Spacer(1, 12))

    for order in orders:
        text = f"ID: {order['id']} | Serial: {order['serial_code']} | Name: {order['item_name']} | Price: ${order['price']} | Type: {order['item_type']} | Time: {order['order_date']} {order['order_time']} | Group: {order['group_id']}"
        story.append(Paragraph(text, styles['BodyText']))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return Response(
        buffer,
        mimetype='application/pdf',
        headers={"Content-Disposition": f"attachment;filename=orders_{date}.pdf"}
    )