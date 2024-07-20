from pymongo import MongoClient

#mongo data
db_name = 'transactions'
collection_name = 'invoices'
transformed_ELT_view_name = 'invioce_view'

uri = "mongodb://root:example@localhost:27017/" #use if you are running in localhost
# uri = "mongodb://root:example@mongo:27017/"   #use if yout are running in docker compos

client = MongoClient(uri)
db = client[db_name]
collection = db[collection_name]
collection_names = db.list_collection_names()

#mongo staging destination
target_table_name = 'CSV_STAGING'
MysqlMongoMap = [
    ('invoice_id',      'invoice_id'        ),
    ('client_fname',    'first_name'        ),
    ('client_lname',    'sure_name'         ),
    ('client_email',    'email'             ),
    ('client_phone',    'phone_number'      ),
    ('product_name',    'product_name'      ),
    ('product_line',    'product_line'      ),
    ('product_price',   'price'             ),
    ('amount',          'quantity'          ),
    ('order_date',      'date'              ),
    ('order_time',      'time'              ),
    ('payment_method',  'payement_methos'   )
]