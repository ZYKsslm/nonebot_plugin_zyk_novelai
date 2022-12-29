#!usr/bin/env python3
# -*- coding: utf-8 -*-
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment, GROUP, PRIVATE_FRIEND, Bot
from nonebot import on_regex, on_fullmatch, get_driver, on_command
from nonebot.params import CommandArg, RegexGroup, RegexDict
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.exception import ActionFailed

from .work import get_data, get_userid, AsyncDownloadFile, random_prompt, search_tags
from base64 import b64encode, b64decode
from asyncio import sleep
from re import findall, S
from random import randint
from colorama import init, Fore


__version__ = "2.9.4"


# 构造响应器
check_state = on_fullmatch(msg="check state", permission=SUPERUSER, priority=5, block=True)
set_port = on_regex(pattern=r'set_port:(?P<port>.*)', permission=SUPERUSER, priority=5, block=True)
set_url = on_regex(pattern=r'set_url:(?P<url>.*/)', permission=SUPERUSER, priority=5, block=True)
set_time = on_regex(pattern=r'set_time:(?P<time>.*)', permission=SUPERUSER, priority=5, block=True)
search_tag = on_command(cmd="补魔", aliases={"召唤魔咒", "搜索魔咒"}, permission=SUPERUSER, priority=5, block=True)
# 普通生图正则
pattern = r'^(?P<mode>ai绘图|AI绘图|ai作图|AI作图)( scale=(?P<scale>\d+))?( steps=(?P<steps>\d+))?( size=(?P<size>\d+x\d+))?( seed=(?P<seed>\d+))?( prompt=(?P<prompt>.+))?'
process_img = on_regex(pattern=pattern, permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)
# 以图生图正则
img2img_pattern = r'^(img2img|以图生图).*?url=(?P<url>.*);.*?\](.*?strength=(?P<strength>\d\.\d))?(.*?noise=(?P<noise>\d\.\d))?(.*?scale=(?P<scale>\d+))?(.*?size=(?P<size>\d+x\d+))?(.*?seed=(?P<seed>\d+))?(.*?prompt=(?P<prompt>.+))?'
img2img = on_regex(pattern=img2img_pattern, flags=S, permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)

# 获取全局配置
try:
    withdraw_time = get_driver().config.novelai_withdraw_time
    port = get_driver().config.novelai_proxy_port
    post_url = str(get_driver().config.novelai_post_url) + "generate-stream"
    img_time = get_driver().config.novelai_img_time
except AttributeError:
    logger.warning(Fore.LIGHTYELLOW_EX + "缺少env配置项，缺少项将使用默认配置！")
    proxies = None
    port = "None"
    post_url = ""
    img_time = None
    withdraw_time = None
else:
    if port == "None":
        proxies = None
    else:
        try:
            int(port)
        except ValueError:
            logger.warning(Fore.LIGHTYELLOW_EX + "novelai_proxy_port配置项格式错误！")
            proxies = None
        else:
            proxies = {
                "http://": f"http://127.0.0.1:{port}",
                "https://": f"http://127.0.0.1:{port}"
            }

    if img_time == "None":
        img_time = None
    else:
        try:
            img_time = int(img_time)
        except ValueError:
            logger.warning(Fore.LIGHTYELLOW_EX + "novelai_img_time配置项格式错误！")
            img_time = None

    if withdraw_time == "None":
        withdraw_time = None
    else:
        try:
            withdraw_time = float(withdraw_time)
        except ValueError:
            logger.warning(Fore.LIGHTYELLOW_EX + "novelai_withdraw_time配置项格式错误！")
            withdraw_time = None

# 初始化一个全局变量，记录bot的状态（控制bot只能同时接受并处理一次生图请求）
switch = True

# 初始化字体样式（自动重置字体样式）
init(autoreset=True)

logger.success(Fore.LIGHTGREEN_EX + f"成功导入本插件，插件版本为{__version__}")


# 查看后端状态信息
@check_state.handle()
async def _():
    await check_state.send(f"当前后端URL为：{post_url}，本地代理端口号为：{port}，生图时间限制为：{img_time}，撤回时间为{withdraw_time}")
    logger.info(Fore.LIGHTCYAN_EX + f"当前后端URL为：{post_url}，本地代理端口号为：{port}，生图时间限制为：{img_time}，撤回时间为{withdraw_time}")


# 设置生图时间限制
@set_time.handle()
async def _(regex: tuple = RegexGroup()):
    global img_time
    time = regex[0]

    # 判断是否为数字
    try:
        time = int(time)
    except ValueError:
        # 无限制
        if time == "None":
            img_time = None
            logger.success(Fore.LIGHTCYAN_EX + "成功取消生图时间限制")
            await set_time.finish("成功取消生图时间限制")
        else:
            await set_time.finish("请输入有效参数！")
    else:
        img_time = time
        logger.success(Fore.LIGHTCYAN_EX + f"当前生图时间限制：{img_time}")

        await set_time.finish("生图时间限制设置成功，设置将在下一次请求时启用")


# 设置本地代理端口
@set_port.handle()
async def _(regex: tuple = RegexGroup()):
    global port, proxies
    pt = regex[0]

    # 判断是否为数字
    try:
        int(pt)
    except ValueError:
        # 取消代理模式
        if pt == "None":
            port = pt
            proxies = None
            logger.success(Fore.LIGHTCYAN_EX + "成功取消代理模式")
            await set_port.finish("成功取消代理模式")
        else:
            await set_port.finish("请输入有效参数！")
    else:
        port = pt
        proxies = {
            "http://": f"http://127.0.0.1:{port}",
            "https://": f"http://127.0.0.1:{port}"
        }
        logger.success(Fore.LIGHTCYAN_EX + f"当前本地代理端口：{port}")

        await set_port.finish("本地代理端口设置成功，设置将在下一次请求时启用")


# 设置后端URL
@set_url.handle()
async def _(regex: tuple = RegexGroup()):
    global post_url
    url = regex[0]
    post_url = url + "generate-stream"
    logger.success(Fore.LIGHTCYAN_EX + f"当前后端URL：{post_url}")
    await set_url.finish(f"url设置成功，设置将在下一次请求时启用")


# 搜索魔咒
@search_tag.handle()
async def _(event: MessageEvent, msg: Message = CommandArg()):
    id_ = get_userid(event)

    tag = str(msg)
    tags = await search_tags(tag, proxies)

    if tags[0] is False:
        await search_tag.finish(Message(f"[CQ:at,qq={id_}]魔咒搜索失败！"))
    else:
        await search_tag.finish(Message(f"[CQ:at,qq={id_}]魔咒搜索结果：{tags[1]}"))


# 普通生图
@process_img.handle()
async def _(event: MessageEvent, bot: Bot, regex: dict = RegexDict()):
    global switch
    if switch is False:
        await process_img.finish("资源占用中！")

    # 获取用户ID
    id_ = get_userid(event)

    # 生图参数
    seed = regex["seed"]
    scale = regex["scale"]
    steps = regex["steps"]
    size = regex["size"]
    prompt = regex["prompt"]
    uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"

    if seed is None:
        seed = randint(0, pow(2, 32))
    if scale is None:
        scale = 12
    if steps is None:
        steps = 28
    if size is None:
        size = "512x768"

    # 这一段写得很乱，prompt和uc合起来了，要再分一次
    if prompt is None:
        if_randomP = True
        num = randint(0, 1000)
        prompt = random_prompt(num)
        try:
            uc = findall(r'uc=(?P<uc>.+)', str(event.get_plaintext()))[0]
        except IndexError:
            pass
    else:
        # 获取随机prompt
        if "RandomP" in prompt:
            if_randomP = True
            try:
                num = findall(r'RandomP (?P<num>\d+)', prompt)[0]
            except IndexError:
                switch = True
                await process_img.finish(Message(f"[CQ:at,qq={id_}]请输入随机tag条数！"))
            else:
                prompt = random_prompt(num)
        else:
            if_randomP = False

        try:
            uc = findall(r'uc=(?P<uc>.+)', str(event.get_plaintext()))[0]
        except IndexError:
            pass
        else:
            if if_randomP is False:
                prompt = findall(r'(?P<prompt>.+) uc', prompt)[0]

    # 处理图片尺寸
    try:
        size = size.split("x")
    except AttributeError:
        size = [512, 512]
    size = [int(size[0]), int(size[1])]
    if size[0] > 1024 or size[1] > 1024:
        switch = True
        await process_img.finish(Message(f"[CQ:at,qq={id_}]图片尺寸过大，请重新输入！"))

    # 获取用户名
    name = (await bot.get_stranger_info(user_id=int(id_)))["nickname"]

    await process_img.send(Message(fr"[CQ:at,qq={id_}]正在生成图片，请稍等..."))
    logger.info(
        Fore.LIGHTYELLOW_EX +
        f"\n开始生成{name}的图片："
        f"\nscale={scale}"
        f"\nsteps={steps}"
        f"\nsize={size[0]},{size[1]}"
        f"\nseed={seed}"
        f"\nprompt={prompt}"
        f"\nnegative prompt={uc}"
    )
    switch = False
    data = await get_data(post_url=post_url, size=size, prompt=prompt, proxies=proxies, timeout=img_time, uc=uc, steps=steps, scale=scale,
                          seed=seed)

    if data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败:{data[1]}")
        await process_img.finish(Message(f"[CQ:at,qq={id_}]生成失败"))

    logger.success(Fore.LIGHTGREEN_EX + f"{name}的图片生成成功")

    # 把base64字符串转成bytes
    image = b64decode(data[1])
    msg = Message(f"[CQ:at,qq={id_}]\n{prompt}") + MessageSegment.image(image) if if_randomP == True else Message(
        f"[CQ:at,qq={id_}]") + MessageSegment.image(image)
    switch = True

    try:
        msg_id = (await process_img.send(msg))["message_id"]
    except ActionFailed:
        switch = True
        logger.warning(Fore.LIGHTYELLOW_EX + "Bot可能被风控，请稍后再试")
        await search_tag.finish(Message(f"[CQ:at,qq={id_}]Bot可能被风控，请稍后再试"))
    else:
        if withdraw_time is not None:
            await sleep(withdraw_time)
            await bot.delete_msg(message_id=msg_id)


# 以图生图
@img2img.handle()
async def _(event: MessageEvent, bot: Bot, regex: dict = RegexDict()):
    global switch
    if switch is False:
        await process_img.finish("资源占用中！")

    id_ = get_userid(event)

    img_url = regex["url"]
    strength = regex["strength"]
    noise = regex["noise"]
    seed = regex["seed"]
    scale = regex["scale"]
    size = regex["size"]
    prompt = regex["prompt"]
    uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"

    if strength is None:
        strength = 0.7
    else:
        if float(strength) > 0.99:
            switch = True
            await img2img.finish(Message(f"[CQ:at,qq={id_}]strength过大！（不能超过0.99）"))

    if noise is None:
        noise = 0.2
    else:
        if float(noise) > 0.99:
            switch = True
            await img2img.finish(Message(f"[CQ:at,qq={id_}]noise过大！（不能超过0.99）"))

    if seed is None:
        seed = randint(0, pow(2, 32))
    if scale is None:
        scale = 12

    if size is None:
        size = "512x768"
    # 处理图片尺寸
    try:
        size = size.split("x")
    except AttributeError:
        size = [512, 512]
    size = [int(size[0]), int(size[1])]
    if size[0] > 1024 or size[1] > 1024:
        switch = True
        await img2img.finish(Message(f"[CQ:at,qq={id_}]图片尺寸过大，请重新输入"))

    if prompt is None:
        if_randomP = True
        num = randint(0, 1000)
        prompt = random_prompt(num)
        try:
            uc = findall(r'uc=(?P<uc>.+)', str(event.get_plaintext()))[0]
        except IndexError:
            pass
    else:
        # 获取随机prompt
        if "RandomP" in prompt:
            if_randomP = True
            try:
                num = findall(r'RandomP (?P<num>\d+)', prompt)[0]
            except IndexError:
                switch = True
                await process_img.finish(Message(f"[CQ:at,qq={id_}]请输入随机tag条数！"))
            else:
                prompt = random_prompt(num)
        else:
            if_randomP = False

        try:
            uc = findall(r'uc=(?P<uc>.+)', str(event.get_plaintext()))[0]
        except IndexError:
            pass
        else:
            if if_randomP is False:
                prompt = findall(r'(?P<prompt>.+) uc', prompt)[0]

    switch = False
    await img2img.send(Message(f"[CQ:at,qq={id_}]正在获取图片"))
    name = (await bot.get_stranger_info(user_id=int(id_)))["nickname"]
    logger.info(Fore.LIGHTYELLOW_EX + f"开始获取{name}发送的图片")
    # 下载用户发的图片
    img_data = await AsyncDownloadFile(url=img_url, proxies=proxies)

    if img_data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"{name}发送的图片获取失败:{img_data[1]}")
        await img2img.finish(Message(fr"[CQ:at,qq={id_}]图片获取失败！"))

    logger.success(Fore.LIGHTGREEN_EX + f"{name}发送的图片获取成功")

    await img2img.send(Message(fr"[CQ:at,qq={id_}]正在生成图片，请稍等..."))

    # 先把bytes转成base64，再用utf-8编码
    img = b64encode(img_data[1]).decode("utf-8")
    mode = "以图生图"
    switch = False
    logger.info(
        Fore.LIGHTYELLOW_EX +
        f"\n开始生成{name}的图片："
        f"\nstrength={strength}"
        f"\nnoise={noise}"
        f"\nscale={scale}"
        "\nsteps=50"
        f"\nsize={size[0]},{size[1]}"
        f"\nseed={seed}"
        f"\nprompt={prompt}"
        f"\nnegative prompt={uc}"
    )
    data = await get_data(post_url=post_url, size=size, prompt=prompt, proxies=proxies, timeout=img_time, img=img, mode=mode,
                          strength=strength, noise=noise, scale=scale, steps=50, seed=seed, uc=uc)

    if data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败:{data[1]}")
        await img2img.finish(Message(f"[CQ:at,qq={id_}]生成失败：{data[1]}"))

    logger.success(Fore.LIGHTGREEN_EX + f"{name}的图片生成成功")

    image = b64decode(data[1])
    msg = Message(f"[CQ:at,qq={id_}]\n{prompt}") + MessageSegment.image(image) if if_randomP == True else Message(
        f"[CQ:at,qq={id_}]") + MessageSegment.image(image)
    switch = True

    try:
        msg_id = (await img2img.send(msg))["message_id"]
    except ActionFailed:
        switch = True
        logger.warning(Fore.LIGHTYELLOW_EX + "Bot可能被风控，请稍后再试")
        await search_tag.finish(Message(f"Bot可能被风控，请稍后再试"))
    else:
        if withdraw_time is not None:
            await sleep(withdraw_time)
            await bot.delete_msg(message_id=msg_id)