import pandas as pd
from dags.src.data_processing import pd_cleaner
import json

class CSV_source_cleaner:
    def __init__(self, path):
        self.path = path
        self.status = 'pending'
        self.dataframe = pd.read_csv(self.path)
        self.cleandf = None
        self.json_logs = None
        self.error_log = []
        self.error_codes = {
            'duplicate':            1,
            'missing_value':        2,
            'invalid_email':        3,
            'invalid_phone':        4,
            'negative_value':       5,
            'invalid_date':         6,
            'invalid_time':         7,
            'invalid_person_name':  8,
            'invalid_invoice_id':   9,
            'invalid_price':        10,
            'invalid_quantity':     11,
        }
        self.table_schema = None
        self.clean()
        print(self.json_logs)
    def clean(self):
        cleaner = pd_cleaner(self.error_codes)
        
        df = self.dataframe.copy()
        df = cleaner.remove_duplicates(df, 'duplicate')
        
        crucial_columns = ["Invoice_ID", "Branch", "City", "First_name", "Last_name", "Email", 
                           "Phone_number", "product", "Product_line", "Unit_price", "Quantity", 
                           "Date", "Time", "Payment","Salesman_firstname", "Salesman_lastname"]
        
        df = cleaner.drop_missing_values(df, crucial_columns, 'missing_value')
        
        df = cleaner.validate_column_types(df, "Invoice_ID", int, 'invalid_invoice_id')
        df = cleaner.validate_column_types(df, "Unit_price", float, 'invalid_price')
        df = cleaner.validate_column_types(df, "Quantity", int, 'invalid_quantity')
        df = cleaner.validate_column_types(df, "Phone_number", str, 'invalid_quantity')
        df['Phone_number'] = df['Phone_number'].astype(str).str.replace('\.0$', '', regex=True).apply(lambda x: '+' + x)

        
        df = cleaner.validate_dates(df, "Date", None, 'invalid_date')
        df = cleaner.validate_dates(df, "Time", '%H:%M:%S', 'invalid_time')
        
        email_pattern = r"[^@]+@[^@]+\.[^@]+"
        df = cleaner.validate_regex(df, 'Email', email_pattern, 'invalid_email')
        
        phone_pattern = r"^\+?1?\d*$"
        df = cleaner.validate_regex(df, 'Phone_number', phone_pattern, 'invalid_phone')
        
        person_name_pattern = r"^[A-Za-z]+"
        df = cleaner.validate_regex(df, 'First_name', person_name_pattern, 'invalid_person_name')
        df = cleaner.validate_regex(df, 'Last_name', person_name_pattern, 'invalid_person_name')
        df = cleaner.validate_regex(df, 'Salesman_firstname', person_name_pattern, 'invalid_person_name')
        df = cleaner.validate_regex(df, 'Salesman_lastname', person_name_pattern, 'invalid_person_name')
        
        df = cleaner.filter_negative_values(df, ["Unit_price", "Quantity"])
        
        self.cleandf = df
        self.status = 'cleaned'
        self.json_logs = json.dumps(cleaner.error_log)
        self.table_schema = "\n".join([f'{column}\t-->\t{df[column].dtype}' for column in df.columns])
    
    def save_cleaned_data(self, output_path:str):
        if self.cleandf is not None:
            self.cleandf.to_csv(output_path, index=False)
        else:
            raise ValueError("Dataframe has not been cleaned. Call the clean method first.")

    def export_json_logs(self, output_path: str):
        with open(output_path, 'w') as f:
            json.dump(self.json_logs, f, indent=4)
    
    def export_table_schema(self, output_path:str):
        with open(output_path, 'w') as f:
            f.write(self.table_schema)
            
# Example usage:
# _PATH = "STAGES/LANDED/2024-06-20 17:56:33.772837.csv"
# cleaner = CSV_source_cleaner(_PATH)
# cleaner.clean()
# cleaner.save_cleaned_data("cleaned_data.csv")
# cleaner.export_json_logs("json_logs.json")
# cleaner.export_table_schema("schema.txt")
# print(cleaner.json_logs)
# print(cleaner.table_schema)
