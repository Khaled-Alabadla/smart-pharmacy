from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from manager import PharmacyManager
from tables import Medicine, Customer
from exceptions import PharmacyError
import os

app = FastAPI(title="Smart Pharmacy Management System")
manager = PharmacyManager()

# Serve static files for the frontend
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models for API
class MedicineSchema(BaseModel):
    name: str
    base_price: float
    quantity: int
    expiry_date: str
    requires_prescription: bool = False

class SaleRequest(BaseModel):
    name: str
    quantity: int
    customer_name: str
    customer_phone: str
    prescription_confirmed: bool = False

@app.get("/")
def root():
    return {"message": "Welcome to the Smart Pharmacy Management API"}

@app.get("/inventory")
def get_inventory():
    return [
        {
            "name": m.name,
            "base_price": m.base_price,
            "final_price": m.get_price(),
            "quantity": m.quantity,
            "expiry_date": m.expiry_date.strftime("%Y-%m-%d"),
            "requires_prescription": m.requires_prescription,
            "is_expired": m.is_expired()
        } for m in manager.inventory
    ]

@app.post("/add_medicine")
def add_medicine(med: MedicineSchema):
    new_med = Medicine(med.name, med.base_price, med.quantity, med.expiry_date, med.requires_prescription)
    manager.add_medicine(new_med)
    return {"status": "success", "medicine": med.name}

@app.post("/sell")
def sell_medicine(sale: SaleRequest):
    customer = Customer(sale.customer_name, sale.customer_phone)
    try:
        receipt = manager.sell_medicine(
            sale.name, 
            sale.quantity, 
            customer, 
            sale.prescription_confirmed
        )
        return {"status": "success", "receipt": receipt, "customer_debt": customer.balance}
    except PharmacyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/report/expired")
def expired_report():
    expired = manager.get_expired_report()
    return [{"name": m.name, "expiry": m.expiry_date.strftime("%Y-%m-%d")} for m in expired]

@app.get("/sales_history")
def sales_history():
    return manager.sales_history

# Initial Data Setup
if not manager.inventory:
    initial_meds = [
        Medicine("Panadol", 10.0, 50, "2027-12-31", False),
        Medicine("Amoxicillin", 25.0, 20, "2026-05-20", True),
        Medicine("Old Syrum", 5.0, 5, "2024-01-01", False),
    ]
    for m in initial_meds:
        manager.add_medicine(m)
