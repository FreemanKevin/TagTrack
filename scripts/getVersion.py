import requests
import json
import os
from datetime import datetime
from packaging.version import parse, InvalidVersion
from typing import List, Dict, Any

def download_file(url: str) -> Any:
    """从URL获取文件并返回其JSON内容。"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"请求错误: {url}, 错误信息: {e}")
        return None

def parse_version(version: str, format: str = "") -> datetime:
    """通用版本解析函数，根据不同格式解析版本。"""
    try:
        return parse(version.split('-')[0])
    except (ValueError, InvalidVersion):
        return datetime.min

def get_versions(data: List[Dict], service_name: str = "", ik_versions: List[str] = None) -> List[Dict]:
    if service_name.lower() == "elasticsearch":
        data = [d for d in data if any(ik_ver.replace('v', '') in d['version'] for ik_ver in ik_versions)]

    if service_name.lower() == "nacos":
        data = [d for d in data if "-slim" not in d['version']]
    
    data = sorted(data, key=lambda x: parse_version(x['version']), reverse=True)
    
    if service_name.lower() == "nacos":
        major_versions = {}
        for version_info in data:
            major_version = '.'.join(version_info['version'].split('.')[:2])
            if major_version not in major_versions:
                major_versions[major_version] = version_info
                if len(major_versions) == 2:
                    break
        return list(major_versions.values())

    return data[:2]

def get_github_files(base_url: str, repo_path: str, file_list: List[str]) -> Dict[str, Any]:
    files_data = {}
    for file_name in file_list:
        file_url = f"{base_url}/{repo_path}/{file_name}"
        file_content = download_file(file_url)
        if file_content:
            files_data[file_name] = file_content
    return files_data

def get_latest_ik_versions():
    url = "https://api.github.com/repos/infinilabs/analysis-ik/releases"
    response = requests.get(url)
    response.raise_for_status()
    releases = response.json()
    filtered_releases = [release for release in releases if not release['draft'] and not release['prerelease'] and release['tag_name'].lower() != 'latest']
    latest_versions = [release['tag_name'] for release in sorted(filtered_releases, key=lambda x: parse(x['tag_name']), reverse=True)[:2]]
    return latest_versions

# GitHub仓库的基础URL和路径
base_url = "https://raw.githubusercontent.com"
repo_path = "FreemanKevin/DockerPeek/main/data"
file_list = [
    "elasticsearch_versions.json",
    "geoserver_versions.json",
    "minio_versions.json",
    "nacos-server_versions.json",
    "nginx_versions.json",
    "rabbitmq_versions.json",
    "redis_versions.json"
]

# 下载版本文件
files_versions = get_github_files(base_url, repo_path, file_list)

# 获取IK版本
ik_versions = get_latest_ik_versions()

# 处理服务列表
services = ["Elasticsearch", "GeoServer", "Minio", "Nacos", "Nginx", "RabbitMQ", "Redis"]
latest_versions = []
penultimate_versions = []

for service in services:
    file_key = f"{service.lower()}_versions.json" if service != "Nacos" else "nacos-server_versions.json"
    versions = get_versions(files_versions.get(file_key, []), service_name=service, ik_versions=ik_versions if service == "Elasticsearch" else None)
    if len(versions) > 0:
        latest_versions.append({'name': service, 'tag': versions[0]['version']})
    if len(versions) > 1:
        penultimate_versions.append({'name': service, 'tag': versions[1]['version']})

# 写入JSON文件
data_directory = '../data'
os.makedirs(data_directory, exist_ok=True) 

with open(os.path.join(data_directory, 'services_latest_versions.json'), 'w') as f:
    json.dump(latest_versions, f, indent=4)
with open(os.path.join(data_directory, 'services_penultimate_versions.json'), 'w') as f:
    json.dump(penultimate_versions, f, indent=4)