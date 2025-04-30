import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QComboBox, QLineEdit, QPushButton, QLabel, QListWidget, 
                             QTabWidget, QMessageBox)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFont
import mysql.connector
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from dotenv import load_dotenv
import os

load_dotenv("C:/Users/dixit/Desktop/Project 2025/Zentrix/Starbucks/file.env")

# Opt into future pandas behavior to avoid downcasting warning
pd.set_option('future.no_silent_downcasting', True)

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database="starbucks"
        )
    except mysql.connector.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to connect to MySQL: {e}")
        return None

class StarbucksApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Starbucks Order Pro")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("C:/Users/dixit/Desktop/Project 2025/Zentrix/Starbucks/desktop-app/starbucks_logo.jpg"))

        # Main widget and layout
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Stylish Starbucks theme
        self.setStyleSheet("""
            QMainWindow { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00704A, stop:1 #F5E8C7); 
            }
            QWidget { 
                font-family: 'Arial'; 
                color: #231F20; 
            }
            QPushButton { 
                background: #00704A; 
                color: white; 
                border-radius: 15px; 
                padding: 10px; 
                font-size: 16px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background: #004d33; 
            }
            QLineEdit, QComboBox { 
                border: 3px solid #00704A; 
                border-radius: 10px; 
                padding: 8px; 
                background: white; 
                font-size: 14px; 
            }
            QListWidget { 
                border: 2px solid #00704A; 
                border-radius: 10px; 
                background: #FFFFFF; 
                padding: 5px; 
            }
            QLabel { 
                font-size: 18px; 
                font-weight: bold; 
                color: #00704A; 
            }
            QTabWidget::pane { 
                border: 2px solid #00704A; 
                border-radius: 10px; 
                background: rgba(255, 255, 255, 0.95); 
            }
            QTabWidget::tab-bar { 
                alignment: center; 
            }
            QTabBar::tab { 
                background: #00704A; 
                color: white; 
                padding: 10px; 
                border-radius: 8px; 
                margin-right: 5px; 
            }
            QTabBar::tab:selected { 
                background: #004d33; 
            }
        """)

        # Left panel (Order Entry)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setStyleSheet("background: rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 20px;")

        # Logo and title
        logo_label = QLabel()
        logo_path = "C:/Users/dixit/Desktop/Project 2025/Zentrix/Starbucks/desktop-app/starbucks_icon.ico"
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(100, 100, Qt.KeepAspectRatio)
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label.setText("Starbucks")
            logo_label.setFont(QFont("Arial", 24, QFont.Bold))
        left_layout.addWidget(logo_label, alignment=Qt.AlignCenter)

        # Category dropdown
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        db = get_db_connection()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT DISTINCT item_type FROM menu")
            for row in cursor.fetchall():
                self.category_combo.addItem(row[0].capitalize().replace('_', ' '))
            cursor.close()
            db.close()
        self.category_combo.currentTextChanged.connect(self.fetch_suggestions)
        left_layout.addWidget(QLabel("Select Category"))
        left_layout.addWidget(self.category_combo)

        # Serial code input
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Type Serial Code (e.g., CPL)")
        self.suggestion_timer = QTimer()
        self.suggestion_timer.setSingleShot(True)
        self.suggestion_timer.timeout.connect(self.fetch_suggestions)
        self.serial_input.textChanged.connect(lambda: self.suggestion_timer.start(200))
        left_layout.addWidget(QLabel("Serial Code"))
        left_layout.addWidget(self.serial_input)

        # Suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.itemClicked.connect(self.select_suggestion)
        left_layout.addWidget(self.suggestions_list)

        # Quantity controls
        qty_layout = QHBoxLayout()
        self.qty_label = QLabel("1")
        minus_btn = QPushButton("➖")
        minus_btn.clicked.connect(lambda: self.change_quantity(-1))
        plus_btn = QPushButton("➕")
        plus_btn.clicked.connect(lambda: self.change_quantity(1))
        self.animate_button(minus_btn)
        self.animate_button(plus_btn)
        qty_layout.addWidget(minus_btn)
        qty_layout.addWidget(self.qty_label, alignment=Qt.AlignCenter)
        qty_layout.addWidget(plus_btn)
        left_layout.addWidget(QLabel("Quantity"))
        left_layout.addLayout(qty_layout)

        # Add item button
        self.add_btn = QPushButton("Add to Order")
        self.add_btn.clicked.connect(self.add_item)
        self.animate_button(self.add_btn)
        left_layout.addWidget(self.add_btn)

        # Added items list
        self.items_list = QListWidget()
        left_layout.addWidget(QLabel("Your Order"))
        left_layout.addWidget(self.items_list)

        # Submit button
        self.submit_btn = QPushButton("Submit Order")
        self.submit_btn.clicked.connect(self.submit_order)
        self.animate_button(self.submit_btn)
        left_layout.addWidget(self.submit_btn)

        # Right panel (Tabs: Orders + Dashboard)
        right_panel = QTabWidget()
        right_panel.setStyleSheet("background: rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 20px;")

        # Orders tab
        orders_widget = QWidget()
        orders_layout = QVBoxLayout(orders_widget)
        self.orders_list = QListWidget()
        orders_layout.addWidget(QLabel("Recent Orders"))
        orders_layout.addWidget(self.orders_list)
        right_panel.addTab(orders_widget, "Orders")

        # Dashboard tab (Heatmap)
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        self.update_heatmap()  # Initial heatmap setup
        dashboard_layout.addWidget(self.heatmap_canvas)
        right_panel.addTab(dashboard_widget, "Dashboard")

        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        # Initialize state
        self.items = []
        self.update_orders()

    def animate_button(self, button):
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(100)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        button.clicked.connect(lambda: self.start_button_animation(button, animation))

    def start_button_animation(self, button, animation):
        original = button.geometry()
        animation.setStartValue(original)
        animation.setEndValue(original.adjusted(-5, -5, 5, 5))
        animation.start()

    def fetch_suggestions(self):
        query = self.serial_input.text().strip()
        category = self.category_combo.currentText().lower().replace(' ', '_')
        self.suggestions_list.clear()
        if not query:
            return
        db = get_db_connection()
        if not db:
            return
        cursor = db.cursor(dictionary=True)
        sql = "SELECT serial_code, item_name FROM menu WHERE serial_code LIKE %s"
        params = [f"%{query}%"]
        if category != "all categories":
            sql += " AND item_type = %s"
            params.append(category)
        try:
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                self.suggestions_list.addItem(f"{row['serial_code']} - {row['item_name']}")
        except mysql.connector.Error as e:
            QMessageBox.warning(self, "Error", f"Database query failed: {e}")
        finally:
            cursor.close()
            db.close()

    def select_suggestion(self, item):
        self.serial_input.setText(item.text().split(' - ')[0])
        self.suggestions_list.clear()

    def change_quantity(self, delta):
        qty = max(1, int(self.qty_label.text()) + delta)
        self.qty_label.setText(str(qty))

    def add_item(self):
        serial = self.serial_input.text().strip()
        qty = int(self.qty_label.text())
        if not serial:
            QMessageBox.warning(self, "Error", "Please enter a serial code!")
            return
        db = get_db_connection()
        if not db:
            return
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT item_name FROM menu WHERE serial_code = %s", (serial,))
        result = cursor.fetchone()
        if result:
            self.items.append((serial, qty))
            self.items_list.addItem(f"{serial} - {result['item_name']} - Qty: {qty}")
            self.serial_input.clear()
            self.qty_label.setText("1")
        else:
            QMessageBox.warning(self, "Error", "Invalid serial code!")
        cursor.close()
        db.close()

    def submit_order(self):
        if not self.items:
            QMessageBox.warning(self, "Error", "Add at least one item!")
            return
        db = get_db_connection()
        if not db:
            return
        cursor = db.cursor()
        order_date = datetime.now().strftime('%Y-%m-%d')
        order_time = datetime.now().strftime('%H:%M:%S')
        group_id = int(datetime.now().timestamp())
        try:
            for serial, qty in self.items:
                cursor.execute("SELECT item_name, price, item_type FROM menu WHERE serial_code = %s", (serial,))
                item = cursor.fetchone()
                for _ in range(qty):
                    cursor.execute(
                        "INSERT INTO orders (serial_code, item_name, price, item_type, order_date, order_time, group_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (serial, item[0], float(item[1]), item[2], order_date, order_time, group_id)  # Ensure price is float
                    )
            db.commit()
            QMessageBox.information(self, "Success", "Order submitted successfully!")
            self.items.clear()
            self.items_list.clear()
            self.update_orders()
            self.update_heatmap()
        except mysql.connector.Error as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to submit order: {e}")
        finally:
            cursor.close()
            db.close()

    def update_orders(self):
        self.orders_list.clear()
        db = get_db_connection()
        if not db:
            return
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orders ORDER BY order_date DESC, order_time DESC LIMIT 10")
        orders = cursor.fetchall()
        if orders:
            grouped = {}
            for order in orders:
                group_id = order['group_id'] or 0
                if group_id not in grouped:
                    grouped[group_id] = []
                grouped[group_id].append(order)
            for group_id, group_orders in grouped.items():
                self.orders_list.addItem(f"Order at: {group_orders[0]['order_date']} {group_orders[0]['order_time']} (Group: {group_id})")
                for order in group_orders:
                    self.orders_list.addItem(f"  {order['serial_code']} - {order['item_name']} - ${order['price']}")
        else:
            self.orders_list.addItem("No recent orders")
        cursor.close()
        db.close()

    def update_heatmap(self):
        db = get_db_connection()
        if not db:
            self.heatmap_canvas = QLabel("Database unavailable")
            return
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT order_date, order_time, price FROM orders")
        data = cursor.fetchall()
        cursor.close()
        db.close()

        if not data:
            self.heatmap_canvas = QLabel("No data for heatmap")
            return

        df = pd.DataFrame(data)
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['DayOfWeek'] = df['order_date'].dt.day_name()
        df['Hour'] = df['order_time'].dt.components['hours']  # Handle timedelta64[ns]
        df['price'] = pd.to_numeric(df['price'], errors='coerce')  # Convert price to float
        df['TimeCategory'] = pd.cut(
            df['Hour'], 
            bins=[0, 9, 12, 16, 19, 22], 
            labels=['Morning', 'Noon', 'Evening', 'Night', 'Late Night'], 
            right=False,
            include_lowest=True
        )

        pivot = df.pivot_table(
            values='price', 
            index='DayOfWeek', 
            columns='TimeCategory', 
            aggfunc='sum', 
            fill_value=0,
            observed=False  # Silence observed warning
        ).reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(pivot, annot=True, fmt='.2f', cmap='Greens', ax=ax)
        ax.set_title("Sales Heatmap", fontsize=16, color="#00704A")
        self.heatmap_canvas = FigureCanvas(fig)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = StarbucksApp()
    window.show()
    sys.exit(app.exec_())