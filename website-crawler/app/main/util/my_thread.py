
from ..service.raw_service import crawl_by_file, get_url_to_scrap, zipdir, web_summary
from ..service.constant_service import ConstantService
from threading import Barrier, Thread
import math
import os
import shutil
import time


def run(url_list, check_history, days_history, history_path,  out_path, internal_page, internal_page_limit, barrier):
    crawl_by_file(url_list, check_history, days_history, history_path,  out_path, internal_page, internal_page_limit)
    barrier.wait()

def execute(check_history, month_history, history_path, file_path, out_path, internal_page, internal_page_limit):
    try:
        start_time = time.time()
        thread_count = 5
        url_list = get_url_to_scrap(file_path)
        if len(url_list) == 0:
            return ""
        chunk = math.ceil(len(url_list) / thread_count)
        chunk_list = [url_list[i:i + chunk] for i in range(0, len(url_list), chunk)]
        thread_size = len(chunk_list)
        barrier = Barrier(thread_size)
        threads = []
        for i in range(thread_size):
            threads.append(Thread(target=run, args=(chunk_list[i], check_history, month_history, history_path, out_path, internal_page, internal_page_limit, barrier)))
            print("Thread is starting", threads[i])
            threads[-1].start()
            time.sleep(1)

        for thread in threads:
            thread.join()

        # Move file to processed after completed the process
        if not os.path.exists(os.path.dirname(ConstantService.data_processed_path())):
            os.makedirs(os.path.dirname(ConstantService.data_processed_path()))
        shutil.move(file_path, os.path.join(ConstantService.data_processed_path(), os.path.basename(file_path)))

        dest_path = ConstantService.data_processed_path()
        web_summary(out_path)
        zip_file_path = zipdir(out_path, dest_path)


        end_time = time.time()
        print("Processing Time: ", '{:.3f} sec'.format(end_time - start_time))
        return zip_file_path
    except Exception as e:
        print(str(e))

