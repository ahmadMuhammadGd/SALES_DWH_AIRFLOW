from mongo_global_var import *
from mysql_dwh import dwh_init_tables, dwh_execute_SQL

def set_transform_mongo_invoices_view():
    pipeline = [
        {'$unwind': '$invoices'},
        {'$unwind': '$invoices.products'},
        
        {'$project':{
                '_id': 0,
                'first_name':               '$user.first_name',
                'sure_name':                '$user.sure_name',
                'username':                 '$user.username',
                'email':                    '$user.email',
                'phone_number':             '$user.phone_number',
                'invoice_id':               '$invoices.invoice_id',
                'payement_method':          '$invoices.payement_method',
                'product_name':             '$invoices.products.product_name',
                'product_line':             '$invoices.products.product_line',
                'product_description':      '$invoices.products.product_description',
                'price':                    '$invoices.products.price',
                'quantity':                 '$invoices.products.quantity',
                'date':                     '$invoices.date',
                'time':                     '$invoices.time'
            }
        }
    ]
    
    if transformed_ELT_view_name not in collection_names:
        db.create_collection(
            transformed_ELT_view_name,
            viewOn=collection_name,
            pipeline=pipeline)


def dwh_load_unwinded_document(host, user, password):
    dwh_init_tables(host, user, password)
    
    view = db[transformed_ELT_view_name]
    result = view.find()
    
    for record in result:
        for pair in MysqlMongoMap:
            targetQuery = f'''
            INSERT INTO {target_table_name}
                ({pair[0]}) 
            VALUE
                ({record[pair[1]]});
            '''
            dwh_execute_SQL(targetQuery)

#test
mysql_credentials = {
    "host": "mysql-db",
    "user": "root",
    "password": "root"
}
dwh_load_unwinded_document(**mysql_credentials)
    
