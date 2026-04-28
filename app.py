from flask import Flask, jsonify, request, abort, render_template
from manager import PharmacyManager
from tables import Medicine, Customer
from exceptions import PharmacyError
import os

app = Flask(__name__, static_folder='static')
manager = PharmacyManager()

# Serve static files for the frontend
if not os.path.exists("static"):
    os.makedirs("static")

@app.route("/")
def root():
    return render_template('index.html')

@app.route("/inventory")
def get_inventory():
    return jsonify([
        {
            "name": m.name,
            "base_price": m.base_price,
            "final_price": m.get_price(),
            "quantity": m.quantity,
            "expiry_date": m.expiry_date.strftime("%Y-%m-%d"),
            "requires_prescription": m.requires_prescription,
            "is_expired": m.is_expired()
        } for m in manager.inventory
    ])

@app.route("/add_medicine", methods=['POST'])
def add_medicine():
    med = request.json
    new_med = Medicine(med['name'], med['base_price'], med['quantity'], med['expiry_date'], med.get('requires_prescription', False))
    manager.add_medicine(new_med)
    return jsonify({"status": "success", "medicine": med['name']})

@app.route("/sell", methods=['POST'])
def sell_medicine():
    sale = request.json
    customer = Customer(sale['customer_name'], sale['customer_phone'])
    try:
        receipt = manager.sell_medicine(
            sale['name'], 
            sale['quantity'], 
            customer, 
            sale.get('prescription_confirmed', False)
        )
        return jsonify({"status": "success", "receipt": receipt, "customer_debt": customer.balance})
    except PharmacyError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/report/expired")
def expired_report():
    expired = manager.get_expired_report()
    return jsonify([{"name": m.name, "expiry": m.expiry_date.strftime("%Y-%m-%d")} for m in expired])

@app.route("/sales_history")
def sales_history():
    return jsonify(manager.sales_history)

# Initial Data Setup
if not manager.inventory:
    initial_meds = [
        Medicine("Panadol", 10.0, 50, "2027-12-31", False),
        Medicine("Amoxicillin", 25.0, 20, "2026-05-20", True),
        Medicine("Old Syrum", 5.0, 5, "2024-01-01", False),
    ]
    for m in initial_meds:
        manager.add_medicine(m)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
