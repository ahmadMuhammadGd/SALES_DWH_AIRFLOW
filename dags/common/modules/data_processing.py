import pandas as pd

class pd_cleaner:
    def __init__(self, error_codes):
        self.error_log = {}
        self.error_codes = error_codes
        
    def log_error(self, index, error_type):
        if index not in self.error_log:
            self.error_log[index] = []
        # self.error_log[index].append(self.error_codes[error_type])
        self.error_log[index].append(error_type)
    
    def remove_duplicates(self, df, error_code):
        duplicates = df.duplicated()
        for idx in df[duplicates].index:
            self.log_error(idx, error_code)
        df.drop_duplicates(inplace=True)
        return df
    
    def drop_missing_values(self, df, columns, error_code):
        for column in columns:
            missing = df[column].isna()
            for idx in df[missing].index:
                self.log_error(idx, error_code)
        df.dropna(subset=columns, inplace=True)
        return df
    
    def validate_column_types(self, df, column, dtype, error_code):
        try:
            df[column] = df[column].astype(dtype)
        except ValueError:
            for idx in df.index:
                self.log_error(idx, error_code)
        return df
    
    def validate_dates(self, df, column, date_format, error_code):
        try:
            df[column] = pd.to_datetime(df[column], format=date_format).dt.time if column == "Time" else pd.to_datetime(df[column])
        except ValueError:
            for idx in df.index:
                self.log_error(idx, error_code)
        return df
     
    def validate_regex(self, df, column, pattern, error_code):
        df[column] = df[column].astype(str).str.strip()
        
        invalid_records = ~df[column].str.contains(pattern)
        for idx in df[invalid_records].index:
            self.log_error(idx, error_code)
        
        return df[~invalid_records]

    
    def filter_negative_values(self, df, columns):
        for column in columns:
            invalid_values = df[column] <= 0
            for idx in df[invalid_values].index:
                self.log_error(idx, 'negative_value')
            df = df[df[column] > 0]
        return df