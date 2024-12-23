# SJTU-Annual-Eat

思源码消费年度总结

来看看你今年都在交大消费了些什么吧

## 快速开始

前往 [Release 页面](https://github.com/Milvoid/SJTU-Annual-Eat/releases/tag/1.0.0) 下载 `Release.zip`

解压后得到 `Get-Eat-Data.exe` 与 `Annual-Report.py` 

首先运行  `Get-Eat-Data.exe` ，按照提示获取数据后得到 `eat-data.json`

之后再运行  `Annual-Report.py`  即可生成年度报告啦

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

![example](https://raw.githubusercontent.com/Milvoid/SJTU-Annual-Eat/main/example.png)

## Notes

`Get-Eat-Data.exe` 可直接运行；如果需要运行 `Get-Eat-Data.py`，请参考 [SJTU 开发者文档](https://developer.sjtu.edu.cn/auth/oauth.html) 填写 `client_id` 和 `client_secret`

特别感谢来自 Boar 大佬的帮助
