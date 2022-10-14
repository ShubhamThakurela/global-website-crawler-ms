import csv
import os
import errno
from bs4.element import Comment


def create_csv_file(process_date, file_name):
    filePath = '../data/out/' + process_date + '/' + file_name + '.csv'
    if not os.path.exists(os.path.dirname(filePath)):
        try:
            os.makedirs(os.path.dirname(filePath))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    outFile = open(filePath, 'a+')
    writer = csv.DictWriter(outFile, fieldnames=['company_name', 'website', 'page_name', 'page_url', 'description', 'keywords', 'content'])
    writer.writeheader()

    return writer


def create_text_file(processDate, texts, baseUrl, url):
    baseUrl = baseUrl.replace('http://', '')
    baseUrl = baseUrl.replace('https://', '')

    url = url.replace('http://', '')
    url = url.replace('https://', '')
    url = url.replace('/', '-')
    urlPath = 'data/out/' + processDate + '/' + baseUrl+ '/' + url + '.txt'
    if not os.path.exists(os.path.dirname(urlPath)):
        try:
            os.makedirs(os.path.dirname(urlPath))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    visible_texts = filter(tag_visible, texts)
    bodyText = u" ".join(t.strip() for t in visible_texts)
    textFile = open(urlPath, 'w')
    textFile.write(bodyText)
    textFile.close()


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False

    return True


def create_error_file(processDate):
    if not os.path.exists(os.path.dirname('log/' + processDate + '/error_list.csv')):
        try:
            os.makedirs(os.path.dirname('log/' + processDate + '/error_list.csv'))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    errorFile = open('log/' + processDate + '/error_list.csv', 'w+')
    errWriter = csv.DictWriter(errorFile, fieldnames=['website', 'error', 'timestamp'])
    errWriter.writeheader()

    return errWriter
