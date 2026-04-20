import uuid
from datetime import datetime

class Product:
    def __init__(self, name, base_price, quantity):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self._base_price = base_price
        self.quantity = int(quantity)

    @property
    def base_price(self):
        return self._base_price

    @base_price.setter
    def base_price(self, value):
        if value < 0:
            raise ValueError("Price cannot be negative.")
        self._base_price = float(value)

    def update_stock(self, amount: int):
        """Update stock quantity. Positive to add, negative to subtract."""
        if self.quantity + amount < 0:
            return False
        self.quantity += amount
        return True

    def get_price(self):
        """Returns the final price. Overridden by child classes."""
        return self._base_price

class Medicine(Product):
    def __init__(self, name: str, base_price: float, quantity: int, expiry_date: str, requires_prescription: bool = False):
        super().__init__(name, base_price, quantity)
        # Parse expiry date from string 'YYYY-MM-DD'
        self.expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
        self.requires_prescription = requires_prescription

    def is_expired(self):
        """Checks if the current date is past the expiry date."""
        return datetime.now() > self.expiry_date

    def get_price(self):
        """Returns final price with 5% medicine tax."""
        return self.base_price * 1.05

class Customer:
    def __init__(self, name: str, phone: str):
        self.name = name
        self.phone = phone
        self.__balance = 0.0

    @property
    def balance(self):
        return self.__balance

    def add_debt(self, amount: float):
        """Increases the customer's debt."""
        if amount > 0:
            self.__balance += float(amount)

    def pay_debt(self, amount: float):
        """Decreases the customer's debt."""
        if amount > 0:
            self.__balance = max(0.0, self.__balance - float(amount))
