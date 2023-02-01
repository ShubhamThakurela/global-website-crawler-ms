import os
import shutil
import traceback
import logging
from flask import request, jsonify
from flask_restplus import Resource
from werkzeug.datastructures import FileStorage
from ..util.dto import TargetBasedDto
from ..service.constant_service import ConstantService
from ..service.mailer_service import MailUtilities
from ..service.scrappig_service import scrappingservice
import time
from datetime import datetime

api = TargetBasedDto.api
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage)


@api.route('/fetch_all_scrapped_companies_info')
class TargetBasedCrawlUrlController(Resource):
    @api.doc(params={'start_date': {'description': '%Y-%m-%d', 'in': 'query', 'type': 'str'},
                     'Http_status_code': {'description': '400,401,402,403,500,503,506', 'in': 'query', 'type': 'str'},
                     })
    def get(self):
        try:
            data = {
                "start_dt": request.args.get('start_date'),
                'response_code': request.args.get('Http_status_code')
            }
            dict_len = 0
            query_dict = {}
            for key, value in data.items():
                if value is not None and not value.startswith(" ") and value.lower() != "none" and value != "":
                    query_dict[key] = value
                    dict_len += 1
            if dict_len > 0:
                result = scrappingservice.get_details(query_dict)
                if result:
                    response = {
                        "Code": 200,
                        "Message": "successfully fetch the record",
                        "Result": result,
                        "Status": True
                    }
                    return jsonify(response)
                else:
                    response = {"Status": False,
                                "Message": "No data in database",
                                "Code": 404,
                                }
                    return jsonify(response)
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


@api.route('/get_history_in_file')
class TargetBasedDownloadController(Resource):
    @api.doc(params={'start_date': {'description': '%Y-%m-%d', 'in': 'query', 'type': 'str'},
                     'Http_status_code': {'description': '400,401,402,403,500,503,506', 'in': 'query', 'type': 'str'},
                     'email_id': {'description': 'Specify Email_id', 'in': 'query', 'type': 'string'}
                     })
    def get(self):
        try:
            data = {
                "start_dt": request.args.get('start_date'),
                'response_code': request.args.get('Http_status_code')
            }
            start_time = time.time()
            email_id = None
            if 'email_id' in request.args:
                email_id = request.args.get('email_id')
            now = datetime.now()
            dt_start = now.strftime("%d/%m/%Y %H:%M:%S")
            """"file store_path"""
            out_path = ConstantService.data_out_path()
            query_dict = {}
            for key, value in data.items():
                query_dict[key] = value

            result_data = scrappingservice.writing_data_to_file(query_dict)
            """"Insert data to dataframe"""
            file_data = scrappingservice.insert_data(result_data)
            """"Write dataframe to excel"""
            data_file = scrappingservice.data_to_file(file_data, out_path)

            end_time = time.time()
            download_link = "http://" + ConstantService.server_host() + "/Download/download_data_file?output_file_name=" + data_file
            # if email_id is not None:
            # mail_status = MailUtilities.send_success_notification(email_id, download_link, dt_start)

            # if mail_status == "Email has been sent":
            response = {
                "Status": True,
                "Message": "Your Scrapping History Crawled Successfully Completed",
                "Processed_Time": '{:.3f} sec'.format(end_time - start_time),
                "Download_link": "http://" + ConstantService.server_host() + "/Download/download_data_file?output_file_name=" + data_file,
                "Mail_sent_id": email_id,
                # "Mail_status": mail_status
            }
            return jsonify(response)
            #
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
