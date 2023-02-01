import logging
import os
import re
import traceback
import pandas as pd
from flask import jsonify
from ..database.connection import scrapping_orm


class scrappingservice(object):
    @staticmethod
    def get_details(query_dict):
        try:
            data = scrapping_orm.fetch_complete_details(query_dict)
            result = []
            for i in data:
                result.append({
                    'company_id': i[0],
                    'company_url': i[1],
                    'company_file_name': i[2],
                    'http_code': i[3],
                    'status': i[8],
                    'Dt': str(i[7])
                })
            return result
        except Exception as e:
            print(str(traceback.format_exc()))
            logging.error(str(e))
            response = {
                "Status": False,
                "Message": "Sorry an error occurred",
                "Error": str(e),
                "Code": 500,
            }
            return jsonify(response)

    @staticmethod
    def writing_data_to_file(query_dict):
        try:
            data = scrapping_orm.fetch_complete_details(query_dict)
            return data
        except Exception as e:
            print(str(traceback.format_exc()))
            logging.error(str(e))
            response = {
                "Status": False,
                "Message": "Sorry an error occurred",
                "Error": str(e),
                "Code": 500,
            }
            return jsonify(response)

    @staticmethod
    def insert_data(result_data):
        try:
            df = pd.DataFrame(result_data)
            return df
        except Exception as e:
            print(str(traceback.format_exc()))
            logging.error(str(e))

    @staticmethod
    def data_to_file(file_data, out_path):
        try:
            file_path = out_path + '/'
            file_name = "scrapping_history"
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            file_data.rename(columns={
                0: 'Company_id', 1: 'Company_urls', 2: 'Company_file_name',
                3: 'http_code', 4: 'Page_counts', 5: 'Menu_count', 6: 'Start_Dt', 8: 'status',
            }, inplace=True)
            file_data.to_csv(file_path + file_name + '.csv', index=False)
            file_save_name = file_name + ".csv"

            return file_save_name
        except Exception as e:
            print(str(traceback.format_exc()))
            logging.error(str(e))
