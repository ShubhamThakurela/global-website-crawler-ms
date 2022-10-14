import os
import sys
from flask import request, send_file, abort
from flask_restplus import Resource
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from ..util.dto import TargetBasedDto
from ..service.raw_service import crawl_by_url, crawl_by_file
from ..service.constant_service import ConstantService

api = TargetBasedDto.api
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage)


@api.route('/crawlUrl')
class TargetBasedCrawlUrlController(Resource):
    @api.doc(params={'url': {'description': 'website url', 'in': 'query', 'type': 'str'}})
    def get(self):
        return {
            "status": True,
            "message": "Coming Soon...!",
        }


@api.route('/crawlUrls')
class TargetBasedCrawlUrlsController(Resource):
    @api.doc(params={'urls': {
        'description': 'website urls',
        'in': 'body',
        'type': 'json',
        'example': {"urls": ["website_url1", "website_url2"]}
    }})
    def post(self):
        return {
            "status": True,
            "message": "Coming Soon...!",
        }


@api.route('/crawlFile')
@api.expect(upload_parser)
class TargetBasedCrawlFileController(Resource):
    def post(self):
        return {
            "status": True,
            "message": "Coming Soon...!",
        }


@api.route('/download')
class TargetBasedDownloadController(Resource):
    @api.doc(params={'output_file_name': {'description': 'website crawled data output file name', 'in': 'query', 'type': 'str'}})
    def get(self):
        return {
            "status": True,
            "message": "Coming Soon...!",
        }