#!usr/bin/env python3
# -*- coding: utf-8 -*-
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, GROUP, PRIVATE_FRIEND, Bot, Message
from nonebot import on_regex, on_command
from nonebot.params import CommandArg, RegexGroup, RegexDict
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.exception import ActionFailed

from .work import get_data, AsyncDownloadFile, random_prompt, search_tags
from .config import *
from base64 import b64encode, b64decode
from asyncio import sleep
from re import findall, S
from colorama import init, Fore

__version__ = "2.9.5.1"

# 构造响应器
check_state = on_command(cmd="check state", permission=SUPERUSER, priority=5, block=True)
set_url = on_regex(pattern=r'set_url:(?P<url>.*/)', permission=SUPERUSER, priority=5, block=True)
search_tag = on_command(cmd="补魔", aliases={"召唤魔咒", "搜索魔咒"}, permission=SUPERUSER, priority=5, block=True)
pattern = r'^(?P<mode>ai绘图|AI绘图|ai作图|AI作图)( scale=(?P<scale>\d+))?( steps=(?P<steps>\d+))?( size=(?P<size>\d+x\d+))?( seed=(?P<seed>\d+))?( prompt="(?P<prompt>.+?)")?( uc="(?P<uc>.+?)")?'
process_img = on_regex(pattern=pattern, permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)
img2img_pattern = r'^(img2img|以图生图).*?url=(?P<url>.*);.*?\](.*?strength=(?P<strength>\d\.\d))?(.*?noise=(?P<noise>\d\.\d))?(.*?scale=(?P<scale>\d+))?(.*?size=(?P<size>\d+x\d+))?(.*?seed=(?P<seed>\d+))?(.*?prompt="(?P<prompt>.+)")?(.*?uc="(?P<uc>.+)")?'
img2img = on_regex(pattern=img2img_pattern, flags=S, permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)

# 获取后端URL
try:
    post_url = get_driver().config.novelai_post_url
except AttributeError:
    post_url = ""
else:
    post_url += "generate-stream"

# 初始化一个全局变量，记录bot的状态（控制bot只能同时接受并处理一次生图请求）
switch = True

# 初始化字体样式（自动重置字体样式）
init(autoreset=True)

# CD信息
cd_dict = {}

logger.success(Fore.LIGHTGREEN_EX + f"成功导入本插件，插件版本为{__version__}")


# 查看后端状态信息
@check_state.handle()
async def _():
    await check_state.send(
        f"当前后端URL为：{post_url}，本地代理端口号为：{port}，生图时间限制为：{img_time}，撤回时间为：{withdraw_time}，CD时间为：{cd_time}秒")
    logger.info(
        Fore.LIGHTCYAN_EX + f"当前后端URL为：{post_url}，本地代理端口号为：{port}，生图时间限制为：{img_time}，撤回时间为：{withdraw_time}，CD时间为：{cd_time}秒")


# 设置后端URL
@set_url.handle()
async def _(regex: tuple = RegexGroup()):
    global post_url
    url = regex[0]
    post_url = url + "generate-stream"
    logger.success(Fore.LIGHTCYAN_EX + f"当前后端URL：{post_url}")
    await set_url.finish(f"url设置成功，设置将在下一次请求时启用！")


# 搜索魔咒
@search_tag.handle()
async def _(tag: Message = CommandArg()):
    tag = str(tag)
    tags = await search_tags(tag, proxies)

    if tags[0] is False:
        await search_tag.finish("魔咒搜索失败！", at_sender=True)
        logger.error(Fore.LIGHTRED_EX + f"魔咒搜索失败：{tags[1]}")
    else:
        await search_tag.finish(f"魔咒搜索结果：{tags[1]}", at_sender=True)


# 普通生图
@process_img.handle()
async def _(event: MessageEvent, bot: Bot, regex: dict = RegexDict()):
    global switch
    if switch is False:
        await process_img.finish(f"{nickname}资源占用中！")

    id_ = event.get_user_id()

    # 保存CD信息
    if id_ not in superusers or id_ not in white_list:
        if id_ not in cd_dict:
            cd_dict[id_] = event.time
        else:
            cdt = event.time - cd_dict[id_]
            if cdt < cd_time:
                await process_img.finish(f"CD受限中，还剩{cd_time - cdt}秒解除！", at_sender=True)
    elif id_ in black_list:
        await process_img.finish()

    # 生图参数
    seed = regex["seed"]
    scale = regex["scale"]
    steps = regex["steps"]
    size = regex["size"]
    prompt = regex["prompt"]
    uc = regex["uc"]

    if seed is None:
        seed = randint(0, pow(2, 32))
    if scale is None:
        scale = 12
    if steps is None:
        steps = 28
    if size is None:
        size = "512x768"
    if uc is None:
        uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
    if prompt is None:
        if_randomP = True
        num = randint(0, 50)
        prompt = random_prompt(num)
    else:
        if "RandomP" in prompt:
            if_randomP = True
            num = findall(r'RandomP (\d+)', prompt)[0]
            prompt = random_prompt(num)
        else:
            if_randomP = False

    # 处理图片尺寸
    size = size.split("x")
    size = [int(size[0]), int(size[1])]
    if size[0] > 1024 or size[1] > 1024:
        switch = True
        await process_img.finish("图片尺寸过大，请重新输入！", at_sender=True)

    # 获取当前用户名
    name = (await bot.get_stranger_info(user_id=int(id_)))["nickname"]

    await process_img.send("正在生成图片，请稍等...", at_sender=True)
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
    data = await get_data(
        post_url=post_url,
        size=size,
        prompt=prompt,
        proxies=proxies,
        timeout=img_time,
        uc=uc, steps=steps,
        scale=scale,
        seed=seed
    )

    if data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败：{data[1]}")
        await process_img.finish("生成失败！", at_sender=True)

    logger.success(Fore.LIGHTGREEN_EX + f"{name}的图片生成成功！")

    # 把base64字符串转成bytes
    image = b64decode(data[1])
    msg = f"\n{prompt}" + MessageSegment.image(image) if if_randomP else MessageSegment.image(image)
    switch = True

    try:
        msg_id = (await process_img.send(msg, at_sender=True))["message_id"]
    except ActionFailed:
        logger.warning(Fore.LIGHTYELLOW_EX + f"{nickname}可能被风控，请稍后再试！")
        await search_tag.finish(f"{nickname}可能被风控，请稍后再试！", at_sender=True)
    else:
        cd_dict[id_] = event.time
        if withdraw_time is not None:
            await sleep(withdraw_time)
            await bot.delete_msg(message_id=msg_id)


# 以图生图
@img2img.handle()
async def _(event: MessageEvent, bot: Bot, regex: dict = RegexDict()):
    global switch
    if switch is False:
        await process_img.finish(f"{nickname}资源占用中！")

    id_ = event.get_user_id()

    # 保存CD信息
    if id_ not in superusers or id_ not in white_list:
        if id_ not in cd_dict:
            cd_dict[id_] = event.time
        else:
            cdt = event.time - cd_dict[id_]
            if cdt < cd_time:
                await process_img.finish(f"CD受限中，还剩{cd_time - cdt}秒解除！", at_sender=True)
    elif id_ in black_list:
        await process_img.finish()

    img_url = regex["url"]
    strength = regex["strength"]
    noise = regex["noise"]
    seed = regex["seed"]
    scale = regex["scale"]
    size = regex["size"]
    prompt = regex["prompt"]
    uc = regex["uc"]

    if strength is None:
        strength = 0.7
    else:
        if float(strength) > 0.99:
            switch = True
            await img2img.finish("strength过大！（不能超过0.99）", at_sender=True)

    if noise is None:
        noise = 0.2
    else:
        if float(noise) > 0.99:
            switch = True
            await img2img.finish("noise过大！（不能超过0.99）", at_sender=True)

    if seed is None:
        seed = randint(0, pow(2, 32))
    if scale is None:
        scale = 12

    if prompt is None:
        if_randomP = True
        num = randint(0, 50)
        prompt = random_prompt(num)
    else:
        if "RandomP" in prompt:
            if_randomP = True
            num = findall(r'RandomP (\d+)', prompt)[0]
            prompt = random_prompt(num)
        else:
            if_randomP = False
        
    if uc is None:
        uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"

    if size is not None:
        # 处理图片尺寸
        size = size.split("x")
        size = [int(size[0]), int(size[1])]
        if size[0] > 1024 or size[1] > 1024:
            switch = True
            await img2img.finish("图片尺寸过大，请重新输入！", at_sender=True)

    switch = False
    name = (await bot.get_stranger_info(user_id=int(id_)))["nickname"]
    await img2img.send(f"开始获取图片...", at_sender=True)
    logger.info(Fore.LIGHTYELLOW_EX + f"开始获取{name}发送的图片...")
    # 下载用户发的图片
    img_data = await AsyncDownloadFile(url=img_url, proxies=proxies)

    if img_data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"{name}发送的图片获取失败：{img_data[1]}")
        await img2img.finish("图片获取失败！", at_sender=True)

    logger.success(Fore.LIGHTGREEN_EX + f"{name}发送的图片获取成功！")

    if size is None:
        size = [512, 768]

    await img2img.send("正在生成图片，请稍等...", at_sender=True)

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
    data = await get_data(
        post_url=post_url,
        size=size,
        prompt=prompt,
        proxies=proxies,
        timeout=img_time,
        img=img,
        mode=mode,
        strength=strength,
        noise=noise,
        scale=scale,
        steps=50,
        seed=seed,
        uc=uc
    )

    if data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败：{data[1]}")
        await img2img.finish(f"生成失败：{data[1]}", at_sender=True)

    logger.success(Fore.LIGHTGREEN_EX + f"{name}的图片生成成功！")

    image = b64decode(data[1])
    msg = f"\n{prompt}" + MessageSegment.image(image) if if_randomP else MessageSegment.image(image)
    switch = True

    try:
        msg_id = (await img2img.send(msg, at_sender=True))["message_id"]
    except ActionFailed:
        logger.warning(Fore.LIGHTYELLOW_EX + f"{nickname}可能被风控，请稍后再试！")
        await search_tag.finish(f"{nickname}可能被风控，请稍后再试！", at_sender=True)
    else:
        cd_dict[id_] = event.time
        if withdraw_time is not None:
            await sleep(withdraw_time)
            await bot.delete_msg(message_id=msg_id)
