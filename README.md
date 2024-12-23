# SJTU-Annual-Eat

思源码消费年度总结

来看看你今年都在交大消费了些什么吧

## 快速开始

> 同时支持 Windows 与 macOS（仅测试过 Apple Silicon 版本）

前往 [Release 页面](https://github.com/Milvoid/SJTU-Annual-Eat/releases/tag/1.0.1) 下载 `Release.zip`

解压后得到 `Get-Eat-Data` 与 `Annual-Report.py` 

首先运行  `Get-Eat-Data` ，按照提示获取数据后得到 `eat-data.json`

之后再运行  `Annual-Report.py`  即可生成年度报告啦

## 常见问题及解决

- Annual-Report.py 闪了一下就没了

可能是所需的库没有安装，可以用文本编辑器打开文件，之后查看最上方需要导入的模块是否有缺失

- Access Token 获取失败

可以确认一下自己没有使用代理，sjtu服务器好像会somehow因为代理拒绝访问

- 运行到早中晚餐之后报错

应该是统计最早一餐部分的兼容性问题，可以手动注释掉该部分，或者下载新的 Release 这部分失败之后自动跳过

代码有点bug，按日期分组,找到每一天中最早的时间那边会错误，不知道是不是 pandas 版本问题

如果是 `reduction operation 'argmin' not allowed for this dtype` 问题，可以在函数load_eat_data的最后加一行

```python
df['time_in_seconds'] = df['payTime'].dt.hour * 3600 + df['payTime'].dt.minute * 60 + df['payTime'].dt.second
```

然后把“按日期分组，找到每一天中最早的时间”下面两行中的'time'都改成'time_in_seconds'就行了。

- 运行 Get-Eat-Data 后仍然找不到 json 文件

可以在终端里先 cd 到 json 文件所在路径，之后从终端运行 Annual-Report.py；或者直接把 Annual-Report.py 的文件路径改成绝对路径

## 示例

运行 `Annual-Report.py` 之后，你就可以看到今年的一些 Highlight 以及相关统计图，譬如：

```shell
思源码年度消费报告：

  2024年，你在交大共消费了 1885.17 元。

  01月01日17点43分，你在 闵行三餐外婆桥 开启了第一笔在交大的消费，花了 17.0 元。
  在交大的每一年都要有一个美好的开始。

  今年 02月20日11点56分，你在交大的 教材科 单笔最多消费了 41.5 元。
  哇，真是胃口大开的一顿！

  你在 闵行三餐学生餐厅 消费最多，38 次消费里，一共花了 493.38 元。
  想来这里一定有你钟爱的菜品。

  你今年一共在交大吃了 0 顿早餐，62 顿午餐，55 顿晚餐。
  在交大的每一顿都要好好吃饭～

  05月08日09点57分 是你今年最早的一次用餐，你一早就在 沪FP2215 吃了 6.0 元。

  你在 10 月消费最多，一共花了 308.2 元。
  来看看你的月份分布图

不管怎样，吃饭要紧
2025年也要记得好好吃饭喔(⌒▽⌒)☆ 
```

![example](https://raw.githubusercontent.com/Milvoid/SJTU-Annual-Eat/main/figs/example.png)

## 海报生成

你也可以通过运行下面的脚本来生成一幅简单的海报，你可以用你的浏览器打开```海报.html```和截图。
```
python generate-poster.py
```

![](./figs/example-poster.png)

## Notes

`Get-Eat-Data.exe` 可直接运行；如果需要运行 `Get-Eat-Data.py`，请参考 [SJTU 开发者文档](https://developer.sjtu.edu.cn/auth/oauth.html) 填写 `client_id` 和 `client_secret`

特别感谢来自 Boar 大佬的帮助

以及感谢本仓库帮忙修代码的 Contributors
