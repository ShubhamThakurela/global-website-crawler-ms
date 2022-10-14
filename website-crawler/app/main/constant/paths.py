mode = "local"

if mode == "DEV":
    IN_PATH = r"/home/ubuntu/temp/drive/in"
    SCRAPPED_PATH = r"/home/ubuntu/temp/drive/out"
    HISTORY_PATH = r"/home/ubuntu/temp/drive/history"
    PROCESSED_PATH = r"/home/ubuntu/temp/drive/processed"
    LOG_PATH = r"/home/ubuntu/temp/drive/log"
    SERVER_HOST = r"54.152.136.117:6001"
elif mode == "QA":
    IN_PATH = r"/home/ubuntu/kv2/qa/sub-platform/kv2-global-crawl-engine/website_crawl/drive/in"
    SCRAPPED_PATH = r"/home/ubuntu/kv2/qa/sub-platform/kv2-global-crawl-engine/website_crawl/drive/out"
    PROCESSED_PATH = r"/home/ubuntu/kv2/qa/sub-platform/kv2-global-crawl-engine/website_crawl/drive/processed"
    LOG_PATH = r"/home/ubuntu/kv2/qa/sub-platform/kv2-global-crawl-engine/log"
    SERVER_HOST = r"0.0.0.0:6001"
elif mode == "PROD":
    IN_PATH = r"/home/ubuntu/app/prod/kv2/global-crawl-engine/website-crawl/drive/in"
    SCRAPPED_PATH = r"/home/ubuntu/app/prod/kv2/global-crawl-engine/website-crawl/drive/out"
    PROCESSED_PATH = r"/home/ubuntu/app/prod/kv2/global-crawl-engine/website-crawl/drive/processed"
    HISTORY_PATH = r"/home/ubuntu/app/prod/kv2/global-crawl-engine/website-crawl/drive/history"
    LOG_PATH = r"/home/ubuntu/app/prod/kv2/global-crawl-engine/website-crawl/drive/logs"
    SERVER_HOST = r"44.203.14.141:6001"
else:
    IN_PATH = r"W:\STRATESPHERE\drive\website_crawler_drive\in"
    SCRAPPED_PATH = r"W:\STRATESPHERE\drive\website_crawler_drive\out"
    HISTORY_PATH = r"W:\STRATESPHERE\drive\website_crawler_drive\history"
    PROCESSED_PATH = r"W:\STRATESPHERE\drive\website_crawler_drive\processed"
    LOG_PATH = r"W:\STRATESPHERE\drive\website_crawler_drive\logs"
    SERVER_HOST = r"127.0.0.1:3000"
