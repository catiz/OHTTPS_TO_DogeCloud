from hashlib import sha1, md5
import hmac
import requests
import json
import urllib
from typing import Set, Union
from fastapi import FastAPI
from pydantic import BaseModel
import pymysql


Token = "令牌"  # OHTTPS设置的令牌，别忘了在下面设置多吉云的ak and sk in line 73

def update_new_ssl_id(old_id, new_id):
    db = pymysql.connect(host='127.0.0.1',
                         user='user',
                         password='password',
                         database='database',
                         port=3306)

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    upsql = "UPDATE `sslid` SET `id`=%d WHERE `id`=%d;" % (new_id, old_id)
    # 更新数据库
    cursor.execute(upsql)
    db.commit()

    # 关闭数据库连接
    db.close()


def get_old_ssl_id():
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1',
                         user='user',
                         password='password',
                         database='database',
                         port=3306)

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    # 使用 execute()  方法执行 SQL 查询
    cursor.execute("SELECT id from sslid")

    # 使用 fetchone() 方法获取单条数据.
    data = cursor.fetchone()

    # 关闭数据库连接
    db.close()

    return data[0]


def dogecloud_api(api_path, data={}, json_mode=False):
    """
    调用多吉云API

    :param api_path:    调用的 API 接口地址，包含 URL 请求参数 QueryString，例如：/console/vfetch/add.json?url=xxx&a=1&b=2
    :param data:        POST 的数据，字典，例如 {'a': 1, 'b': 2}，传递此参数表示不是 GET 请求而是 POST 请求
    :param json_mode:   数据 data 是否以 JSON 格式请求，默认为 false 则使用表单形式（a=1&b=2）

    :type api_path: string
    :type data: dict
    :type json_mode bool

    :return dict: 返回的数据
    """

    # 这里替换为你的多吉云永久 AccessKey 和 SecretKey，可在用户中心 - 密钥管理中查看
    # 请勿在客户端暴露 AccessKey 和 SecretKey，否则恶意用户将获得账号完全控制权
    access_key = 'AccessKey'
    secret_key = 'SecretKey'

    if json_mode:
        body = json.dumps(data)
        mime = 'application/json'
    else:
        body = urllib.parse.urlencode(data)  # Python 2 可以直接用 urllib.urlencode
        mime = 'application/x-www-form-urlencoded'
    sign_str = api_path + "\n" + body
    signed_data = hmac.new(secret_key.encode('utf-8'), sign_str.encode('utf-8'), sha1)
    sign = signed_data.digest().hex()
    authorization = 'TOKEN ' + access_key + ':' + sign
    response = requests.post('https://api.dogecloud.com' + api_path, data=body, headers={
        'Authorization': authorization,
        'Content-Type': mime
    })
    return response.json()


def upload_ssl(name, cert, private):
    # 在下面的代码行中使用断点来调试脚本。
    api = dogecloud_api('/cdn/cert/upload.json', {
        "note": name,
        "cert": cert,
        "private": private,
    })
    if api['code'] == 200:
        # print(api['data']['id'])
        return "success", api['data']['id']
    else:
        # print("api failed: " + api['msg'])  # 失败
        return "error", "api failed: " + api['msg']


def binding(cert_id, old_id):
    api = dogecloud_api('/cdn/domain/list.json')
    if api['code'] == 200:
        for domain in api['data']['domains']:
            if domain['cert_id'] == old_id:  # 当前的证书ID，需要存在数据库中，或者通过接口获取通配符证书下的任意一域名绑定的证书ID
                print("正在绑定域名：" + domain['name'] + "\n")
                dogecloud_api('/cdn/domain/config.json?domain=' + domain['name'], {
                    'cert_id': cert_id
                }, True)  # Dogecloud官方文档中API中没有此接口，但在SDK中展示了，没有具体的使用方法以及返回参数
        return True
    else:
        print("api failed: " + api['msg'])  # 失败
        return False, "api failed: " + api['msg']


class certificate_information(BaseModel):
    certificateName: str
    certificateDomains: Set[str] = set()
    certificateCertKey: str
    certificateFullchainCerts: str
    certificateExpireAt: int


class OHTTP_Json(BaseModel):
    timestamp: int
    payload: certificate_information
    sign: str


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/Dogecloud_SSL")
def read_ssl(json_text: OHTTP_Json):
    if json_text.sign == md5((str(json_text.timestamp) + ":" + Token).encode()).hexdigest():
        print("密钥正确\n正在上传证书")
        upload_results = upload_ssl(json_text.timestamp, json_text.payload.certificateFullchainCerts, json_text.payload.
                                    certificateCertKey)
        if upload_results[0] == "success":
            old_ssl_id = get_old_ssl_id()
            print("证书上传完成\n新证书ID为：" + str(upload_results[1]) + "\n老证书ID为：" + str(old_ssl_id) + "\n正在重新绑定证书")
            if binding(upload_results[1], old_ssl_id):
                update_new_ssl_id(old_ssl_id, upload_results[1])
                print("证书更新成功")
                return {"success": "true"}
            else:
                return {"success": "error"}
        if upload_results[0] == "error":
            print(upload_results[1])
            return {"success": "false"}
    else:
        return {"success": "false"}
