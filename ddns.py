import json
import urllib.request
import urllib.error
import sys
import os

CONFIG_FILE = 'config.json'

import subprocess
import re

def get_ipv6():
    """获取本机公网 IPv6 地址，优先尝试本地命令"""
    # 1. 尝试通过 ip addr 获取全球单播地址 (Global Unicast Address)
    try:
        # 过滤 scope global 且非 dynamic (可选) 的 AAAA 地址
        output = subprocess.check_output(['ip', '-6', 'addr', 'show', 'scope', 'global'], stderr=subprocess.STDOUT).decode()
        # 匹配非临时地址 (prefer_lft forever) 或根据需要调整正则
        # 这里寻找典型的 IPv6 地址格式
        ips = re.findall(r'inet6 ([a-f0-9:]+)/\d+ scope global', output)
        for ip in ips:
            # 排除链路本地地址和回环地址 (虽然 scope global 已经过滤了一部分)
            if not ip.startswith('fe80') and not ip.startswith('::1'):
                return ip
    except Exception as e:
        print(f"Local detection failed: {e}")

    # 2. 如果本地获取失败，尝试外部 API
    urls = ['https://api64.ipify.org?format=json', 'https://v6.ident.me/.json']
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                ip = data.get('ip') or data.get('origin')
                if ip and ':' in ip:
                    return ip
        except Exception:
            continue
    return None

def cf_api(endpoint, token, method='GET', data=None):
    """调用 Cloudflare API"""
    url = f"https://api.cloudflare.com/client/v4/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode()
        
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def update_ddns():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found.")
        return

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    token = config['api_token']
    zone_id = config['zone_id']
    record_name = config['record_name']

    current_ip = get_ipv6()
    if not current_ip:
        print("Could not detect public IPv6 address.")
        return

    print(f"Current IPv6: {current_ip}")

    # 1. 获取已有的 DNS 记录
    records = cf_api(f"zones/{zone_id}/dns_records?name={record_name}&type=AAAA", token)
    
    if records and records.get('result'):
        # 更新现有记录
        record = records['result'][0]
        record_id = record['id']
        old_ip = record['content']

        if old_ip == current_ip:
            print(f"IP has not changed ({old_ip}). No update needed.")
            return

        print(f"Updating {record_name} from {old_ip} to {current_ip}...")
        update_data = {
            "type": "AAAA",
            "name": record_name,
            "content": current_ip,
            "ttl": 1,
            "proxied": config.get('proxied', False)
        }
        result = cf_api(f"zones/{zone_id}/dns_records/{record_id}", token, 'PUT', update_data)
    else:
        # 自动创建新记录
        print(f"Record {record_name} not found, creating new AAAA record with {current_ip}...")
        create_data = {
            "type": "AAAA",
            "name": record_name,
            "content": current_ip,
            "ttl": 1,
            "proxied": config.get('proxied', False)
        }
        result = cf_api(f"zones/{zone_id}/dns_records", token, 'POST', create_data)

    if result and result.get('success'):
        print("Success!")
    else:
        print("Operation failed.")

if __name__ == "__main__":
    update_ddns()
