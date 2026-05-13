from datetime import datetime
from tables import Medicine, Customer
from exceptions import OutOfStockError, ExpiredProductError, PrescriptionRequiredError
from db_config import get_db_connection
import mysql.connector

class PharmacyManager:
    def __init__(self):
        self.ensure_tables_exist()

    def ensure_tables_exist(self):
        """Creates tables if they don't exist."""
        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor()
        
        # Medicines Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                base_price DECIMAL(10, 2) NOT NULL,
                quantity INT NOT NULL,
                expiry_date DATE NOT NULL,
                requires_prescription BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Customers Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                balance DECIMAL(10, 2) DEFAULT 0.0
            )
        """)
        
        # Sales Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                medicine_name VARCHAR(255) NOT NULL,
                quantity INT NOT NULL,
                total_price DECIMAL(10, 2) NOT NULL,
                customer_name VARCHAR(255) NOT NULL
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()

    def get_inventory(self):
        """Fetches all medicines from the database."""
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM medicines")
        rows = cursor.fetchall()
        
        inventory = []
        for row in rows:
            med = Medicine(
                row['name'], 
                float(row['base_price']), 
                row['quantity'], 
                row['expiry_date'].strftime("%Y-%m-%d"), 
                bool(row['requires_prescription'])
            )
            inventory.append(med)
        
        cursor.close()
        conn.close()
        return inventory

    def add_medicine(self, medicine: Medicine):
        """Add a medicine object to the database."""
        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor()
        
        # Check if medicine already exists to update quantity instead of adding new
        cursor.execute("SELECT id, quantity FROM medicines WHERE LOWER(name) = LOWER(%s)", (medicine.name,))
        result = cursor.fetchone()
        
        if result:
            new_qty = result[1] + medicine.quantity
            cursor.execute("UPDATE medicines SET quantity = %s WHERE id = %s", (new_qty, result[0]))
        else:
            cursor.execute("""
                INSERT INTO medicines (name, base_price, quantity, expiry_date, requires_prescription)
                VALUES (%s, %s, %s, %s, %s)
            """, (medicine.name, medicine.base_price, medicine.quantity, medicine.expiry_date.strftime("%Y-%m-%d"), medicine.requires_prescription))
        
        conn.commit()
        cursor.close()
        conn.close()

    def sell_medicine(self, name: str, qty: int, customer: Customer, prescription_confirmed: bool = False):
        """Processes a sale using the MySQL database."""
        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed.")
        
        cursor = conn.cursor(dictionary=True)
        
        # 1. Find medicine
        cursor.execute("SELECT * FROM medicines WHERE LOWER(name) = LOWER(%s)", (name,))
        med_data = cursor.fetchone()
        
        if not med_data:
            cursor.close()
            conn.close()
            raise ValueError(f"Medicine '{name}' not found in inventory.")

        medicine = Medicine(
            med_data['name'], 
            float(med_data['base_price']), 
            med_data['quantity'], 
            med_data['expiry_date'].strftime("%Y-%m-%d"), 
            bool(med_data['requires_prescription'])
        )

        # 2. Check Stock
        if medicine.quantity < qty:
            cursor.close()
            conn.close()
            raise OutOfStockError(medicine.name, medicine.quantity)

        # 3. Check Expiry
        if medicine.is_expired():
            cursor.close()
            conn.close()
            raise ExpiredProductError(medicine.name, medicine.expiry_date.strftime("%Y-%m-%d"))

        # 4. Check Prescription
        if medicine.requires_prescription and not prescription_confirmed:
            cursor.close()
            conn.close()
            raise PrescriptionRequiredError(medicine.name)

        # Process Sale
        total_price = medicine.get_price() * qty
        new_stock = medicine.quantity - qty
        
        # Update Stock
        cursor.execute("UPDATE medicines SET quantity = %s WHERE name = %s", (new_stock, medicine.name))
        
        # Update/Insert Customer and balance
        cursor.execute("SELECT * FROM customers WHERE LOWER(name) = LOWER(%s)", (customer.name,))
        cust_data = cursor.fetchone()
        
        if cust_data:
            new_balance = float(cust_data['balance']) + total_price
            cursor.execute("UPDATE customers SET balance = %s WHERE id = %s", (new_balance, cust_data['id']))
            customer.add_debt(total_price) # For consistency with the class instance
        else:
            cursor.execute("INSERT INTO customers (name, phone, balance) VALUES (%s, %s, %s)", 
                           (customer.name, customer.phone, total_price))
            customer.add_debt(total_price)

        # Record Sale
        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO sales (sale_date, medicine_name, quantity, total_price, customer_name)
            VALUES (%s, %s, %s, %s, %s)
        """, (sale_date, medicine.name, qty, total_price, customer.name))
        
        conn.commit()
        
        sale_record = {
            "date": sale_date,
            "medicine": medicine.name,
            "quantity": qty,
            "total_price": float(total_price),
            "customer": customer.name
        }
        
        cursor.close()
        conn.close()
        return sale_record

    def get_expired_report(self):
        """Returns a list of expired medicines from the database."""
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM medicines WHERE expiry_date < CURDATE()")
        rows = cursor.fetchall()
        
        expired = []
        for row in rows:
            med = Medicine(
                row['name'], 
                float(row['base_price']), 
                row['quantity'], 
                row['expiry_date'].strftime("%Y-%m-%d"), 
                bool(row['requires_prescription'])
            )
            expired.append(med)
        
        cursor.close()
        conn.close()
        return expired

    def get_sales_history(self):
        """Fetches sales history from the database."""
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT sale_date as date, medicine_name as medicine, quantity, total_price, customer_name as customer FROM sales ORDER BY sale_date DESC")
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            row['total_price'] = float(row['total_price'])
            history.append(row)
            
        cursor.close()
        conn.close()
        return history

