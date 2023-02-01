import os
import re
import time
import copy
import shutil
import random
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import glob
import zipfile
import logging
import requests
import pandas as pd
from pathlib import Path
import app.main.util.proxy as proxy
import app.main.service.file_service as file
from bs4 import BeautifulSoup, Comment
from selenium import webdriver
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from ..service.constant_service import ConstantService
from ..database.connection import insert_update_scraping_detail
from webdriver_manager.chrome import ChromeDriverManager


def crawl_by_url(org_url, internal=True, internal_limit=51):
    try:
        org_data = {}
        data_dict_ = {
            "web_url": org_url,
            "file_name": get_domain(org_url).strip().lower() + ".xlsx",
            "http_code": '',
            "page_count": '',
            "menu_count": '',
            "start_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_dt": '',
            "status": 0
        }

        logging.info("Started scraping for " + org_url)

        # Get home page data
        home_page_data = request_data(org_url)
        if 'url' in home_page_data:
            org_url = home_page_data['url']

        # website status
        org_data.update({"active": {"home": home_page_data['active']}})

        # Response status code
        org_data.update({"status_code": {"home": home_page_data['status_code']}})

        # website status
        org_data.update({"redirected_url": {"home": home_page_data['redirected_url']}})

        # Fetch soup object
        soup_obj = BeautifulSoup(home_page_data['content'], "html.parser")

        # Extract meta data from home page response
        meta_data = extract_meta_data(soup_obj)
        org_data.update({"meta": meta_data})

        # Extract home page content.
        home_content = extract_page_content(soup_obj)

        # Extract data using selenium
        is_js_page = False
        if home_page_data['active'] in [1, 2]:
            is_js_page = any(js_str in home_content.lower().replace("\n", " ") for js_str in
                             ConstantService.get_js_page_identifier())

        if is_js_page or not home_content.strip() or home_page_data['status_code'] != 200:
            selenium_obj = get_by_selenium(org_url)
            if not isinstance(selenium_obj, type(None)):
                home_content = selenium_obj.text
                if 'skip the intro' in home_content.lower():
                    selenium_obj = get_by_selenium(org_url, 30)
                    home_content = selenium_obj.text

                if not isinstance(selenium_obj, type(None)):
                    source_code = selenium_obj.get_attribute("outerHTML")
                    soup_obj = BeautifulSoup(source_code, "html.parser")

                # Reset status and active
                org_data.update({"active": {"home": 1}})

                page_title = ''
                if not isinstance(meta_data['title'], type(None)):
                    page_title = meta_data['title']

                if page_title.lower() not in ConstantService.get_not_ok_title():
                    org_data.update({"status_code": {"home": 200}})

        # Update home content in data dict
        org_data.update({"content": {"home": home_content}})

        # Update with home page urls
        org_data.update({"urls": {"home": org_url}})

        # Extract menu item.
        menu_item = extract_menu_item(soup_obj)

        if len(menu_item):
            org_data.update({"menu": menu_item})

        # Extract headings from homepage.
        heading = extract_headings(soup_obj)
        org_data.update({"heading": {"home": heading}})
        page_count = 1
        # Extract data from internal pages
        if internal:
            # Get internal and external page links
            urls = get_website_links_from_response(soup_obj, org_url, org_data, 5)
            if 'internal' in urls:
                org_data['urls'].update(urls['internal'])
                internal_data, org_data = process_internal(urls['internal'], org_data, internal_limit)
                if len(internal_data):
                    page_count += len(internal_data)
                    org_data['content'].update(internal_data)

            # Manage external links
            if 'external' in urls:
                external_links = ", ".join(urls['external'].values())
                # if external_links:
                org_data.update({"external_links": external_links})
                data_dict_.update({
                    "http_code": home_page_data['status_code'],
                    "page_count": page_count,
                    "menu_count": len(menu_item),
                    "end_dt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": home_page_data['active']
                })
                insert_update_scraping_detail(data_dict_)
    except Exception as e:
        print(str(e))
        logging.error(str(e))
    else:
        # LogService.log_info("Completed scraping for " + org_url)
        logging.info("Completed scraping for " + org_url)

    return org_data


def get_external_urls(org_url):
    try:
        org_data = {}
        external_links = {}

        # Get home page data
        home_page_data = request_data(org_url)
        if 'url' in home_page_data:
            org_url = home_page_data['url']

        # website status
        org_data.update({"redirected_url": {"home": home_page_data['redirected_url']}})

        # Fetch soup object
        soup_obj = BeautifulSoup(home_page_data['content'], "html.parser")

        # Get internal and external page links
        urls = get_website_links_from_response(soup_obj, org_url, org_data, 5)
        if 'external' in urls:
            external_links = urls['external']
    except Exception as e:
        print(str(e))
        logging.error(str(e))

    return external_links


def process_internal(internal_pages, org_data, internal_limit):
    subpage_data_dict = {}
    try:
        num = 1
        print("Internal Pages... ")
        for page_name in internal_pages:
            if page_name == 'home':
                continue

            if int(num) > int(internal_limit):
                break

            page_url = prepare_http_url(internal_pages[page_name])
            print(str(num) + "   ---------> Page... " + page_url)

            subpage_page_data = request_data(page_url)
            page_name = data_clean(page_name)
            if page_name == '':
                page_name = get_page_name(page_url)

            # Fetch soup object
            subpage_soup_obj = BeautifulSoup(subpage_page_data['content'], "html.parser")
            sub_page_content = extract_page_content(subpage_soup_obj)

            # Extract data using selenium
            is_js_page = False
            if subpage_page_data['active'] in [1, 2]:
                is_js_page = any(
                    js_str in sub_page_content.lower() for js_str in ConstantService.get_js_page_identifier())

            if is_js_page or not sub_page_content.strip() or subpage_page_data['status_code'] != 200:
                selenium_obj = get_by_selenium(page_url)
                if not isinstance(selenium_obj, type(None)):
                    sub_page_content = selenium_obj.text
                    if 'skip the intro' in sub_page_content.lower():
                        selenium_obj = get_by_selenium(page_url, 30)
                        sub_page_content = selenium_obj.text

                    if not isinstance(selenium_obj, type(None)):
                        source_code = selenium_obj.get_attribute("outerHTML")
                        subpage_soup_obj = BeautifulSoup(source_code, "html.parser")

                    # Reset status and active
                    subpage_page_data['active'] = 1

                    sub_page_title = ''
                    if not isinstance(org_data['meta']['title'], type(None)):
                        sub_page_title = org_data['meta']['title']

                    if sub_page_title.lower() not in ConstantService.get_not_ok_title():
                        subpage_page_data['status_code'] = 200

            # Set subpage data to data dict
            subpage_data_dict[page_name] = sub_page_content

            # Extract headings.
            heading = extract_headings(subpage_soup_obj)
            org_data['heading'].update({page_name: heading})

            org_data['active'].update({page_name: subpage_page_data['active']})
            org_data['status_code'].update({page_name: subpage_page_data['status_code']})
            org_data['redirected_url'].update({page_name: subpage_page_data['redirected_url']})
            num += 1
    except Exception as e:
        print(str(e))
        logging.error(str(e))
    return subpage_data_dict, org_data


# Returns all URLs that is found on `url` in which it belongs to the same website
def get_website_links_from_response(soup, url, org_data, level=0):
    all_urls = set()
    internal_urls = {}
    external_urls = {}
    urls_dict = {}
    try:
        all_urls.add(url)
        internal_urls['home'] = url

        # domain name of the URL without the protocol
        domain_name = urlparse(url).netloc
        domain_name = domain_name.replace('www.', '').lower()

        # Redirected url domain name
        redirected_domain = domain_name
        if 'redirected_url' in org_data:
            if 'home' in org_data['redirected_url']:
                redirected_domain = get_domain(org_data['redirected_url']['home']).strip().lower()

        for a_tag in soup.findAll("a"):
            href_name = a_tag.get_text().strip()
            href_name = data_clean(href_name).lower().replace("'", '')
            href = a_tag.attrs.get("href")

            # Not a valid URL
            if not_valid_href(href):
                continue

            # join the URL if it's relative (not absolute link)
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            # remove URL GET parameters, URL fragments, etc.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            href = href.rstrip('/')

            # already in the set
            if href in all_urls:
                continue

            # All found urls
            href = href.lower()
            all_urls.add(href)

            # If page name not present
            if href_name == '' or len(href_name) == 1:
                href_name = get_page_name(href)

            href_list = href.split("//")
            if re.search('[a-zA-Z]', href_list[len(href_list) - 1]) is None:
                continue

            # Internal links
            domain_from_href = get_domain(href)
            if domain_name in domain_from_href or (redirected_domain and (
                    redirected_domain in domain_from_href or redirected_domain.split('.')[
                0] + '.' in domain_from_href)):
                if level != 0:
                    new_href = href.replace('http://', '')
                    new_href = new_href.replace('https://', '')
                    new_href = new_href.rstrip('/')
                    if new_href.count('/') > level:
                        continue
                internal_urls[href_name] = href
            else:
                href_name = get_href_name(href)
                href_name = data_clean(href_name).lower().replace("'", '')
                external_urls[href_name] = href
        urls_dict['external'] = external_urls
        urls_dict['internal'] = internal_urls
    except Exception as e:
        print(str(e))
        logging.error(str(e))
    return urls_dict


def url_valid(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except:
        return False


# Get label for extracted link
def get_href_name(href):
    domain_name = urlparse(href).netloc
    domain_name = domain_name.replace('www.', '')
    domain_res = domain_name.split('.')
    return domain_res[0].strip()


# Check several cases of not valid urls
def not_valid_href(url):
    if not is_valid(url):
        return True

    if valid_image_url(url):
        return True

    SKIP_PATTERN = [
        "youtube.com",
        "javascript",
        "mailto:",
        "tel:",
        "download",
    ]

    for pattern in SKIP_PATTERN:
        if url.lower().find(pattern) != -1:
            return True

    return False


# Check url is an image url
def valid_image_url(url):
    VALID_IMAGE_EXTENSIONS = [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
    ]
    return any([url.endswith(e) for e in VALID_IMAGE_EXTENSIONS])


def extract_page_content(soup):
    body_text = ''
    strip_content = 0
    try:
        texts = soup.findAll(text=True)
        visible_texts = filter(file.tag_visible, texts)
        if strip_content:
            body_text = u" ".join(t.strip() for t in visible_texts)
        else:
            body_text = u"\n".join(t for t in visible_texts)
        body_text = body_text.strip()
    except Exception as e:
        print(str(e))
        logging.error(str(e))
    return body_text


def create_com(url):
    urllist = []
    url = url.replace("https://www.", "").replace("https://", "").replace("http://", "").replace("http://www.",
                                                                                                 "").replace("https://",
                                                                                                             "").replace(
        "www.", "")
    if "https://www." not in url:
        urllist.append("https://www." + url)
    if "https://" not in url:
        urllist.append("https://" + url)
    if "http://www." not in url:
        urllist.append("http://www." + url)
    if "http:/" not in url:
        urllist.append("http://" + url)
    return urllist


def request_data(page_url):
    data_dict = {}
    # Get Random User Agent String.
    referer = random.choice(ConstantService.get_all_search_engines())
    headers = {'User-Agent': proxy.ua.random, 'Referer': referer, 'Accept-Language': 'en-US,en;q=0.5'}
    page_url = prepare_http_url(page_url)
    url_list = create_com(page_url)
    for url in url_list:
        response_url = ''
        try:
            response = requests.get(url, headers=headers, timeout=40, allow_redirects=True)
            status_code = response.status_code
            response_url = response.url
            response_txt = response.content
            if status_code == 200:
                break
        except Exception as e:
            print(e)
            status_code = 503
            response_txt = str(e)

    # Update status on the basis of status code.
    status = 1
    if status_code in [503, 404, 500]:
        status = 0

    redirected_url = ''
    if status and get_domain(response_url) != get_domain(page_url):
        redirected_url = response_url
        status = 2

    # Set org url from response url
    if response_url:
        page_url = response_url

    data_dict.update({
        'active': status,
        'status_code': status_code,
        'url': page_url,
        'redirected_url': redirected_url.strip('/'),
        'content': response_txt,
    })

    return data_dict


def http_post_call(page_url, headers):
    try:
        # Making the post request
        request = Request(page_url, headers=headers)
        response = urlopen(request)

        # Reading the response from the site.
        data = response.read()

        # Get status code
        status_code = response.getcode()
    except Exception as e:
        print(str(e))
        logging.error(str(e))
    else:
        return data, status_code


def prepare_https_url(url):
    url = url.replace('http://', '')
    url = url.replace('https://', '')
    url = url.replace('www.', '')
    url = url.strip()
    return 'https://www.' + url


def extract_meta_data(soup):
    try:
        metas = soup.find_all('meta')
        meta_dict = {'description': '', 'keywords': '', 'title': '', 'tags': '', 'content_type': '',
                     'registration_required': '', 'customer_type': '', 'sales_availability': ''}

        for tag in metas:
            if 'name' in tag.attrs.keys():
                meta_dict = extract_meta_from_name(tag, meta_dict)

            if 'property' in tag.attrs.keys():
                meta_dict = extract_meta_from_property(tag, meta_dict)

        title = soup.find('title')
        if not isinstance(title, type(None)):
            if title.text not in meta_dict['title']:
                meta_dict['title'] = title.text + ", " + meta_dict['title']
                meta_dict['title'] = meta_dict['title'].strip(", ")
    except Exception as e:
        print(str(e))
        logging.error(str(e))

    return meta_dict


def extract_meta_from_name(tag, meta_dict):
    try:
        content = ''
        if tag.has_attr('content'):
            content = data_clean(tag.attrs['content'].strip())

        if content:
            if 'description' in tag.attrs['name'].strip().lower() and content not in meta_dict['description']:
                meta_dict['description'] = (meta_dict['description'] + " " + content).strip()

            if 'keywords' in tag.attrs['name'].strip().lower() and content not in meta_dict['keywords']:
                meta_dict['keywords'] = (meta_dict['keywords'] + " " + content).strip()

            if 'title' in tag.attrs['name'].strip().lower() and content not in meta_dict['title']:
                meta_dict['title'] = (meta_dict['title'] + " " + content).strip()

            if 'tags' in tag.attrs['name'].strip().lower() and content not in meta_dict['tags']:
                meta_dict['tags'] = (meta_dict['tags'] + " " + content).strip()

            if 'contentType' in tag.attrs['name'].strip().lower() and content not in meta_dict['content_type']:
                meta_dict['content_type'] = (meta_dict['content_type'] + " " + content).strip()

            if 'registrationRequired' in tag.attrs['name'].strip().lower() and content not in meta_dict[
                'registration_required']:
                meta_dict['registration_required'] = (meta_dict['registration_required'] + " " + content).strip()

            if 'customerType' in tag.attrs['name'].strip().lower() and content not in meta_dict['customer_type']:
                meta_dict['customer_type'] = (meta_dict['customer_type'] + " " + content).strip()

            if 'salesAvailability' in tag.attrs['name'].strip().lower() and content not in meta_dict[
                'sales_availability']:
                meta_dict['sales_availability'] = (meta_dict['sales_availability'] + " " + content).strip()
    except Exception as e:
        print(str(e))
        logging.error(str(e))
    return meta_dict


def extract_meta_from_property(tag, meta_dict):
    try:
        content = ''
        if tag.has_attr('content'):
            content = data_clean(tag.attrs['content'].strip())

        if content:
            if 'description' in tag.attrs['property'].strip().lower() and content not in meta_dict['description']:
                meta_dict['description'] = (meta_dict['description'] + " " + content).strip()

            if 'keywords' in tag.attrs['property'].strip().lower() and content not in meta_dict['keywords']:
                meta_dict['keywords'] = (meta_dict['keywords'] + " " + content).strip()

            if 'title' in tag.attrs['property'].strip().lower() and content not in meta_dict['title']:
                meta_dict['title'] = (meta_dict['title'] + " " + content).strip()

            if 'tags' in tag.attrs['property'].strip().lower() and content not in meta_dict['tags']:
                meta_dict['tags'] = (meta_dict['tags'] + " " + content).strip()

            if 'contentType' in tag.attrs['property'].strip().lower() and content not in meta_dict['content_type']:
                meta_dict['content_type'] = (meta_dict['content_type'] + " " + content).strip()

            if 'registrationRequired' in tag.attrs['property'].strip().lower() and content not in meta_dict[
                'registration_required']:
                meta_dict['registration_required'] = (meta_dict['registration_required'] + " " + content).strip()

            if 'customerType' in tag.attrs['property'].strip().lower() and content not in meta_dict['customer_type']:
                meta_dict['customer_type'] = (meta_dict['customer_type'] + " " + content).strip()

            if 'salesAvailability' in tag.attrs['property'].strip().lower() and content not in meta_dict[
                'sales_availability']:
                meta_dict['sales_availability'] = (meta_dict['sales_availability'] + " " + content).strip()
    except Exception as e:
        print(str(e))
        logging.error(str(e))
    return meta_dict


# Checks whether `url` is a valid URL
def is_valid(url):
    result = False
    if url:
        url = url.strip()
        url_list = url.split(".")
        url_ext = url_list[len(url_list) - 1].lower()
        if len(url) > 1 and url_ext not in ['pdf', 'csv', 'zip', 'mp4', 'jpeg', 'png', 'gif', 'xml']:
            result = True

    return result


def copy_file_data(files, source_folder, destination_folder):
    try:
        file_path = destination_folder + '/'
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        for file_name in files:
            source = source_folder + '/' + file_name
            destination = destination_folder + '/' + file_name
            if os.path.isfile(source):
                shutil.copy(source, destination)
    except Exception as e:
        print(str(e))


def test(f, day):
    try:
        format1 = "%Y%m%d"
        today = datetime.today()
        tomorrow = today + timedelta(1)
        date1 = tomorrow.strftime(format1)
        thirty_d = today - relativedelta(days=int(day))
        date2 = thirty_d.strftime(format1)
        timefmt = format1
        start = calendar.timegm(datetime.strptime(date2, timefmt).timetuple())
        end = calendar.timegm(datetime.strptime(date1, timefmt).timetuple())
        if not os.path.isfile(f):
            return 0
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(f)
        return start <= ctime and end >= ctime
    except Exception as e:
        print(str(e))


def history_check(hist_path, website_list, days_history):
    files = [f for f in glob.glob(os.path.join(hist_path, "*")) if test(f, days_history)]
    file_name_list = []
    for x in files:
        name = os.path.basename(x)
        name = name.replace('.xlsx', '')
        file_name_list.append(name)
    url_list = []
    file_list = []
    for i in website_list:
        if i not in file_name_list:
            url_list.append(i)
        if i in file_name_list:
            file_list.append(i + '.xlsx')
    return url_list, file_list


def crawl_by_file(url_list, check_history, days_history, history_path, out_path, internal_page, internal_page_limit):
    # Start time

    # start_time = time.time()
    website_list = []
    for url in url_list:
        website_list.append(get_domain(url))
    hist_path = ConstantService.histroy_path()
    if check_history is True:
        url_list, history_list = history_check(hist_path, website_list, days_history)
        if len(history_list) != 0:
            copy_file_data(history_list, hist_path, out_path)

    counter = 1
    for url in url_list:
        print(str(counter) + " - Url... " + str(url))
        raw_data = crawl_by_url(url, internal_page, internal_page_limit)
        data_to_file(raw_data, url, out_path)
        data_to_file_histroy(raw_data, url, history_path)
        counter += 1

    # Move file to processed after completed the process
    # if not os.path.exists(os.path.dirname(ConstantService.data_processed_path())):
    #     os.makedirs(os.path.dirname(ConstantService.data_processed_path()))
    # shutil.move(file_path, os.path.join(ConstantService.data_processed_path(), os.path.basename(file_path)))

    # End Time
    # end_time = time.time()
    # print("Processing Time: ", '{:.3f} sec'.format(end_time - start_time))

    # return zip_file_path


def data_to_file(data_dict, output_file_name, out_path):
    file_path = out_path + '/'
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    writer = pd.ExcelWriter(file_path + get_domain(output_file_name) + '.xlsx')
    have_data = False
    if len(data_dict):
        have_data = True
        save_website_data(data_dict, writer)
    if have_data:
        writer.save()


def data_to_file_histroy(data_dict, output_file_name, out_path):
    file_path = out_path
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    writer = pd.ExcelWriter(file_path + get_domain(output_file_name) + '.xlsx')
    have_data = False
    if len(data_dict):
        have_data = True
        save_website_data(data_dict, writer)
    if have_data:
        writer.save()


def save_website_data(web_data, writer):
    profile_data_dict = {}
    if 'meta' in web_data:
        profile_data_dict.update(web_data['meta'])

    if 'menu' in web_data:
        profile_data_dict.update(web_data['menu'])

    if 'external_links' in web_data:
        profile_data_dict.update({
            "external_links": web_data['external_links']
        })

    profile_data_list = []
    if 'content' in web_data:
        for page, pg_data in web_data['content'].items():
            profile_data_dict = copy.deepcopy(profile_data_dict)
            profile_data_dict.update({
                "page": page,
                "page_url": web_data['urls'][page] if page in web_data['urls'] else '',
                "redirected_url": web_data['redirected_url'][page] if page in web_data['redirected_url'] else '',
                "headings": web_data['heading'][page] if page in web_data['heading'] else '',
                "content": pg_data,
                "active": web_data['active'][page] if page in web_data['active'] else '',
                "status_code": web_data['status_code'][page] if page in web_data['status_code'] else ''
            })
            profile_data_list.append(profile_data_dict)
    try:
        df = pd.DataFrame.from_dict(profile_data_list)
        df = df.applymap(illegal_char_remover)
        df.to_excel(writer, sheet_name='Website', index=False)
    except Exception as e:
        print(str(e))


def get_url_to_scrap(file_path):
    url_list = []
    if not os.path.isfile(file_path) or os.path.getsize(file_path) == 0:
        return url_list

    print("Processing File... " + str(file_path))

    # Check file type
    name, file_type = os.path.splitext(file_path)
    file_type = file_type.lower()

    # Read file on the basis of type
    if file_type in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path)
    elif file_type == '.csv':
        df = pd.read_csv(file_path)
    else:
        print("Unsupported file extension " + file_type + "! We are supporting only (csv, xls, xlsx).")
        return url_list

    for i, j in df.iterrows():
        url = ''
        if 'Url' in j:
            url = str(j['Url'])
        elif 'urls' in j:
            url = str(j['urls'])
        elif 'url' in j:
            url = str(j['url'])
        elif 'website' in j:
            url = str(j['website'])
        elif 'Website' in j:
            url = str(j['Website'])

        url = str(url).replace(" ", "")
        if url == 'nan' or url == '-' or url == '':
            continue

        # url_list.append(prepare_http_url(url))
        url_list.append(url)
    return url_list


def extract_menu_item(soup):
    menu_item = {}
    try:
        # Get menu match by class name
        menu_item = get_menu_from_class_name(soup, menu_item)

        # When menu arrange in ul/li
        if not menu_item:
            menu_item = get_menu_from_ul_tag(soup, menu_item)

        # Get menu when start from li
        if not menu_item:
            menu_item = get_menu_from_li_tag(soup, menu_item)

        # Get menu as nav from nav tag
        if not menu_item:
            menu_item = get_menu_from_nav_tag(soup, menu_item)

        # Get menu match by role
        if not menu_item:
            menu_item = get_menu_from_role(soup, menu_item)

        # Get menu match by button
        if not menu_item:
            menu_item = get_menu_from_button(soup, menu_item)

        # Get menu match by aside
        if not menu_item:
            menu_item = get_menu_from_aside(soup, menu_item)

        # Get menu match by dl
        if not menu_item:
            menu_item = get_menu_from_dl(soup, menu_item)

    except Exception as e:
        print(str(e))
        logging.error(str(e))

    return menu_item


def get_menu_from_button(soup_obj, menu_item):
    button_list_obj = soup_obj.find_all('button')
    for button_obj in button_list_obj:
        next_obj = button_obj.find_next()
        if not isinstance(next_obj, type(None)):
            # menu_wrapper = next_obj.find_all('div', {'class': re.compile('|'.join(ConstantService.get_menu_item_wrapper_class()) + '$')})
            menu_wrapper = next_obj.find_all('div', class_=ConstantService.get_menu_item_wrapper_class())
            if isinstance(menu_wrapper, type(None)):
                menu_list = [', '.join(item_div.find_all(text=True)) for item_div in menu_wrapper]
                if len(menu_list):
                    menu_name = button_obj.get_text(strip=True)
                    menu_item = update_in_item(menu_item, menu_list, menu_name)

    return menu_item


def get_menu_from_role(soup_obj, menu_item):
    menu_list_obj = soup_obj.find_all(['a', 'div', 'span'], {'role': 'menu'})
    for menu_obj in menu_list_obj:
        submenu_obj = menu_obj.find_next_sibling(['a', 'div', 'span'], {'id': 'submenu'})
        if isinstance(submenu_obj, type(None)):
            menu_list = submenu_obj.find_all(text=True)
            if len(menu_list):
                menu_name = menu_obj.get_text(strip=True)
                menu_item = update_in_item(menu_item, menu_list, menu_name)

    return menu_item


def get_menu_from_ul_tag(soup_obj, menu_item):
    ul_list = soup_obj.find_all(['ul', 'ol'])
    for ul_tab in ul_list:
        if not valid_parent(ul_tab):
            continue

        li_list = ul_tab.find_all('li', recursive=False)
        for li_tab in li_list:
            # Remove commented code from soup object
            for element in li_tab(text=lambda it: isinstance(it, Comment)):
                element.extract()

            # Check if li have nested ul
            menu_name, menu_list = menu_from_li(li_tab)
            menu_item = update_in_item(menu_item, menu_list, menu_name)

            # Check if li have data in some inner tags
            menu_name, menu_list = menu_from_data_inner_tag(li_tab, soup_obj)
            menu_item = update_in_item(menu_item, menu_list, menu_name)

            # Check if li have button
            menu_name, menu_list = menu_from_button_in_li(li_tab)
            menu_item = update_in_item(menu_item, menu_list, menu_name)

    return menu_item


def get_menu_from_li_tag(soup_obj, menu_item):
    li_tag = soup_obj.find('li')
    while li_tag is not None:
        # Check if li have nested ul
        menu_name, menu_list = menu_from_li(li_tag)
        menu_item = update_in_item(menu_item, menu_list, menu_name)
        li_tag = li_tag.find_next_sibling('li')

    return menu_item


def menu_from_li(li_tab):
    menu_name = ''
    menu_item = []
    # First check for ul in li, if not present check for div
    inner_ul_list = li_tab.find_all('ul', recursive=True)
    if len(inner_ul_list) == 0:
        inner_ul_list = li_tab.find_all('div', {'aria-labelledby': re.compile('Dropdown|dropdown|dropdown-menu$')})
        if len(inner_ul_list) == 0:
            inner_ul_list = li_tab.find_all('div', {'class': re.compile('Dropdown|dropdown|dropdown-menu$')})

    if len(inner_ul_list):
        for menu_tab in li_tab.find_all():
            menu_name = get_menu_name(menu_tab)
            if menu_name != '':
                break
            if menu_name == '' and len(menu_tab.find_all()):
                for menu_tab1 in menu_tab.find_all():
                    menu_name = get_menu_name(menu_tab1)
                    if menu_name != '':
                        break

        menu_list = []
        for inner_ul in inner_ul_list:
            all_in_ul = inner_ul.find_all()
            for tag_in_ul in all_in_ul:
                if isinstance(tag_in_ul, type(None)):
                    continue
                menu_string = tag_in_ul.get_text(separator=", ").strip()
                for menu_text in menu_string.split(','):
                    if re.match(r'^[_\W]+$', menu_text.strip()):
                        continue
                    menu_list.append(menu_text.strip())

        # Item cleanup
        for m_item in menu_list:
            m_item = m_item.strip(',')
            m_item = m_item.strip()
            if m_item:
                menu_item.append(m_item)

    return menu_name, list(set(menu_item))


def menu_from_data_inner_tag(li_tab, soup):
    menu_name = ''
    menu_item = []
    li_tab_a = li_tab.find('a')
    if not isinstance(li_tab_a, type(None)):
        menu_name = li_tab_a.get_text()
        if not menu_name:
            menu_name = li_tab_a.find(text=True)

        if menu_name:
            menu_name = menu_name.strip()
            data_nav_dropdown = li_tab_a.attrs.get("data-nav-dropdown-toggle")
            if data_nav_dropdown:
                menu_div = soup.find("div", {"data-nav-dropdown": data_nav_dropdown})
                for menu_dev_item in menu_div.findAll(text=True):
                    if menu_dev_item.strip():
                        menu_item.append(menu_dev_item.strip())
            else:
                item_list = li_tab.find_all(['nav', 'div', 'ol', 'ul'])
                if len(item_list):
                    menu_item = [', '.join(item.find_all(text=True)) for item in item_list]

    return menu_name, list(set(menu_item))


def menu_from_button_in_li(li_tab):
    menu_name = ''
    menu_item = []
    menu_button = li_tab.find('button')
    if not isinstance(menu_button, type(None)):
        menu_name = menu_button.get_text().strip()
        if menu_name != 'close':
            menu_item_div = menu_button.parent.find('div')
            if not isinstance(menu_item_div, type(None)):
                menu_item.append(menu_item_div.get_text().strip())

    return menu_name, list(set(menu_item))


def get_menu_name(manu_tab):
    menu_name = ''
    if manu_tab.string:
        menu_name = manu_tab.string.strip()
    else:
        if manu_tab.text:
            menu_name = manu_tab.text.strip()
    return menu_name


def get_menu_from_nav_tag(soup_obj, menu_item):
    nav_sections = soup_obj.find_all('nav')
    for nav_section in nav_sections:
        nav_list = nav_section.find_all('nav')
        if len(nav_list):
            for nav in nav_list:
                sibling = nav.previousSibling
                if not isinstance(sibling, type(None)):
                    menu_list = [nav_a.text for nav_a in nav.findAll('a')]
                    menu_name = sibling.text.strip()
                    menu_item = update_in_item(menu_item, menu_list, menu_name)

                nested_navs = nav.find_all('nav')
                if not isinstance(nested_navs, type(None)):
                    for nested_nav in nested_navs:
                        if len(nested_nav.find_previous_siblings('div')):
                            menu_name = nested_nav.find_previous_siblings('div')[0].text.strip()
                            menu_list = [nav_a.text for nav_a in nested_nav.findAll('a')]
                            menu_item = update_in_item(menu_item, menu_list, menu_name)

                    if len(nested_navs) == 0:
                        if len(nav.find_previous_siblings('div')):
                            menu_name = nav.find_previous_siblings('div')[0].text.strip()
                            menu_list = [nav_a.text for nav_a in nav.findAll('a')]
                            menu_item = update_in_item(menu_item, menu_list, menu_name)
        else:
            section_list = nav_section.find_all('section', {'class': re.compile('menu$')})
            if len(section_list):
                for section in section_list:
                    dropdown_a = section.find('a')
                    if not isinstance(dropdown_a, type(None)):
                        menu_name = dropdown_a.text.strip()
                        menu_list = [nav_div.text for nav_div in section.find_all('div')]
                        menu_item = update_in_item(menu_item, menu_list, menu_name)
    return menu_item


def get_menu_from_class_name(soup_obj, menu_item):
    menu_list = soup_obj.find_all(['div', 'td'], class_=ConstantService.get_menu_class())
    for menu in menu_list:
        # Remove commented code from soup object
        for element in menu(text=lambda it: isinstance(it, Comment)):
            element.extract()

        menu_name_wrapper = menu.find('div', class_=ConstantService.get_menu_name_wrapper_class())
        if isinstance(menu_name_wrapper, type(None)):
            menu_name_wrapper = menu.find('div', {'role': 'button'})
            if isinstance(menu_name_wrapper, type(None)):
                menu_name_wrapper = menu.find(['label', 'p', 'ins', 'a', 'h3', 'span'])

        if not isinstance(menu_name_wrapper, type(None)):
            menu_name = menu_name_wrapper.find(text=True, recursive=False)
            if isinstance(menu_name, type(None)) or not menu_name.strip():
                menu_name = menu_name_wrapper.get_text().strip()

            menu_item_wrapper = menu.find_all(['div', 'nav', 'a', 'li'],
                                              class_=ConstantService.get_menu_item_wrapper_class())
            if len(menu_item_wrapper):
                menu_list = [', '.join(item_div.find_all(text=True)) for item_div in menu_item_wrapper]
                if len(menu_list):
                    menu_item = update_in_item(menu_item, menu_list, menu_name.strip())

        span_item_list = menu.find_all('span', {'class': re.compile('Header-nav-item$')})
        if len(span_item_list):
            for span_section in span_item_list:
                menu_title_a = span_section.find('a', {'class': re.compile('Header-nav-folder-title$')})
                if not isinstance(menu_title_a, type(None)):
                    menu_name = menu_title_a.text.strip()
                    span_section_list = span_section.find_all('a', {'class': re.compile('Header-nav-folder-item$')})
                    if not isinstance(span_section_list, type(None)):
                        menu_list = [', '.join(item_div.find_all(text=True)) for item_div in span_section_list]
                        if len(menu_list):
                            menu_item = update_in_item(menu_item, menu_list, menu_name)

    return menu_item


def get_menu_from_aside(soup_obj, menu_item):
    aside_obj = soup_obj.find('aside')
    if not isinstance(aside_obj, type(None)):
        aside_uls = aside_obj.find_all('ul')
        for aside_ul in aside_uls:
            aside_lis = aside_ul.find_all('li')
            for aside_li in aside_lis:
                li_text = aside_li.get_text().strip()
                if aside_li.has_attr('class') and aside_li['class'][0] in ['oc-menu-header']:
                    menu_name = li_text
                    menu_item.update({'menu_' + menu_name: ''})
                else:
                    if menu_item['menu_' + menu_name]:
                        menu_item.update({'menu_' + menu_name: menu_item['menu_' + menu_name] + ', ' + li_text})
                    else:
                        menu_item.update({'menu_' + menu_name: li_text})

    return menu_item


def get_menu_from_dl(soup_obj, menu_item):
    dl_list = soup_obj.find_all('dl')
    for dl_obj in dl_list:
        dt_obj = dl_obj.find('dt')
        if not isinstance(dt_obj, type(None)):
            menu_name = dt_obj.find(text=True).strip()
            if not menu_name:
                dt_img = dt_obj.find('img')
                if not isinstance(dt_img, type(None)):
                    menu_name = dt_img.attrs.get('alt')

            if menu_name and len(menu_name) > 1:
                dd_list = dl_obj.find_all('dd')
                if len(dd_list):
                    menu_list = [', '.join(dd_obj.find_all(text=True)) for dd_obj in dd_list]
                    if len(menu_list):
                        menu_item = update_in_item(menu_item, menu_list, menu_name.strip())

    return menu_item


def update_in_item(menu_item, menu_list, menu_name):
    menu_list = list(set(menu_list))
    if menu_name and len(menu_list) and 'menu_' + menu_name not in menu_item:
        new_menu_items = []

        for item in menu_list:
            item = " ".join(item.split())
            item = ", ".join(val.strip() for val in item.split(",") if val.strip() != '')
            new_menu_items.append(item.strip())

        if len(new_menu_items):
            menu_item.update({
                'menu_' + menu_name: ', '.join(map(str, new_menu_items))
            })

    return menu_item


def valid_parent(tag_soup):
    valid_parent_tag = ['nav', 'header', 'section']
    valid = False
    for parent in tag_soup.parents:
        if parent.name.lower() in valid_parent_tag or parent.get('id') in ['header', 'nav']:
            valid = True
            break
    return valid


def extract_headings(soup):
    headings = ''
    try:
        heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong']
        for tag in heading_tags:
            headings += str(get_heading(soup, tag).strip()) + "\n"
        headings = headings.strip()
    except Exception as e:
        print(str(e))
        logging.error(str(e))

    return headings


def get_by_selenium(org_url, stime=10):
    try:
        # Commented it because without www chrome opening wrong page. It may open other issue.
        # org_url = org_url.replace('www.', '')
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
        driver.get(org_url)
        time.sleep(stime)
        # content = driver.find_element_by_tag_name("body")
        content = driver.find_element('xpath', '/html/body')
    except Exception as e:
        print(str(e))
        return None
    else:
        return content


# def get_by_selenium(org_url, stime=10):
#     try:
#         # Display in order to avoid CloudFare bot detection
#         display = Display(visible=0, size=(800, 800))
#         display.start()
#
#         options = webdriver.ChromeOptions()
#         options.add_argument('--ignore-certificate-errors')
#         options.add_argument('--incognito')
#         # options.add_argument('--headless')
#         options.add_argument("--disable-blink-features=AutomationControlled")
#         # driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
#         driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
#         try:
#             driver.get(org_url)
#             time.sleep(stime)
#             content = driver.find_element_by_tag_name("body")
#         except:
#             driver.close()
#             driver.quit()
#     except Exception as e:
#         print(str(e))
#         return None
#     else:
#         return content


def get_heading(soup, tag):
    heading = ''
    try:
        h_list = soup.findAll(tag)
        if not isinstance(h_list, type(None)):
            heading = '\n'.join(str(h_data.text.strip()) for h_data in h_list)
    except Exception as e:
        print(str(e))
        logging.error(str(e))

    return heading


def get_page_name(page_url):
    social_list = [
        'linkedin',
        'facebook',
        'instagram',
        'twitter',
        'youtube'
    ]
    if any(pattern in page_url for pattern in social_list):
        social_domain = get_domain(page_url)
        page_name = social_domain.split(".")[0]
    else:
        page_name = page_url.split("/")[len(page_url.split("/")) - 1].strip()
        page_name = page_name.strip("/")
    return page_name


def data_clean(y):
    if type(y) == str:
        y = " ".join(re.findall("[a-zA-Z0-9._^%₹$#!~@,-:;&*()='}{|\/]+", y))
    elif type(y) == bytes:
        y = y.strip()
        y = y.replace(b'\xa0', b'')

    return y


def clean_url(url):
    url = url.rstrip('/')
    url = url.rstrip('#')
    url = url.rstrip('/')
    url = url.strip()
    url = url.lower()
    return url


def prepare_http_url(url):
    url = url.replace('http://', '')
    url = url.replace('https://', '')
    url = url.replace('www.', '')
    url = url.strip()
    url = url.strip('/')
    return 'http://www.' + url


def get_domain(url):
    url = url.rstrip('/')
    url = url.rstrip('#')
    url = url.rstrip('/')
    url = url.replace('http://', '')
    url = url.replace('https://', '')
    url = url.replace('www.', '')
    url = url.strip()
    url = url.lower()
    res = url.split('/')
    url = res[0].strip()
    url = url.split(":")[0].strip()
    return url


def illegal_char_remover(data):
    ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
    """Remove ILLEGAL CHARACTER."""
    if isinstance(data, str):
        return ILLEGAL_CHARACTERS_RE.sub("", data)
    else:
        return data


def zipdir(src, dst):
    dir_path_list = src.split("/")
    dir_name = dir_path_list[len(dir_path_list) - 1]
    zip_file_path = dst + '/' + dir_name + '_Web_Data'
    zf = zipfile.ZipFile("%s.zip" % (zip_file_path), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            print('Zipping %s' % (os.path.join(dirname, filename)))
            zf.write(absname, arcname)
    zf.close()

    return dir_name + '_Web_Data.zip'


def web_summary(out_path):
    try:
        txt_folder = Path(out_path).rglob('*.xlsx')
        files = [x for x in txt_folder]
        url_page = []
        for x in files:
            name = x.name
            name = name.replace(".xlsx", "")
            data = pd.read_excel(x, sheet_name=None, engine='openpyxl')
            data["Website"].fillna('', inplace=True)
            data = data["Website"]
            index = data.index
            menu_cols = [c for c in data.columns if "menu_" in c]
            for i in index:
                pass
            http_status = data["status_code"].iloc[0]
            companies_url = data["page_url"].iloc[0]
            url_page.append({"Company_url": companies_url, "Status_code": http_status, "page_count": i + 1,
                             "menu_count": len(menu_cols)})

        df = pd.DataFrame()
        for i in url_page:
            df = df.append(i, ignore_index=True)

        file_path = out_path + '/'
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        df.to_excel(file_path + "Scrapping_data_Summary" + '.xlsx', index=False)

    except Exception as e:
        print(str(e))
