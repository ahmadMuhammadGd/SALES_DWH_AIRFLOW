from faker import Faker
from faker.providers import BaseProvider
import random

class ProductProvider(BaseProvider):
    def product(self):
        products = [
            {"line": "Electronics", "product": "Smartphone", "price": 699.99},
            {"line": "Clothing", "product": "Jeans", "price": 49.99},
            {"line": "Food", "product": "Pizza", "price": 9.99}
        ]
        return random.choice(products)

class CustomerProvider(BaseProvider):
    def customer(self):
        customers = [
            {"firstname": "John", "lastname": "Doe", "email": "john.doe@example.com", "phone": "123-456-7890"},
            {"firstname": "Jane", "lastname": "Smith", "email": "jane.smith@example.com", "phone": "987-654-3210"},
            {"firstname": "Alice", "lastname": "Johnson", "email": "alice.johnson@example.com", "phone": "456-789-1234"}
        ]
        return random.choice(customers)

class BranchProvider(BaseProvider):
    def branch(self):
        branches = [
            {"branch": "A", "city": "New York", "salesmen": ["Tom Brown", "Harry White"]},
            {"branch": "B", "city": "Los Angeles", "salesmen": ["Chris Green", "James Black"]},
            {"branch": "C", "city": "Chicago", "salesmen": ["Sam Blue", "Jack Red"]}
        ]
        return random.choice(branches)

# Initialize Faker and add custom providers
FAKE = Faker()
FAKE.add_provider(ProductProvider)
FAKE.add_provider(CustomerProvider)
FAKE.add_provider(BranchProvider)
