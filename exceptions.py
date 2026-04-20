class PharmacyError(Exception):
    """Base exception class for Pharmacy Management System."""
    pass

class OutOfStockError(PharmacyError):
    """Raised when the requested quantity is not available in stock."""
    def __init__(self, medicine_name, available):
        self.message = f"Error: '{medicine_name}' is out of stock. Available quantity: {available}."
        super().__init__(self.message)

class ExpiredProductError(PharmacyError):
    """Raised when attempting to sell an expired product."""
    def __init__(self, medicine_name, expiry_date):
        self.message = f"Error: '{medicine_name}' has expired on {expiry_date}."
        super().__init__(self.message)

class PrescriptionRequiredError(PharmacyError):
    """Raised when a prescription is required but not confirmed."""
    def __init__(self, medicine_name):
        self.message = f"Error: '{medicine_name}' requires a medical prescription."
        super().__init__(self.message)
