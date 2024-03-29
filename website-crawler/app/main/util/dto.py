from flask_restplus import Namespace


class RawDto:
    api = Namespace('Raw Crawl', description='Unstructured data from website (Beta v1.1.0)')
    raw = api.model('raw', {})


class TargetBasedDto:
    api = Namespace('Target- Crawl', description='Check Scrapping History (Beta v1.1.0)')
    target = api.model('target', {})


class SemanticDto:
    api = Namespace('Semantic Crawl', description='Semantic data from Website (Beta v1.0.0)')
    semantic = api.model('semantic', {})


class AIDto:
    api = Namespace('AI Crawl', description='AI data from Website (Beta v1.0.0)')
    ai = api.model('ai', {})