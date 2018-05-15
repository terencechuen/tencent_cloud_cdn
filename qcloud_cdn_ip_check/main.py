import json
import subprocess
import sys

from QcloudApi.qcloudapi import QcloudApi

action_type = sys.argv[1]
client_ip = sys.argv[2]
jail_name = sys.argv[3]

# 模块
module = 'cdn'

# 接口
action = 'QueryCdnIp'

secret_id = ''
secret_key = ''

config = {
    'Region': 'gz',
    'secretId': secret_id,
    'secretKey': secret_key,
    'method': 'get'
}

params = {
    'ips': client_ip
}

f2b_cmd_1 = None
f2b_cmd_2 = None
f2b_cmd_3 = None

if action_type == 'banip':
    service = QcloudApi(module, config)
    qcloud_output = service.call(action, params).decode()
    qcloud_output = json.loads(qcloud_output)

    if qcloud_output['code'] == 0:
        pass
    else:
        error_msg = 'pub_error_code: ' + str(qcloud_output['code']) + ' error_msg: ' + qcloud_output['message']
        print(error_msg)
        sys.exit(0)

    if qcloud_output['codeDesc'] == 'Success':
        pass
    else:
        error_msg = 'codeDesc: ' + str(qcloud_output['code']) + ' error_msg: ' + qcloud_output['message']
        print(error_msg)
        sys.exit(0)

    if qcloud_output['data']['list'][0]['platform'] == 'no':
        f2b_cmd_1 = '/usr/sbin/iptables -I f2b-' + jail_name + ' 1 -s ' + client_ip + ' -j DROP'

    else:
        f2b_cmd_1 = '/usr/bin/fail2ban-client set ' + jail_name + ' unbanip ' + client_ip

elif action_type == 'unbanip':
    f2b_cmd_1 = '/usr/sbin/iptables -D f2b-' + jail_name + ' -s ' + client_ip + ' -j DROP'

elif action_type == 'start':
    f2b_cmd_1 = '/usr/sbin/iptables -N f2b-' + jail_name
    f2b_cmd_2 = '/usr/sbin/iptables -A f2b-' + jail_name + ' -j RETURN'
    f2b_cmd_3 = '/usr/sbin/iptables -I INPUT -j f2b-' + jail_name

elif action_type == 'stop':
    f2b_cmd_1 = '/usr/sbin/iptables -D INPUT -j f2b-' + jail_name
    f2b_cmd_2 = '/usr/sbin/iptables -F f2b-' + jail_name
    f2b_cmd_3 = '/usr/sbin/iptables -X f2b-' + jail_name

f2b_cmd_list = [f2b_cmd_1, f2b_cmd_2, f2b_cmd_3]

for i in f2b_cmd_list:
    if i is None:
        break
    else:
        cmd_output = subprocess.call(i, shell=True)
        print(cmd_output)
