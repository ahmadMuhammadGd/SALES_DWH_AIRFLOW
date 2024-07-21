from common.global_vars.mongo_global_var import *
from common.modules.dwhInterface import dwh_execute_SQL

def set_transform_mongo_invoices_view() -> None:
    client_helper = MongoDBclientData()
    collection_names = client_helper.collection_names
    db = client_helper.db
    
    if transformed_ELT_view_name in collection_names:
        return
    
    pipeline = [
        {'$unwind': '$invoices'},
        {'$unwind': '$invoices.products'},
        {
            '$addFields': {
                'salesman_fname': {
                    '$ifNull':              ['$salesman_fname', 'online']
                },
                'branch_name': {
                    '$ifNull':              ['$branch_name', 'online']
                }
            }
        },
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
                'time':                     '$invoices.time',
                'branch_name':              '$branch_name',
                'salesman_fname':           '$salesman_fname',
            }
        }
    ]
    db.create_collection(
        transformed_ELT_view_name,
        viewOn=collection_name,
        pipeline=pipeline)


def dwh_stage_unwinded_document(host, user, password, target_table_name):
    client_helper = MongoDBclientData()
    db = client_helper.db
    
    view = db[transformed_ELT_view_name]
    result = view.find()
    
    data_to_insert = [
        tuple(record.get(pair[1]) for pair in MysqlMongoMap)
        for record in result
    ]
    target_query = f'''
            USE DWH;
            INSERT INTO {target_table_name} ({", ".join([pair[0] for pair in MysqlMongoMap])})
            VALUES ({", ".join(["%s" for _ in MysqlMongoMap])})
            '''
    dwh_execute_SQL(target_query, host, user, password, params=data_to_insert)
