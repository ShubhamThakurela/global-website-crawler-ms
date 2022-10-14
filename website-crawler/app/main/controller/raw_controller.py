import os
from flask import request, send_file, abort
from flask_restplus import Resource
from werkzeug.datastructures import FileStorage
from ..util.dto import RawDto
from datetime import datetime
from ..service.mailer_service import MailUtilities
from ..service.raw_service import crawl_by_url, crawl_by_file, get_external_urls
from ..service.constant_service import ConstantService
import logging
from app.main.util.my_thread import execute


api = RawDto.api
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage)


@api.route('/externalLinks')
class RawCrawlExternalUrlsController(Resource):
    @api.doc(params={
        'url': {'description': 'website url', 'in': 'query', 'type': 'str'}
    })
    def get(self):
        url = request.args.get('url')
        return {
            "status": True,
            "message": "Congratulations! Your website url crawled for external links successfully.",
            "result": get_external_urls(url)
        }


@api.route('/crawlUrl')
class RawCrawlUrlController(Resource):
    @api.doc(params={
        'url': {'description': 'website url', 'in': 'query', 'type': 'str'},
        'internal_page': {'description': 'Specify whether internal page need to scrap or not', 'in': 'query', 'type': 'boolean', 'default': 'true'},
        'internal_page_limit': {'description': 'Specify limit of internal page to scrap', 'in': 'query', 'type': 'int'}
    })
    def get(self):
        url = request.args.get('url')
        internal_page = True
        if 'internal_page' in request.args:
            internal_page = True if request.args.get('internal_page') == 'true' else False

        internal_page_limit = 100
        if 'internal_page_limit' in request.args:
            internal_page_limit = request.args.get('internal_page_limit')

        website_data = crawl_by_url(url, internal_page, internal_page_limit)
        return {
            "status": True,
            "message": "Congratulations! Your website url crawled successfully.",
            "result": website_data
        }


@api.route('/crawlUrls')
class RawCrawlUrlsController(Resource):
    @api.doc(params={
        'internal_page': {'description': 'Specify whether internal page need to scrap or not', 'in': 'query', 'type': 'boolean', 'default': 'true'},
        'internal_page_limit': {'description': 'Specify limit of internal page to scrap', 'in': 'query', 'type': 'int'},
        'urls': {
        'description': 'website urls',
        'in': 'body',
        'type': 'json',
        'example': {"urls": ["website_url1", "website_url2"]}
    }})
    def post(self):
        internal_page = True
        if 'internal_page' in request.args:
            internal_page = True if request.args.get('internal_page') == 'true' else False

        internal_page_limit = 100
        if 'internal_page_limit' in request.args:
            internal_page_limit = request.args.get('internal_page_limit')

        data = request.get_json()
        website_data_list = []
        for url in data['urls']:
            website_data_list.append(crawl_by_url(url, internal_page, internal_page_limit))

        return {
            "status": True,
            "message": "Congratulations! Your list of website urls crawled successfully.",
            "result": website_data_list
        }


@api.route('/crawlFile')
@api.expect(upload_parser)
class RawCrawlFileController(Resource):
    @api.doc(params={
        'internal_page': {'description': 'Specify whether internal page need to scrap or not', 'in': 'query', 'type': 'boolean', 'default': 'true'},
        'internal_page_limit': {'description': 'Specify limit of internal page to scrap', 'in': 'query', 'type': 'int'},
        'check_history': {'description': 'Specify whether check history or not', 'in': 'query', 'type': 'boolean', 'default': 'false'},
        'month_history': {'description': 'Specify limit of Days back to check history', 'in': 'query', 'type': 'int'},
        'email_id': {'description': 'Specify Email_id', 'in': 'query', 'type': 'string'}
    })
    def post(self):
        if 'file' not in request.files:
            return {
                "status": False,
                "message": "Sorry! file not passed."
            }
        file = request.files['file']

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return {
                "status": False,
                "message": "Sorry! file not passed.",
            }

        check_history = False
        if 'check_history' in request.args:
            check_history = False if request.args.get('check_history') == 'false' else True

        internal_page = True
        if 'internal_page' in request.args:
            internal_page = True if request.args.get('internal_page') == 'true' else False

        internal_page_limit = 100
        if 'internal_page_limit' in request.args:
            internal_page_limit = request.args.get('internal_page_limit')

        month_history = 2
        if 'month_history' in request.args:
            month_history = request.args.get('month_history')

        email_id = None
        if 'email_id' in request.args:
            email_id = request.args.get('email_id')

        now = datetime.now()
        dt_start = now.strftime("%d/%m/%Y %H:%M:%S")

        try:
            file_path = ConstantService.data_in_path() + '/' + file.filename
            out_path = ConstantService.fetched_scraped_data()
            file.save(file_path)
            history_path = ConstantService.fetched_scraped_histroy()
            output_file_name = execute(check_history, month_history, history_path, file_path, out_path, internal_page, internal_page_limit)
            download_link = "http://" + ConstantService.server_host() + "/raw/download?output_file_name=" + output_file_name
            if email_id is not None:
                MailUtilities.send_success_notification(email_id, download_link, dt_start)
            if len(output_file_name) == 0:
                return {
                    "status": False,
                    "message": "Sorry! file list empty."
                }
            else:
                return {
                    "status": True,
                    "message": "Congratulations! Your list of website urls crawled successfully.",
                    "download_link": "http://" + ConstantService.server_host() + "/raw/download?output_file_name=" + output_file_name
                }

        except Exception as e:
            print(str(e))
            logging.error(str(e))
            if email_id is not None:
                MailUtilities.send_failed_notification(email_id, str(e), dt_start)



@api.route('/download')
class RawDownloadController(Resource):
    @api.doc(params={'output_file_name': {'description': 'website crawled data output file name', 'in': 'query', 'type': 'str'}})
    def get(self):
        output_file_name = request.args.get('output_file_name')
        out_file_path = os.path.join(ConstantService.data_processed_path(), output_file_name)
        if os.path.exists(out_file_path):
            return send_file(out_file_path, as_attachment=True)

        abort(404, description="Crawled data not found")
