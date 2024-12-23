import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import json
from jinja2 import Template

# 指定字体
# plt.rcParams['font.sans-serif'] = ['MiSans', 'SimHei', 'Hiragino Sans GB', 'Noto Sans SC', 'Noto Sans']

html_data = {
    'total_spending_text': '',
    'first_spending_text': '',
    'highest_single_spending_text': '',
    'favorite_place_spending_text': '',
    'meal_counts_text': '',
    'earliest_meal_text': '',
    'most_expensive_month_text': '',
    'pie_label_1': '',
    'pie_data_1': '',
    'pie_data_2': ''
}


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

    # 取反并乘100取整，修复浮点精度问题
    df['amount'] = (df['amount'] * -100).round().astype(int)
    df['amount'] = df['amount'] / 100
    df['orderTime'] = df['orderTime'].apply(lambda x: convert_time(x, time_zone))
    df['payTime'] = df['payTime'].apply(lambda x: convert_time(x, time_zone))

    # 去除年份、秒和时区
    df['formatted_orderTime'] = df['orderTime'].dt.strftime('%m月%d日%H点%M分')
    df['formatted_payTime'] = df['payTime'].dt.strftime('%m月%d日%H点%M分')

    # 提取日期和时分秒
    df['date'] = df['payTime'].dt.date  # 提取日期部分
    df['time'] = df['payTime'].dt.time  # 提取时分秒部分

    return df

def filter(df):
    '''
    过滤一些非餐饮消费数据
    '''
    filter_keys = ['电瓶车', '游泳', '核减', '浴室', '教材科' ,'校医院', '充值'] # 需要继续补充
    for k in filter_keys:
        df = df[~df['merchant'].str.contains(k)]
    return df

def annual_analysis(df):
    '''
    年度消费分析
    '''

    # 总消费
    total_value = df['amount'].sum()
    html_data['total_spending_text'] = f"2024年，你在交大共消费了<span class=\"highlight\"> {total_value:.2f} </span>元。"

    # 第一笔消费
    first_row = df.iloc[-1]
    html_data['first_spending_text'] = f"<span class=\"highlight\">{first_row['formatted_payTime']}</span>，你在<span class=\"highlight\"> {first_row['merchant']} </span>开启了第一笔在交大的消费，花了<span class=\"highlight\"> {first_row['amount']:.2f} </span>元。"

    # 最大消费
    max_row = df.loc[df['amount'].idxmax()]
    html_data['highest_single_spending_text'] = f"今年<span class=\"highlight\"> {max_row['formatted_payTime']}</span>，你在交大的<span class=\"highlight\"> {max_row['merchant']} </span>单笔最多消费了<span class=\"highlight\"> {max_row['amount']:.2f} </span>元。"

    # 最常消费
    most_frequent_merchant = df['merchant'].mode()[0]
    most_frequent_merchant_count = df[df['merchant'] == most_frequent_merchant].shape[0]
    most_frequent_merchant_total = df[df['merchant'] == most_frequent_merchant]['amount'].sum()
    html_data['favorite_place_spending_text'] = f"你最常前往<span class=\"highlight\"> {most_frequent_merchant} </span>，一共<span class=\"highlight\"> {most_frequent_merchant_count} </span>次，总共花了<span class=\"highlight\"> {most_frequent_merchant_total:.2f} </span>元。"

    # 早中晚消费
    df['hour'] = df['payTime'].dt.hour
    morning = df[(df['hour'] >= 6) & (df['hour'] < 9)]['amount'].shape[0]
    noon = df[(df['hour'] >= 11) & (df['hour'] < 14)]['amount'].shape[0]
    night = df[(df['hour'] >= 17) & (df['hour'] < 19)]['amount'].shape[0]
    html_data['meal_counts_text'] = f"你今年一共在交大吃了<span class=\"highlight\"> {morning} </span>顿早餐，<span class=\"highlight\"> {noon} </span>顿午餐，<span class=\"highlight\"> {night} </span>顿晚餐。"

    # 按日期分组，找到每一天中最早的时间
    try:
        earliest_rows_per_day = df.loc[df.groupby('date')['time'].idxmin()]
        overall_earliest_row = earliest_rows_per_day.loc[earliest_rows_per_day['time'].idxmin()]
        html_data['earliest_meal_text'] = f"<span class=\"highlight\">{overall_earliest_row['formatted_payTime']} </span>是你今年最早的一次用餐，你一早就在<span class=\"highlight\"> {overall_earliest_row['merchant']} </span>吃了<span class=\"highlight\"> {overall_earliest_row['amount']:.2f} </span>元。"
        # print(f"\n <span class=\"highlight\"> {html_data['earliest_meal_text']}")
    # 错误似乎是因为pandas版本过低导致的，建议更新
    except Exception:
        print(f"\n  获取每日最早消费时出错，请更新pandas: pip install --upgrade pandas")


    # 月份消费金额分布
    df['month'] = df['payTime'].dt.month
    most_expensive_month = df.groupby('month')['amount'].sum().idxmax()
    most_expensive_month_total = df.groupby('month')['amount'].sum().max()

    # 按食堂分组，统计总消费金额
    grouped = df.groupby('merchant')['amount'].sum().sort_values(ascending=False)
    # 计算总消费金额
    total_amount = grouped.sum()
    # 找到占比 >= 1% 的食堂
    threshold = 0.01  # 占比 1%
    major_merchants = grouped[grouped / total_amount >= threshold]
    if len(major_merchants) > 9:
        major_merchants = grouped[:9]
        other_sum = grouped[9:].sum()
    # 将占比 < 1% 的合并为 "其他"
    else:
        other_sum = grouped[grouped / total_amount < threshold].sum()
    # 合并为新的 Series
    final_grouped = pd.concat([major_merchants, pd.Series({'其他': other_sum})])
    html_data['pie_data_1'] = list(final_grouped.values)
    html_data['pie_label_1'] = list(final_grouped.index)

    df['month'] = df['payTime'].dt.month
    monthly_amount = df.groupby('month')['amount'].sum()
    html_data['pie_data_2'] = list(monthly_amount.values)



if __name__ == "__main__":
    try:
        with open("eat-data.json", 'r', encoding='utf-8') as eat_data:
            eat_data_df = load_eat_data(eat_data)

        # 现在默认启用过滤
        eat_data_df = filter(eat_data_df)
        annual_analysis(eat_data_df)

        with open('html-template', 'r', encoding='utf-8') as file:
            template_content = file.read()

        template = Template(template_content)
        rendered_html = template.render(html_data)
        with open('海报.html', 'w', encoding='utf-8') as file:
            file.write(rendered_html)

    except FileNotFoundError:
        print("\n首次运行，请先运行 Get-Eat-Data 以获取消费数据")
        print("如果已经运行过 Get-Eat-Data，请查看 README 中的问题解答")
        input("按回车键退出...")
    except Exception:
        print("\n发生其他错误")
        input("按回车键退出...")
