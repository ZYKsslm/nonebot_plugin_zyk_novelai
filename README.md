# nonebot_plugin_zyk_novelai

### 基于4chan魔改版NovelAILeaks(naifu)制作，白嫖的就不要什么自行车了。（基础版，功能后面会陆续加上）

### 安装方式
```
pip install nonebot_plugin_zyk_novelai
```
或
```
nb plugin install nonebot_plugin_zyk_novelai
```

### 配置后端
1. 配置需要**科学上网**（大陆无法访问colab）和**谷歌账号**
   - 后端配置地址：[配置后端](https://colab.research.google.com/drive/1_Ma71L6uGbtt6UQyA3FjqW2lcZ5Bjck-)
   - 请按照要求配置好后在[设置](config.py)中填写url或*使用指令发送给机器人*（推荐直接发送给机器人）
2. 注意，url格式通常为：https://THIS-IS-A-SAMPLE.trycloudflare.com/ **末尾的斜杠“/”不能少！**

### 注意事项
1. 如果[设置](config.py)中已填写url，那么将无法用指令让bot更改
2. 请在[设置](config.py)中设置代理使用的的本地端口，并确保开着代理，不然可能发送不了请求 （*报EOF相关的错误*）

### [设置](config.py)
怕有人忘记就写一下 ~~虽然就两个变量，但比较有仪式感不是么~~

|                   get_url                    |  proxy_port  |
|:--------------------------------------------:|:------------:|
| https://THIS-IS-A-SAMPLE.trycloudflare.com/  |  port number |

### 用法
#### *不愿意看的可以直接去看源码*

查看当前后端URL

      查看后端

      查看url

      查看后端url

      check url


设置后端URL
```
set_url:https://THIS-IS-A-SAMPLE.trycloudflare.com/
```

普通绘图指令

      ai绘图 | AI绘图 | ai作图 | AI作图 size= prompt=

      例子：
         ai绘图 size=512x512 prompt={solo}, {{masterpiece}}, {{best quality}}, finely detail, meticulous painting

以图生图指令

和普通的差不多，只是开头不一样，例子就不给了

      以图生图 size= prompt=
