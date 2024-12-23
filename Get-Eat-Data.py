import json
from requests import get, post
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode

# 配置参数
AUTHORIZATION_URL = "https://jaccount.sjtu.edu.cn/oauth2/authorize"
API_URL = "https://api.sjtu.edu.cn/v1/unicode/transactions"
TOKEN_URL = "https://jaccount.sjtu.edu.cn/oauth2/token"
REDIRECT_URI = "https://net.sjtu.edu.cn"
STATE = ""  
BEGIN_DATE = 1704038400

# 设置 client_id 和 client_secret
CLIENT_ID = ""  
CLIENT_SECRET = ""  

def get_authorization_code():
    """
    构造授权请求 URL
    """
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "",
        "state": STATE
    }
    auth_url = f"{AUTHORIZATION_URL}?{urlencode(params)}"
    print(f"\n请在浏览器中打开以下链接并登录:\n{auth_url}\n")

    # 手动输入授权后的回调 URL
    redirect_response = input("登录完毕后，请稍等片刻至跳转到网络信息中心页面\n此时复制浏览器地址栏中的完整链接，并粘贴到这里，按回车确认: ")
    # 提取 code 参数
    from urllib.parse import urlparse, parse_qs
    query_params = parse_qs(urlparse(redirect_response).query)
    return query_params.get("code", [None])[0]

def get_access_token(authorization_code):
    """
    使用授权码获取访问令牌 (Access Token)
    """
    # 构造请求头，使用 Basic Auth 传递 client_id 和 client_secret
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    # 使用 HTTPBasicAuth 自动生成 Basic Authorization 头
    auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)

    # 构造请求体
    data = {
        "grant_type": "authorization_code",  # 固定参数
        "code": authorization_code,         # 授权码
        "redirect_uri": REDIRECT_URI        # 重定向 URI，必须与之前一致
    }

    # 发起 POST 请求到 TOKEN_URL
    response = post(TOKEN_URL, headers=headers, auth=auth, data=data)

    # 检查返回结果
    if response.status_code == 200:
        # 成功获取令牌，返回 JSON 响应
        return response.json()
    else:
        # 发生错误，打印状态码和错误信息
        print("获取令牌失败:")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        return None

def get_eat_data(access_token, begin_date = BEGIN_DATE):
    """
    获取消费数据
    """
    params = {
        "access_token": access_token,
        "channel": "",
        "start": 0,
        "beginDate": begin_date,
        "status": ""
    }

    # 发起请求
    try:
        response = get(API_URL, params=params)
        
        # 检查请求是否成功
        if response.status_code == 200:
            # 解析响应 JSON 数据
            data = response.json()
            
            if data.get('errno', 0) != 0:
                print(data)
                # 防止泄露 client_id 和 client_secret，只放错误码
                error_code = data.get('errno', '无错误码')
                print(f"API 错误: {error_code})")
                raise Exception()
            else:
                print("消费数据获取成功")
                
                # 保存到文件
                with open("eat-data.json", "w", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)
                
                print("\n消费数据已保存")
            
            return data
        else:
            print(f"\n请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"\n请求过程中发生错误，请检查网络及代理设置，或删除目录下的 eat-data.json 文件后重试")


if __name__ == "__main__":
    try:
        print("\n首次运行，请先登录并获取消费数据")
        # 获取授权码
        authorization_code = get_authorization_code()
        if not authorization_code:
            print("\n授权码获取失败，请检查你的返回 URL\n")
            exit()
        print(f"\n取得授权码: {authorization_code}")

        # 获取访问令牌
        token_response = get_access_token(authorization_code)
        access_token = token_response.get('access_token')
        if token_response:
            print("\n成功获取访问令牌(Access Token):")
            print(f"{access_token}\n")

        # 获取消费数据
        if get_eat_data(access_token):
            input("请前往 Annual-Report.py 以继续...")

    except Exception:
        print("Unknown Error：500")
        input("按回车键退出...")
