import datetime
import gzip
import os
import subprocess
import sys

import requests
from QcloudApi.qcloudapi import QcloudApi

tmp_file_path = sys.path[0] + '/.qcloud_cdn_log_download_main.tmp'
log_tmp_file_path = sys.path[0] + '/log_tmp/'
log_file_path = sys.path[0] + '/log/'

if os.path.exists(tmp_file_path):
    tmp_file_content = subprocess.Popen('/usr/bin/tail -n 1 ' + tmp_file_path, shell=True, stdout=subprocess.PIPE)
    tmp_file_content = tmp_file_content.stdout.readlines()[0]
    tmp_file_content = eval(tmp_file_content)
    start_date = tmp_file_content['log_date']
    tmp_file_content_statue = tmp_file_content['statue']
else:
    start_date = '2018010100'

datetime_now = datetime.datetime.now()
date_now = datetime_now.strftime("%Y-%m-%d %H:%M:%S")
end_date = datetime_now.strftime("%Y-%m-%d %H:00:00")

last_log_time = datetime.datetime.strptime(start_date, '%Y%m%d%H')
time_calculate = (datetime_now - last_log_time).seconds
if time_calculate > 4500:
    need_to_download_log = True
    start_date = datetime.datetime.strftime(last_log_time, '%Y-%m-%d %H:00:00')
else:
    need_to_download_log = False

# 模块
module = 'cdn'

# 接口
action = 'GetCdnLogList'

# 区域

secret_id = ''
secret_key = ''
host_name = ''

config = {
    'Region': 'gz',
    'secretId': secret_id,
    'secretKey': secret_key,
    'method': 'get'
}

params = {
    'host': host_name,
    'startDate': str(start_date),
    'endDate': str(end_date)
}


def process_output(i):
    download_dict = dict()
    i = eval(i)
    if i['code'] == 0 and i['codeDesc'] == 'Success':
        i_data = i['data']['list']
        log_date = i_data[-1]
        log_date = log_date['name'].split('-')[0]
        log_status = i['codeDesc']
        for j in i_data:
            log_filename = j['name']
            log_download_link = j['link']
            download_dict[log_filename] = log_download_link
        return log_date, download_dict, log_status
    else:
        return False, i['message']


def download_log_file(i, j):
    r = requests.get(j, stream=True)
    with open(log_tmp_file_path + i + '.gz', 'wb') as gz:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                gz.write(chunk)
    gz.close()


def uncompress_log_file(i):
    log_gzip = gzip.open(log_tmp_file_path + i + '.gz', 'rb')
    log_text = open(log_file_path + i + '.log', 'wb')
    log_content = log_gzip.read()
    log_text.write(log_content)
    log_gzip.close()
    log_text.close()


def script_log(i, j, k, l):
    script_log_dict = dict()
    script_log_dict['date_now'] = i
    script_log_dict['log_date'] = j
    script_log_dict['statue'] = k
    script_log_dict['message'] = l
    script_log_write = open(tmp_file_path, 'a+')
    script_log_write.write(str(script_log_dict) + '\n')
    script_log_write.close()


if need_to_download_log:
    service = QcloudApi(module, config)
    secretId = secret_id
    service.setSecretId(secretId)
    secretKey = secret_key
    service.setSecretKey(secretKey)
    region = 'gz'
    service.setRegion(region)
    method = 'post'
    service.setRequestMethod(method)
    service.generateUrl(action, params)
    qcloud_output = service.call(action, params).decode()
    qcloud_output = process_output(qcloud_output)
    if qcloud_output[0] is False:
        qcloud_output_loop = 0
        while qcloud_output_loop > 3:
            qcloud_output = process_output(qcloud_output)
            if qcloud_output[0] is not False:
                break
            qcloud_output_loop += 1
else:
    qcloud_output = False, None

if qcloud_output[0] is not False:
    for key, value in qcloud_output[1].items():
        download_link = value.replace('\\', '')
        download_log_file(key, download_link)
        uncompress_log_file(key)
    script_log(str(date_now), qcloud_output[0], qcloud_output[2], 'None')
else:
    script_log(str(date_now), start_date, 'Failure', qcloud_output[1])
