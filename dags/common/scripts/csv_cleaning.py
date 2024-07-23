import pandas as pd
from common.modules.data_processing import pd_cleaner
import json

class CSV_source_cleaner:
    def __init__(self, path):
        self.path = path
        self.status = 'pending'
        self.dataframe = pd.read_csv(self.path)
        self.cleaner = pd_cleaner()
        self.cleandf = None
        self.clean()
    
    def clean(self):
        
        df = self.dataframe.copy()
        df = self.cleaner.remove_duplicates(df, 'duplicate')
        
        crucial_columns = ["Invoice_ID", "Branch", "City", "First_name", "Last_name", "Email", 
                           "Phone_number", "Product", "Product_line", "Unit_price", "Quantity", 
                           "Date", "Time", "Payment","Salesman_firstname", "Salesman_lastname"]
        
        df = self.cleaner.drop_missing_values(df, crucial_columns, 'missing_value')

        df = self.cleaner.validate_column_types(df, "Invoice_ID", int, 'invalid_invoice_id')
        df = self.cleaner.validate_column_types(df, "Unit_price", float, 'invalid_price')
        df = self.cleaner.validate_column_types(df, "Quantity", int, 'invalid_quantity')
        df = self.cleaner.validate_column_types(df, "Phone_number", str, 'invalid_quantity')
        df['Phone_number'] = df['Phone_number'].astype(str).str.replace('\.0$', '', regex=True).apply(lambda x: '+' + x)

        
        df = self.cleaner.validate_dates(df, "Date", None, 'invalid_date')
        df = self.cleaner.validate_dates(df, "Time", '%H:%M:%S', 'invalid_time')
        
        email_pattern = r"[^@]+@[^@]+\.[^@]+"
        df = self.cleaner.validate_regex(df, 'Email', email_pattern, 'invalid_email')
        
        phone_pattern = r"^\+?1?\d*$"
        df['Phone_number'] = df['Phone_number'].map(lambda x: x.replace('-', '').replace(' ', ''))
        df = self.cleaner.validate_regex(df, 'Phone_number', phone_pattern, 'invalid_phone')
        
        person_name_pattern = r"^[A-Za-z]+"
        df = self.cleaner.validate_regex(df, 'First_name', person_name_pattern, 'invalid_person_name')
        df = self.cleaner.validate_regex(df, 'Last_name', person_name_pattern, 'invalid_person_name')
        df = self.cleaner.validate_regex(df, 'Salesman_firstname', person_name_pattern, 'invalid_person_name')
        df = self.cleaner.validate_regex(df, 'Salesman_lastname', person_name_pattern, 'invalid_person_name')
        
        df = self.cleaner.filter_negative_values(df, ["Unit_price", "Quantity"])
        
        self.cleandf = df
    
    def save_cleaned_data(self, output_path:str):
        if self.cleandf is not None:
            self.cleandf.to_csv(output_path, index=False)
        else:
            raise ValueError("Dataframe has not been cleaned. Call the clean method first.")


