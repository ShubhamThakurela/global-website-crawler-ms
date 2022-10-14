from flask_restplus import Api
from flask import Blueprint
from .main.controller.raw_controller import api as raw
from .main.controller.targetbased_controller import api as target
from .main.controller.semantic_controller import api as semantic
from .main.controller.ai_controller import api as ai
from .main.service.constant_service import ConstantService
from logging.handlers import RotatingFileHandler
import logging


logging.basicConfig(
    handlers=[RotatingFileHandler(ConstantService.log_path()+'/website-crawl.log', backupCount=10)],
    level=logging.DEBUG,
    format=f'%(asctime)s %(api_key)s %(pathname)s %(filename)s %(module)s %(funcName)s %(lineno)d %(levelname)s %(message)s'
)

old_factory = logging.getLogRecordFactory()
def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.api_key = "KV2APP00004"
    return record
logging.setLogRecordFactory(record_factory)

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='Company Crawler Microservices',
          version='1.0',
          description='Crawl data from websites'
          )

api.add_namespace(raw, path='/raw')
api.add_namespace(target, path='/target')
api.add_namespace(semantic, path='/semantic')
api.add_namespace(ai, path='/ai')
