import json
import os
from datetime import datetime
from tables import Medicine, Customer
from exceptions import OutOfStockError, ExpiredProductError, PrescriptionRequiredError

class PharmacyManager:
    def __init__(self, data_file="inventory.json"):
        self.data_file = data_file
        self.inventory = [] 
        self.sales_history = []
        self.load_from_file()

    def add_medicine(self, medicine: Medicine):
        """Add a medicine object to the inventory."""
        self.inventory.append(medicine)
        self.save_to_file()

    def sell_medicine(self, name: str, qty: int, customer: Customer, prescription_confirmed: bool = False):
        """
        Processes a sale:
        - Checks availability
        - Checks expiry
        - Checks prescription requirement
        - Updates stock and customer debt
        """
        # Find medicine in inventory
        medicine = None
        for m in self.inventory:
            if m.name.lower() == name.lower():
                medicine = m
                break        
        if not medicine:
            raise ValueError(f"Medicine '{name}' not found in inventory.")

        # 1. Check Stock
        if medicine.quantity < qty:
            raise OutOfStockError(medicine.name, medicine.quantity)

        # 2. Check Expiry
        if medicine.is_expired():
            raise ExpiredProductError(medicine.name, medicine.expiry_date.strftime("%Y-%m-%d"))

        # 3. Check Prescription
        if medicine.requires_prescription and not prescription_confirmed:
            raise PrescriptionRequiredError(medicine.name)

        # Process Sale
        total_price = medicine.get_price() * qty
        medicine.update_stock(-qty)
        customer.add_debt(total_price)

        # Record Sale
        sale_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "medicine": medicine.name,
            "quantity": qty,
            "total_price": total_price,
            "customer": customer.name
        }
        self.sales_history.append(sale_record)
        
        self.save_to_file()
        return sale_record

    def get_expired_report(self):
        """Returns a list of expired medicines."""
        return [m for m in self.inventory if m.is_expired()]

    def save_to_file(self):
        """Saves current inventory and sales to a JSON file."""
        data = {
            "inventory": [
                {
                    "name": m.name,
                    "base_price": m.base_price,
                    "quantity": m.quantity,
                    "expiry_date": m.expiry_date.strftime("%Y-%m-%d"),
                    "requires_prescription": m.requires_prescription
                } for m in self.inventory
            ],
            "sales": self.sales_history
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_from_file(self):
        """Loads inventory and sales from the JSON file."""
        if not os.path.exists(self.data_file):
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Reconstruct inventory
                self.inventory = [
                    Medicine(
                        item['name'], 
                        item['base_price'], 
                        item['quantity'], 
                        item['expiry_date'], 
                        item['requires_prescription']
                    ) for item in data.get('inventory', [])
                ]
                self.sales_history = data.get('sales', [])
        except (json.JSONDecodeError, KeyError):
            self.inventory = []
            self.sales_history = []
