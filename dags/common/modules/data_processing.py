import pandas as pd

class Logger:
    def __init__(self, format_func=None):
        self.error_log = []
        self.format_func = format_func if format_func else self.default_format

    def default_format(self, index, column, error_type):
        return {'index': index, 'column': column, 'error_type': error_type}

    def log_error(self, index, column, error_type):
        self.error_log.append(self.format_func(index, column, error_type))

    def get_logs(self):
        return self.error_log

class pd_cleaner:
    def __init__(self):
        self.logger = Logger()

    def remove_duplicates(self, df, error_code):
        duplicates = df.duplicated()
        for idx in df[duplicates].index:
            self.logger.log_error(idx, None, error_code)
        df.drop_duplicates(inplace=True)
        return df

    def drop_missing_values(self, df, columns, error_code):
        for column in columns:
            missing = df[column].isna()
            for idx in df[missing].index:
                self.logger.log_error(idx, column, error_code)
        df.dropna(subset=columns, inplace=True)
        return df

    def validate_column_types(self, df, column, dtype, error_code):
        try:
            df[column] = df[column].astype(dtype)
        except ValueError:
            invalid = df[~df[column].apply(lambda x: isinstance(x, dtype)).astype(bool)]
            for idx in invalid.index:
                self.logger.log_error(idx, column, error_code)
            df = df.drop(invalid.index)
        return df

    def validate_dates(self, df, column, date_format, error_code):
        try:
            if column == "Time":
                df[column] = pd.to_datetime(df[column], format=date_format).dt.time
            else:
                df[column] = pd.to_datetime(df[column], format=date_format)
        except:
            invalid_dates = df[~df[column].apply(lambda x: pd.to_datetime(x, format=date_format, errors='coerce')).notna()]
            for idx in invalid_dates.index:
                self.logger.log_error(idx, column, error_code)
            df = df.drop(invalid_dates.index)
        return df

    def validate_regex(self, df, column, pattern, error_code):
        df[column] = df[column].astype(str).str.strip()
        invalid_records = ~df[column].str.contains(pattern)
        for idx in df[invalid_records].index:
            self.logger.log_error(idx, column, error_code)
        return df[~invalid_records]

    def filter_negative_values(self, df, columns):
        for column in columns:
            invalid_values = df[column] <= 0
            for idx in df[invalid_values].index:
                self.logger.log_error(idx, column, 'negative_value')
            df = df[df[column] > 0]
        return df