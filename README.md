# :memo: nonebot_plugin_zyk_novelai

*本插件基于Naifu端配置制作*

*:page_facing_up: 使用本插件前请仔细阅读README文档*

## :sparkles: 新版本一览
### :pushpin: version 2.9.5
>都更新了哪些内容？
1. 添加CD功能，CD时间可在env文件中配置。超级用户不受限，白名单用户不受限
2. 添加黑名单和白名单，黑名单用户无法使用生图功能，白名单用户无CD限制。可在env文件中配置
3. 移除 *set_port*，*set_time* 事件响应器（即本地代理端口和生图时间限制仅可在env文件中配置）
4. *check state* 事件响应器更改为命令事件响应器
5. 优化加载全局配置

### :chart_with_upwards_trend: 预计未来更新的内容
1. 更新tag数据库


## :cd: 安装方式
- #### 使用pip
```
pip install nonebot_plugin_zyk_novelai
```
- #### 使用nb-cli
```
nb plugin install nonebot_plugin_zyk_novelai
```

## :rocket: 配置后端（Colab部署）
1. 使用4chan魔改版NovelAILeaks(naifu)的Colab后端：[配置后端](https://colab.research.google.com/drive/1_Ma71L6uGbtt6UQyA3FjqW2lcZ5Bjck-)
    - 配置需要**科学上网**（大陆无法访问Colab）和**谷歌账户**

2. 请按照要求配置好后在**env文件**中填写生成的URL或*使用指令发送给机器人*
    - 注意，URL格式通常为：`https://THIS-IS-A-SAMPLE.trycloudflare.com/` **注意在末尾加上斜杠“/”！**

   ![image](url.png)

3. 发送请求报错：（报EOF相关的错误）
    - 请在**env文件**中填写代理使用的的本地代理端口，并确保开着代理

5. Colab端无法配置问题：普通谷歌账户使用Colab会有GPU使用时限。解决方法：
    - 等一段时间，一般半天或一天就会恢复使用
    - 多开几个谷歌账户轮流使用，重复步骤一
    - 付费购买或订阅
    - 使用本地版Naifu，需要NVIDIA显卡

   ![image](colab.png)

## :wrench: env配置

|         Name          |                    Example                    | Type |       Usage        | Required |
|:---------------------:|:---------------------------------------------:|:----:|:------------------:|:--------:|
|   novelai_post_url    | `https://THIS-IS-A-SAMPLE.trycloudflare.com/` | str  |       后端URL        |    No    |
|  novelai_proxy_port   |                     10809                     | int  |       本地代理端口       |    No    |
|   novelai_img_time    |                      30                       | int  |       生图时间限制       |    No    |
| novelai_withdraw_time |                      20                       | int  |        撤回时间        |    No    |
|    novelai_cd_time    |                      10                       | int  |        CD时间        |    No    |
|  novelai_white_list   |                `[1234567890]`                 | list |     白名单，无CD限制      |    No    |
|  novelai_black_list   |                `[1234567890]`                 | list |    黑名单，无法使用生图功能    |    No    |

## :label: 指令

### 查看当前配置信息
```
(COMMAND_START)check state

eg:
   /check state
```

### 设置后端URL
```
set_url:https://THIS-IS-A-SAMPLE.trycloudflare.com/
```
或直接在env配置文件中填写
```
novelai_post_url=https://THIS-IS-A-SAMPLE.trycloudflare.com/
```

### 普通绘图
```
ai绘图 | AI绘图 | ai作图 | AI作图 [scale=] [steps=] [size=] [seed=] [prompt=] [uc=]

eg：
   ai绘图 steps=50 prompt={masterpiece}, best quality, {1 girl with black long hair and {{red light eyes}} wearing white dress and white leggings}, {loli:2}, full body, {sitting in sofa}, {looking at viewer} AND {dislike and void}, dark background
```

- #### *随机prompt指令参数*

*以图生图和普通模式都可以使用*
1. 不加*prompt参数*默认使用随机prompt，当然tag个数也将随机
2. 使用*随机prompt指令参数*指定tag个数

   ```
   prompt=RandomP (num)
     
   eg：
      prompt=RandomP 30
   ```

### 以图生图

和普通生图指令基本一样
```
以图生图 | img2img (your image) [strength=] [noise=] [scale=] [size=] [seed=] [prompt=] [uc=]

eg：
   img2img (an image) strength=0.5 noise=0.4 size=1024x512
```

- #### :book: 附参数说明

更详细的参数说明见后文

参数strength和noise都是一个*float（浮点）* 类型的数，且应 **<=0.99**

### 搜索魔咒
```
(COMMAND_START)补魔 | 召唤魔咒 | 搜索魔咒 名称

eg：
   /补魔 吊带袜
```

## :bulb: 生图指令参数说明
#### *在使用生图指令时，请严格规范指令格式（参数位置），否则无法触发响应（生图响应器使用正则匹配）*
### 参数支持
普通生图指令支持参数：
- [x] scale *（可选）* 默认**12**
- [x] steps *（可选）* 默认**28**
- [x] seed *（可选）* 默认**随机**
- [x] size *（可选）* 默认**512x768**
- [x] uc *（可选）* 默认 **Naifu通用反咒**
- [x] prompt *（可选）* 默认**随机**

以图生图指令支持参数：
- [x] size *（可选）* 默认**按原图尺寸匹配**
- [x] strength *（可选）* 默认**0.7**
- [x] noise *（可选）* 默认**0.2**
- [x] scale *（可选）* 默认**12**
- [x] seed *（可选）* 默认**随机**
- [x] uc *（可选）* 默认 **Naifu通用反咒**
- [x] prompt *（可选）* 默认**随机**

### :page_with_curl: 参数解释
- **scale**：在高scale下，提示将更紧密地遵循，细节和清晰度更高。低scale通常会导致更大的创作自由度，但清晰度降低

- **steps**：优化图像的迭代次数

- **seed**：图像种子

- **size**：图像尺寸

- **strength**：控制上传图像的更改量。较低的强度将生成更接近原始图像的图像

- **noise**：较高的噪点会增加添加到上传图像的细节，但如果太高，则会导致伪影。通常，噪声应始终小于强度

- **uc**：不需要的内容（反咒）

## :egg: 补充
>:question: 什么是本地代理端口？

本地代理端口指的就是你的**代理软件**所使用的（系统）端口

如何查看本地代理端口？ *（以Windows 10 为例）*

![查看本地代理端口](port.png)

其中的**端口**即你的本地代理端口

>Naifu的正确食用姿势

[Naifu魔咒咏唱：从入门到入土](https://github.com/ZYKsslm/Summoning-Magic-of-Naifu)

---
:bug: 如果发现插件有BUG或有建议，欢迎**合理**提*Issue*

:heart: 最后，如果你喜欢本插件，就请给本插件点个:star:吧
