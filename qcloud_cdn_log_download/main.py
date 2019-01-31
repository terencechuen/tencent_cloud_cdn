import datetime
import gzip
import sys
import json

import requests
from QcloudApi.qcloudapi import QcloudApi

tmp_file_path = sys.path[0] + '/.tmp.log'
log_file_path = sys.path[0] + '/download.log'
log_zip_file_path = sys.path[0] + '/log_zip/'
log_unzip_file_path = sys.path[0] + '/log_txt/'
config_file_path = sys.path[0] + '/config.json'

# 定义变量
config_json = {}

# 读取配置文件
try:
    open_config = open(config_file_path, 'r')
except IOError as e:
    print(str(e))
    exit(1)
else:
    config_content = open_config.read()
    config_json = json.loads(config_content)
    open_config.close()


def read_tmp_file(i_tmp_log_path):
    # 读取临时文件
    try:
        open_tmp_file = open(tmp_file_path, 'r')
    except IOError:
        start_date = False
    else:
        start_date = open_tmp_file.read()
        open_tmp_file.close()
    return start_date


datetime_now = datetime.datetime.now()
date_now = datetime_now.strftime("%Y-%m-%d %H:%M:%S")


def process_output(i):
    download_dict = dict()
    i = eval(i)
    if i['code'] == 0 and i['codeDesc'] == 'Success':
        i_data = i['data']['list']
        for j in i_data:
            if j['type'] == 1:
                download_dict[j['name']] = j['link']
            else:
                pass
        return True, download_dict
    else:
        return False, i['message']


def download_log_file(i_zip_file_name, i_zip_file_link, i_zip_file_path):
    r = requests.get(i_zip_file_link, stream=True)
    if r.status_code == 200:
        with open(i_zip_file_path + i_zip_file_name + '.gz', 'wb') as gz:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    gz.write(chunk)
        gz.close()
        return True
    else:
        return r.status_code


def uncompress_log_file(i_zip_file_name, i_zip_file_path, i_unzip_file_path):
    log_gzip = gzip.open(i_zip_file_path + i_zip_file_name + '.gz', 'rb')
    log_text = open(i_unzip_file_path + i_zip_file_name + '.log', 'wb')
    log_content = log_gzip.read()
    log_text.write(log_content)
    log_gzip.close()
    log_text.close()


def write_log_file(i_date_now, i_log_date, i_statue, i_message):
    """
    script_log_dict = dict()
    script_log_dict['date_now'] = i_date_now
    script_log_dict['log_date'] = i_log_date
    script_log_dict['statue'] = i_statue
    script_log_dict['message'] = i_message
    """
    script_log_write = open(log_file_path, 'a+')
    script_log_write.write('download_date:' + str(i_date_now) + ' log_name:' + str(
        i_log_date) + ' statue:' + i_statue + ' message:' + i_message + '\n')
    script_log_write.close()


def write_tmp_log(log_date):
    open_file = open(tmp_file_path, 'w')
    open_file.write(str(log_date))
    open_file.close()


def get_download_link(params, config):
    service = QcloudApi('cdn', config)
    service.setRequestMethod('post')
    service.generateUrl('GetCdnLogList', params)
    qcloud_output = service.call('GetCdnLogList', params).decode()
    qcloud_output = process_output(qcloud_output)
    if qcloud_output[0] is False:
        qcloud_output_loop = 0
        while qcloud_output_loop > 3:
            qcloud_output = process_output(qcloud_output)
            if qcloud_output[0] is not False:
                break
            qcloud_output_loop += 1
    return qcloud_output


def download_log(qcloud_output):
    if qcloud_output[0] is not False:
        for key, value in qcloud_output[1].items():
            download_link = value.replace('\\', '')
            download_status = download_log_file(key, download_link)
            if download_status is True:
                uncompress_log_file(key)
            else:
                pass
            write_log_file(str(date_now), key, str(download_status), 'None')
    else:
        write_log_file(str(date_now), start_date, 'Failure', qcloud_output[1])


def run(i_start_date):
    cdn_config = {
        'Region': 'gz',
        'secretId': config_json['secret_id'],
        'secretKey': config_json['secret_key'],
        'method': 'get'
    }

    if i_start_date is False:
        cdn_params = {
            'host': config_json['host_name']
        }
        cdn_log_download_link = get_download_link(cdn_params, cdn_config)
        download_log(cdn_log_download_link)
        write_tmp_log(date_now)
    else:
        last_log_time = datetime.datetime.strptime(i_start_date, '%Y-%m-%d %H:%M:%S')
        time_calculate = (datetime_now - last_log_time).seconds
        if time_calculate > 4500:
            i_start_date = datetime.datetime.strftime(last_log_time, '%Y-%m-%d %H:00:00')
            end_date = datetime_now.strftime("%Y-%m-%d %H:00:00")
            cdn_params = {
                'host': config_json['host_name'],
                'startDate': str(i_start_date),
                'endDate': str(end_date)
            }
            cdn_log_download_link = get_download_link(cdn_params, cdn_config)
            download_log(cdn_log_download_link)
            write_tmp_log(date_now)
        else:
            pass


if __name__ == '__main__':
    run(start_date)
