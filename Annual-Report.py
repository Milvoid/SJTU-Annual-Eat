import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import json

# 指定字体
plt.rcParams['font.sans-serif'] = ['MiSans', 'SimHei', 'Hiragino Sans GB', 'Noto Sans SC', 'Noto Sans']

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

    print("\n思源码年度消费报告：")

    # 总消费
    total_value = df['amount'].sum()
    print(f"\n  2024年，你在交大共消费了 {total_value:.2f} 元。")

    # 第一笔消费
    first_row = df.iloc[-1]
    print(f"\n  {first_row['formatted_payTime']}，你在 {first_row['merchant']} 开启了第一笔在交大的消费，花了 {first_row['amount']:.2f} 元。")
    print("  在交大的每一年都要有一个美好的开始。")

    # 最大消费
    max_row = df.loc[df['amount'].idxmax()]
    print(f"\n  今年 {max_row['formatted_payTime']}，你在交大的 {max_row['merchant']} 单笔最多消费了 {max_row['amount']:.2f} 元。")
    print("  哇，真是胃口大开的一顿！")

    # 最常消费
    most_frequent_merchant = df['merchant'].mode()[0]
    most_frequent_merchant_count = df[df['merchant'] == most_frequent_merchant].shape[0]
    most_frequent_merchant_total = df[df['merchant'] == most_frequent_merchant]['amount'].sum()
    print(f"\n  你最常前往 {most_frequent_merchant} ，一共 {most_frequent_merchant_count} 次，总共花了 {most_frequent_merchant_total:.2f} 元。")
    print("  这里的美食真是让你回味无穷。")

    # 最多消费
    most_expensive_merchant = df.groupby('merchant')['amount'].sum().idxmax()
    most_expensive_merchant_count = df[df['merchant'] == most_expensive_merchant].shape[0]
    most_expensive_merchant_total = df.groupby('merchant')['amount'].sum().max()
    print(f"\n  你在 {most_expensive_merchant} 消费最多，{most_expensive_merchant_count} 次消费里，一共花了 {most_expensive_merchant_total:.2f} 元。")
    print("  想来这里一定有你钟爱的菜品。")

    # 早中晚消费
    df['hour'] = df['payTime'].dt.hour
    morning = df[(df['hour'] >= 6) & (df['hour'] < 9)]['amount'].shape[0]
    noon = df[(df['hour'] >= 11) & (df['hour'] < 14)]['amount'].shape[0]
    night = df[(df['hour'] >= 17) & (df['hour'] < 19)]['amount'].shape[0]
    print(f"\n  你今年一共在交大吃了 {morning} 顿早餐，{noon} 顿午餐，{night} 顿晚餐。")
    print("  在交大的每一顿都要好好吃饭～")

    # 按日期分组，找到每一天中最早的时间
    try:
        earliest_rows_per_day = df.loc[df.groupby('date')['time'].idxmin()]
        overall_earliest_row = earliest_rows_per_day.loc[earliest_rows_per_day['time'].idxmin()]
        print(f"\n  {overall_earliest_row['formatted_payTime']} 是你今年最早的一次用餐，你一早就在 {overall_earliest_row['merchant']} 吃了 {overall_earliest_row['amount']:.2f} 元。")
    # 错误似乎是因为pandas版本过低导致的，建议更新
    except Exception:
        print(f"\n  获取每日最早消费时出错，请更新pandas: pip install --upgrade pandas")


    # 月份消费金额分布
    df['month'] = df['payTime'].dt.month
    most_expensive_month = df.groupby('month')['amount'].sum().idxmax()
    most_expensive_month_total = df.groupby('month')['amount'].sum().max()
    print(f"\n  你在 {most_expensive_month} 月消费最多，一共花了 {most_expensive_month_total:.2f} 元。")
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
    fig, axs = plt.subplots(1, 3, figsize=(20, 6))

    # 食堂消费金额饼图
    final_grouped.plot(
        kind='pie', autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12}, ax=axs[0]
    )
    axs[0].set_ylabel('')  # 去掉 y 轴标签
    axs[0].set_title('各食堂总消费金额分布', fontsize=16)

    # 月份消费金额分布
    df['month'] = df['payTime'].dt.month
    monthly_amount = df.groupby('month')['amount'].sum()
    axs[1].bar(monthly_amount.index, monthly_amount.values, color='skyblue')
    axs[1].set_title('月份消费金额分布', fontsize=16)
    axs[1].set_xlabel('月份', fontsize=12)
    axs[1].set_ylabel('消费金额', fontsize=12)
    axs[1].set_xticks(range(1, 13))  # 确保横坐标是 1 到 12 月份

    # 一天内消费时间分布
    axs[2].hist(df['hour'], bins=24, color='skyblue', edgecolor='black')
    axs[2].set_title('一天内消费时间分布', fontsize=16)
    axs[2].set_xlabel('时间 (小时)', fontsize=12)
    axs[2].set_ylabel('消费次数', fontsize=12)
    axs[2].set_xticks(range(0, 24))  # 确保横坐标是 0 到 23 小时

    # 调整布局和显示
    plt.tight_layout()
    try:
        plt.show()
    except Exception:
        print("\n  无法显示图表，输入图片名称以保存图表（可选）")
        filename = input("  图片名称（不需要后缀）：")
        if filename:
            plt.savefig(f"{filename}.png")

    print("\n不管怎样，吃饭要紧")
    input("2025年也要记得好好吃饭喔(⌒▽⌒)☆ \n")



if __name__ == "__main__":
    try:
        with open("eat-data.json", 'r', encoding='utf-8') as eat_data:
            eat_data_df = load_eat_data(eat_data)

        # 现在默认启用过滤
        eat_data_df = filter(eat_data_df)
        annual_analysis(eat_data_df)
    except FileNotFoundError:
        print("\n首次运行，请先运行 Get-Eat-Data 以获取消费数据")
        print("如果已经运行过 Get-Eat-Data，请查看 README 中的问题解答")
        input("按回车键退出...")
    except Exception:
        print("\n发生其他错误")
        input("按回车键退出...")
