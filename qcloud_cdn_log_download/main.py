import datetime
import gzip
import sys, os
import json

import requests
from QcloudApi.qcloudapi import QcloudApi

script_base_path = sys.path[0]

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


# 读取临时文件
def read_tmp_file(i_tmp_log_path):
    # 读取临时文件
    try:
        open_tmp_file = open(i_tmp_log_path + '/tmp.log', 'r')
    except IOError:
        start_date = False
    else:
        start_date = open_tmp_file.read()
        open_tmp_file.close()
    return start_date


# 获取现在时间
datetime_now = datetime.datetime.now()
date_now = datetime_now.strftime("%Y-%m-%d %H:%M:%S")


# 下载日志文件
def download_log_file(i_zip_filename, i_zip_file_link, i_log_path):
    r = requests.get(i_zip_file_link, stream=True)
    if r.status_code == 200:
        with open(i_log_path + '/' + i_zip_filename + '.gz', 'wb') as gz:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    gz.write(chunk)
        gz.close()
        return True
    else:
        return r.status_code


# 解压日志文件
def uncompress_log_file(i_zip_file_name, i_zip_file_path, i_unzip_file_path):
    log_gzip = gzip.open(i_zip_file_path + '/' + i_zip_file_name + '.gz', 'rb')
    log_text = open(i_unzip_file_path + '/' + i_zip_file_name + '.log', 'wb')
    log_content = log_gzip.read()
    log_text.write(log_content)
    log_gzip.close()
    log_text.close()


# 写入日志
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


# 写入临时文件
def write_tmp_log(i_tmp_log_path, log_date):
    open_file = open(i_tmp_log_path + '/tmp.log', 'w')
    open_file.write(str(log_date))
    open_file.close()


# 解析腾讯返还的内容，形成列表
def process_output(i_qcloud_output):
    download_dict = dict()
    i_qcloud_output = eval(i_qcloud_output)
    if i_qcloud_output['code'] == 0 and i_qcloud_output['codeDesc'] == 'Success':
        i_data = i_qcloud_output['data']['list']
        for i in i_data:
            if i['type'] == 1:
                download_dict[i['name']] = i['link']
            else:
                pass
        return True, download_dict
    else:
        return False, i_qcloud_output['message']


# 索取日志列表
def get_download_link(params, config):
    service = QcloudApi('cdn', config)
    service.setRequestMethod('post')
    service.generateUrl('GetCdnLogList', params)
    req_qcloud = service.call('GetCdnLogList', params).decode()
    qcloud_output = process_output(req_qcloud)
    # 如果获取列表失败，则尝试3次
    if qcloud_output[0] is False:
        qcloud_output_loop = 0
        while qcloud_output_loop > 3:
            qcloud_output = process_output(service.call('GetCdnLogList', params).decode())
            if qcloud_output[0] is not False:
                break
            qcloud_output_loop += 1
    return qcloud_output


# 写入日志
def download_log(qcloud_output, i_log_zip_path, i_log_txt_path):
    if qcloud_output[0] is not False:
        for key, value in qcloud_output[1].items():
            download_link = value.replace('\\', '')
            download_status = download_log_file(key, download_link, i_log_zip_path)
            if download_status is True:
                uncompress_log_file(key, i_log_zip_path, i_log_txt_path)
            else:
                pass
            write_log_file(str(date_now), key, str(download_status), 'None')
    else:
        write_log_file(str(date_now), 'none', 'Failure', qcloud_output[1])


# 创建目录
def chk_dir(i_domain):
    log_base_path = script_base_path + '/datastore/' + i_domain
    log_zip_path = log_base_path + '/log_zip'
    log_txt_path = log_base_path + '/log_txt'
    if os.path.exists(log_zip_path):
        pass
    else:
        os.makedirs(log_zip_path)

    if os.path.exists(log_txt_path):
        pass
    else:
        os.makedirs(log_txt_path)

    path_dict = dict()
    path_dict['base'] = log_base_path
    path_dict['zip'] = log_zip_path
    path_dict['txt'] = log_txt_path
    return path_dict


def run(i_hostname):
    cdn_config = {
        'Region': 'gz',
        'secretId': config_json['secret_id'],
        'secretKey': config_json['secret_key'],
        'method': 'get'
    }

    dir_path = chk_dir(i_hostname)
    last_download_date = read_tmp_file(dir_path['base'])

    # 没有临时文件，临时文件从未创建，需下载全部日志
    if last_download_date is False:
        cdn_params = {
            'host': i_hostname
        }
        cdn_log_download_link = get_download_link(cdn_params, cdn_config)
        download_log(cdn_log_download_link, dir_path['zip'], dir_path['txt'])
        write_tmp_log(dir_path['base'], date_now)
    # 有临时文件，获取到最后下载日志的时间，需与现在的时间相比较
    else:
        last_download_date = datetime.datetime.strptime(last_download_date, '%Y-%m-%d %H:%M:%S')
        time_calculate = (datetime_now - last_download_date).seconds
        if time_calculate > 4500:
            last_download_date = datetime.datetime.strftime(last_download_date, '%Y-%m-%d %H:00:00')
            end_date = datetime_now.strftime("%Y-%m-%d %H:00:00")
            cdn_params = {
                'host': i_hostname,
                'startDate': str(last_download_date),
                'endDate': str(end_date)
            }
            cdn_log_download_link = get_download_link(cdn_params, cdn_config)
            download_log(cdn_log_download_link, dir_path['zip'], dir_path['txt'])
            write_tmp_log(dir_path['base'], date_now)
        else:
            pass


if __name__ == '__main__':
    for cdn_domain in config_json['host_name']:
        run(cdn_domain)
