import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import json
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode

# 配置参数
AUTHORIZATION_URL = "https://jaccount.sjtu.edu.cn/oauth2/authorize"
API_URL = "https://api.sjtu.edu.cn/v1/unicode/transactions"
TOKEN_URL = "https://jaccount.sjtu.edu.cn/oauth2/token"
REDIRECT_URI = "https://net.sjtu.edu.cn"
STATE = ""  
BEGIN_DATE = 1704038400


# 指定字体
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'SimHei'] 


# 请在这里填入你的 CLIENT_ID 和 CLIENT_SECRET
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
    redirect_response = input("登录完毕后，请稍等片刻至跳转到网络信息中心页面\n此时复制浏览器地址栏中的完整链接，并粘贴到这里: ")
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
    response = requests.post(TOKEN_URL, headers=headers, auth=auth, data=data)

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
        response = requests.get(API_URL, params=params)
        
        # 检查请求是否成功
        if response.status_code == 200:
            # 解析响应 JSON 数据
            data = response.json()
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
        print(f"\n请求过程中发生错误，请检查网络或删除目录下的 eat-data.json 文件后重试")


def convert_time(timestamp, time_zone = 8):
    '''
    时间转换
    '''
    # 转换为 UTC 时间
    utc_time = dt.datetime.fromtimestamp(timestamp, tz = dt.timezone.utc)
    # 转换为东八区时间
    converted_time = utc_time.astimezone(dt.timezone(dt.timedelta(hours = time_zone))) 
    return converted_time


def load_eat_data(eat_data, time_zone = 8):
    '''
    加载消费数据
    '''

    data = json.load(eat_data)
    entities = data.get("entities", [])
    df = pd.DataFrame(entities)

    df['amount'] = df['amount'] * -1
    df['orderTime'] = df['orderTime'].apply(lambda x: convert_time(x, time_zone))
    df['payTime'] = df['payTime'].apply(lambda x: convert_time(x, time_zone))

    # 去除年份、秒和时区
    df['formatted_orderTime'] = df['orderTime'].dt.strftime('%m月%d日%H点%M分')
    df['formatted_payTime'] = df['payTime'].dt.strftime('%m月%d日%H点%M分')

    # 提取日期和时分秒
    df['date'] = df['payTime'].dt.date  # 提取日期部分
    df['time'] = df['payTime'].dt.time  # 提取时分秒部分

    return df



def annual_analysis(df):
    '''
    年度消费分析
    '''

    print("\n思源码年度消费报告：")

    # 总消费
    total_value = df['amount'].sum()
    print(f"\n  2024年，你在交大共消费了 {total_value} 元。")

    # 第一笔消费
    first_row = df.iloc[-1]
    print(f"\n  {first_row['formatted_payTime']}，你在 {first_row['merchant']} 开启了第一笔在交大的消费，花了 {first_row['amount']} 元。")
    print("  在交大的每一年都要有一个美好的开始。")

    # 最大消费
    max_row = df.loc[df['amount'].idxmax()]
    print(f"\n  今年 {max_row['formatted_payTime']}，你在交大的 {max_row['merchant']} 单笔最多消费了 {max_row['amount']} 元。")
    print("  哇，真是胃口大开的一顿！") 

    # 最常消费
    most_frequent_merchant = df['merchant'].mode()[0]
    most_frequent_merchant_count = df[df['merchant'] == most_frequent_merchant].shape[0]
    most_frequent_merchant_total = df[df['merchant'] == most_frequent_merchant]['amount'].sum()
    print(f"\n  你最常前往 {most_frequent_merchant} ，一共 {most_frequent_merchant_count} 次，总共花了 {most_frequent_merchant_total} 元。")
    print("  这里的美食真是让你回味无穷。")

    # 最多消费
    most_expensive_merchant = df.groupby('merchant')['amount'].sum().idxmax()
    most_expensive_merchant_count = df[df['merchant'] == most_expensive_merchant].shape[0]
    most_expensive_merchant_total = df.groupby('merchant')['amount'].sum().max()
    print(f"\n  你在 {most_expensive_merchant} 消费最多，{most_expensive_merchant_count} 次消费里，一共花了 {most_expensive_merchant_total} 元。")
    print("  想来这里一定有你钟爱的菜品。")

    # 早中晚消费
    df['hour'] = df['payTime'].dt.hour
    morning = df[(df['hour'] >= 6) & (df['hour'] < 9)]['amount'].shape[0]
    noon = df[(df['hour'] >= 11) & (df['hour'] < 14)]['amount'].shape[0]
    night = df[(df['hour'] >= 17) & (df['hour'] < 19)]['amount'].shape[0]
    print(f"\n  你今年一共在交大吃了 {morning} 顿早餐，{noon} 顿午餐，{night} 顿晚餐。")
    print("  在交大的每一顿都要好好吃饭～")

    # 按日期分组，找到每一天中最早的时间
    earliest_rows_per_day = df.loc[df.groupby('date')['time'].idxmin()]
    overall_earliest_row = earliest_rows_per_day.loc[earliest_rows_per_day['time'].idxmin()]
    print(f"\n  {overall_earliest_row['formatted_payTime']} 是你今年最早的一次用餐，你一早就在 {overall_earliest_row['merchant']} 吃了 {overall_earliest_row['amount']} 元。")

    # # 一天内消费次数分布
    # plt.figure(figsize=(10, 6))
    # plt.hist(df['hour'], bins=24, color='skyblue', edgecolor='black')
    # plt.title('消费时间分布')
    # plt.xlabel('时间')
    # plt.ylabel('消费次数')
    # plt.xticks(range(0, 24))
    # plt.show()

    # 月份消费金额分布
    df['month'] = df['payTime'].dt.month
    most_expensive_month = df.groupby('month')['amount'].sum().idxmax()
    most_expensive_month_total = df.groupby('month')['amount'].sum().max()
    print(f"\n  你在 {most_expensive_month} 月消费最多，一共花了 {most_expensive_month_total} 元。")
    print("  来看看你的月份分布图")


    # 按食堂分组，统计总消费金额
    grouped = df.groupby('merchant')['amount'].sum().sort_values(ascending=False)
    # 计算总消费金额
    total_amount = grouped.sum()
    # 找到占比 >= 1% 的食堂
    threshold = 0.01  # 占比 1%
    major_merchants = grouped[grouped / total_amount >= threshold]
    # 将占比 < 1% 的合并为 "其他"
    other_sum = grouped[grouped / total_amount < threshold].sum()
    # 合并为新的 Series
    final_grouped = pd.concat([major_merchants, pd.Series({'其他': other_sum})])
    

    # 绘图
    fig, axs = plt.subplots(1, 2, figsize=(15, 6))
    final_grouped.plot(
        kind='pie', autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12}, ax=axs[0]
    )

    axs[0].set_ylabel('')  # 去掉 y 轴标签
    axs[0].set_title('各食堂总消费金额分布', fontsize=16)

    df['month'] = df['payTime'].dt.month
    monthly_amount = df.groupby('month')['amount'].sum()
    axs[1].bar(monthly_amount.index, monthly_amount.values, color='skyblue')
    axs[1].set_title('月份消费金额分布', fontsize=16)
    axs[1].set_xlabel('月份', fontsize=12)
    axs[1].set_ylabel('消费金额', fontsize=12)
    axs[1].set_xticks(range(1, 13))  # 确保横坐标是 1 到 12 月份

    # 调整布局和显示
    plt.tight_layout()
    plt.show()


    print("\n不管怎样，吃饭要紧")
    input("2025年也要记得好好吃饭喔(⌒▽⌒)☆ \n")



if __name__ == "__main__":
    try:
        with open("eat-data.json", 'r', encoding='utf-8') as eat_data:
            eat_data_df = load_eat_data(eat_data)
        annual_analysis(eat_data_df)
    except FileNotFoundError:
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
        get_eat_data(access_token)
        with open("eat-data.json", 'r', encoding='utf-8') as eat_data:
            eat_data_df = load_eat_data(eat_data)
        annual_analysis(eat_data_df)

    except Exception:
        print("发生其他错误，请删除目录下的 eat-data.json 文件后重试")
        exit()
