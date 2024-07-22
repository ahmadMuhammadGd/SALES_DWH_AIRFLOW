import pandas as pd
from faker_provider import *
import datetime

class FakeData:
    def __init__(self):
        self.product_info =                         None
        self.customer_info =                        None
        self.branch_info =                          None
        self.invoice_id =                           None
        self.branch =                               None
        self.city =                                 None
        self.salesman =                             None
        self.salesman_fname =                       None        
        self.salesman_lname =                       None
        self.first_name =                           None
        self.last_name =                            None
        self.email =                                None
        self.phone_number =                         None
        self.product_line =                         None
        self.product_name =                         None
        self.unit_price =                           None
        self.quantity =                             None
        self.date =                                 None
        self.time =                                 None
        self.payment_method =                       None    
        self.generate_fake_row()
    
    def generate_fake_row(self) -> dict:
        self.product_info =                         FAKE.product()
        self.customer_info =                        FAKE.customer()
        self.branch_info =                          FAKE.branch()
        self.invoice_id =                           int(random.randint(100, 6000))
        self.city =                                 self.branch_info["city"]
        self.branch =                               self.branch_info["branch"]
        self.salesman =                             random.choice(self.branch_info["salesmen"])
        self.salesman_fname, self.salesman_lname =  self.salesman.split(' ')
        self.first_name =                           self.customer_info["firstname"]
        self.last_name =                            self.customer_info["lastname"]
        self.email =                                self.customer_info["email"]
        self.phone_number =                         self.customer_info["phone"]
        self.product_line =                         self.product_info["line"]
        self.product_name =                         self.product_info["product"]
        self.unit_price =                           self.product_info["price"]
        self.quantity =                             random.randint(1, 10)
        self.date =                                 FAKE.date_between(start_date=datetime.date(2023, 1, 1))
        self.time =                                 FAKE.time(pattern='%H:%M:%S')
        self.payment_method =                       random.choice(['Cash', 'Credit Card', 'E-wallet'])

        return {
            "Invoice_ID":                           self.invoice_id,
            "Branch":                               self.branch,
            "City":                                 self.city,
            "First_name":                           self.first_name,
            "Last_name":                            self.last_name,
            "Salesman_firstname":                   self.salesman_fname,
            "Salesman_lastname":                    self.salesman_lname,
            "Email":                                self.email,
            "Phone_number":                         self.phone_number,
            "Product":                              self.product_name,
            "Product_line":                         self.product_line,
            "Unit_price":                           self.unit_price,
            "Quantity":                             self.quantity,
            "Date":                                 self.date,
            "Time":                                 self.time,
            "Payment":                              self.payment_method,
        }

class CSV_fake:
    def __init__(self, row_n):
        self.faker = FakeData()
        self.row_n = row_n
        self.df = self.generate_fake_csv()
         
    def generate_fake_csv(self) -> pd.DataFrame:
        columns = self.faker.generate_fake_row().keys()
        data_dict = {column: [] for column in columns}
        for _ in range(self.row_n):
            fake_row_dict = self.faker.generate_fake_row()
            for key, value in fake_row_dict.items():
                data_dict[key].append(value)

        return pd.DataFrame(data_dict)

class Json_fake:
    def __init__(self, n):
        self.faker = FakeData()
        self.n = n + 1
        self.data = self.generate_fake_json()
        
    def _get_user_info(self) -> dict:
        f = self.faker
        return {
                "first_name":                        f.first_name,
                "sure_name":                         f.last_name,
                "username":                          str(f.first_name + f.last_name),
                "email":                             f.email,
                "phone_number":                      f.phone_number
            }
        
    def _get_orders_info(self) -> list[dict]:
        result = []
        f = self.faker
        for _ in range (random.randint(1, 5)):
            f.generate_fake_row()
            result.append({
                    "product_name":                  f.product_name,
                    "product_line":                  f.product_line,
                    "product_description":           None,
                    "price":                         f.unit_price,
                    "quantity":                      f.quantity
            })
        
        return result
    
    def _fill_invoice_template(self, products) -> dict:
        return {
        "invoice_id":                   self.faker.invoice_id,
        "payement_method":              random.choice(['Credit Card', 'E-wallet']),
        "products":                     products,
        "date":                         self.faker.date,
        "time":                         self.faker.time
        }
        
    def generate_fake_json(self) -> list:
        result = []

        for _ in range(self.n):
            user_info = self._get_user_info()
            products = self._get_orders_info()
            invoice = self._fill_invoice_template(products)
            
            user_exists = [user for user in result if user["user"]["username"] == user_info["username"]]
            if user_exists:
                user_exists[0]["invoices"].append(invoice)
            else:
                result.append({
                    "user": user_info,
                    "invoices": [invoice]
                })

        return result

class JSONExporter:
    def __init__(self, data):
        self.data = data
    
    def to_json(self, file_path):
        json_data = self.data.to_json(orient='records', lines=True)
        with open(file_path, 'w') as file:
            file.write(json_data)
        print(f"Data successfully exported to {file_path} in JSON format.")

class CSVExporter:
    def __init__(self, data):
        self.data = data
    
    def to_csv(self, file_path):
        self.data.to_csv(file_path, index=False)
        print(f"Data successfully exported to {file_path} in CSV format.")