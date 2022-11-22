# :memo: nonebot_plugin_zyk_novelai

### 基于4chan魔改版NovelAILeaks(naifu)制作，白嫖的就不要什么自行车了。（基础版，功能后面会陆续加上）

### 安装方式
#### 使用pip
```
pip install nonebot_plugin_zyk_novelai
```
#### 或使用nb-cli
```
nb plugin install nonebot_plugin_zyk_novelai
```

### 配置后端
1. 后端配置地址：[配置后端](https://colab.research.google.com/drive/1_Ma71L6uGbtt6UQyA3FjqW2lcZ5Bjck-)
   - 配置需要**科学上网**（大陆无法访问colab）和**谷歌账号**

2. 请按照要求配置好后在**env**中填写生成的url*或使用指令发送给机器人*
   - 注意，url格式通常为：`https://THIS-IS-A-SAMPLE.trycloudflare.com/` **末尾的斜杠“/”不能少！**

3. 请在**env**中填写代理使用的的本地端口*或使用指令发送给机器人*，并确保开着代理，不然可能发送不了请求 *（报EOF相关的错误）*

### :wrench: env配置

|               novelai_post_url                | novelai_proxy_port |
|:---------------------------------------------:|:------------------:|
| `https://THIS-IS-A-SAMPLE.trycloudflare.com/` |       10809        |

### 指令
#### :clown_face: *不愿意看的可以直接去看源码*

- #### 查看当前配置信息
```
check state
```

- #### 设置后端URL
```
set_url:https://THIS-IS-A-SAMPLE.trycloudflare.com/
```

- #### 设置本地代理端口
```
set_port:10809
```

- #### 普通绘图
```
ai绘图 | AI绘图 | ai作图 | AI作图 size= prompt=

例：
   ai绘图 size=512x512 prompt={solo}, {{masterpiece}}, {{best quality}}, finely detail, meticulous painting
```

- #### 以图生图

除了开头和普通生图指令一样
```
以图生图 | img2img size= prompt=
```

>#### 附
>
>随机prompt
>
>*以图生图和普通模式都可以使用*
>```
>prompt=RandomP 条数
>
>例：
>   ai绘图 size=512x512 prompt=RandomP 10
>```

- #### 搜索魔咒
```
(COMMAND_START)补魔 中文名

例：
   /补魔 黑丝
```