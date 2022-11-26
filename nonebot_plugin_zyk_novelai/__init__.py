#!usr/bin/env python3
# -*- coding: utf-8 -*-
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment, GROUP, PRIVATE_FRIEND, Bot
from nonebot.typing import T_State
from nonebot.permission import SUPERUSER
from nonebot import on_regex, on_fullmatch, on_startswith, get_driver, on_command
from nonebot.params import CommandArg
from nonebot.log import logger
from .work import get_data, get_userid, get_userimg, AsyncDownloadFile, random_prompt, search_tags
from base64 import b64encode, b64decode
from re import findall
from colorama import init, Fore

# 构造响应器
check_state = on_fullmatch(msg="check state", permission=SUPERUSER, priority=5, block=True)
set_port = on_regex(pattern=r'set_port:(?P<port>.*)', permission=SUPERUSER, priority=5, block=True)
set_url = on_regex(pattern=r'set_url:(?P<url>.*/)', permission=SUPERUSER, priority=5, block=True)
search_tag = on_command(cmd="补魔", aliases={"召唤魔咒", "搜索魔咒"}, permission=SUPERUSER, priority=5, block=True)
img2img = on_startswith(msg=("以图生图", "img2img"), permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)
process_img = on_regex(pattern=r"^(?P<mode>ai绘图|AI绘图|ai作图|AI作图) size=(?P<size>\d+x\d+) prompt=(?P<prompt>.*)",
                       permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)

port = get_driver().config.novelai_proxy_port
post_url = str(get_driver().config.novelai_post_url) + "generate-stream"
# 初始化一个全局变量，记录bot的状态（控制bot只能同时处理一次请求）
switch = True
proxies = {
    "http://": f"http://127.0.0.1:{port}",
    "https://": f"http://127.0.0.1:{port}"
}

# 初始化字体样式
init(autoreset=True)


@check_state.handle()
async def _():
    logger.info(Fore.LIGHTCYAN_EX + f"当前后端URL为：{post_url}，本地代理端口号为：{port}")


@set_port.handle()
async def _(state: T_State):
    global port, proxies
    info = list(state["_matched_groups"])
    port = info[0]

    # 判断是否为数字
    try:
        int(port)
    except ValueError:
        if port != "None":
            await set_port.finish("请输入有效参数！")

    if port == "None":
        proxies = None
        logger.success(Fore.LIGHTCYAN_EX + f"成功取消代理模式")
    else:
        proxies = {
            "http://": f"http://127.0.0.1:{port}",
            "https://": f"http://127.0.0.1:{port}"
        }
        logger.success(Fore.LIGHTCYAN_EX + f"你的本地代理端口：{port}")

    await set_port.finish("本地代理端口设置成功，设置将在下一次请求时启用")


@set_url.handle()
async def _(state: T_State):
    global post_url
    info = list(state["_matched_groups"])
    url = info[0]
    post_url = url + "generate-stream"
    logger.success(Fore.LIGHTCYAN_EX + f"你的后端URL：{post_url}")
    await set_url.finish(f"url设置成功，设置将在下一次请求时启用")


@search_tag.handle()
async def _(msg: Message = CommandArg()):
    tag = str(msg)
    tags = await search_tags(tag, proxies)

    if tags[0] is False:
        await search_tag.finish("魔咒搜索失败！")

    await search_tag.finish(f"魔咒搜索结果：{tags[1]}")


@process_img.handle()
async def _(event: MessageEvent, state: T_State, bot: Bot):
    global switch
    if switch is False:
        await process_img.finish("资源占用中！")

    info = list(state["_matched_groups"])
    # 生成的图片尺寸
    size = info[1]
    # 获取prompt
    prompt = info[2]

    # 获取随机prompt
    if "RandomP" in prompt:
        try:
            num = findall(r'RandomP (?P<num>\d+)', prompt)[0]
        except IndexError:
            switch = True
            await process_img.finish("请输入条数！")
        else:
            prompt = random_prompt(num)
    try:
        size = size.split("x")
    except AttributeError:
        size = [512, 768]
    size = [int(size[0]), int(size[1])]
    if size[0] > 1024 or size[1] > 1024:
        switch = True
        await process_img.finish("图片尺寸过大，请重新输入！")

    # 获取用户信息
    id_ = get_userid(event)
    name = (await bot.get_stranger_info(user_id=int(id_)))["nickname"]

    await process_img.send(Message(fr"[CQ:at,qq={id_}]正在生成图片，请稍等..."))
    logger.info(Fore.LIGHTYELLOW_EX + f"\n开始生成{name}的图片：\nsize={size[0]}，{size[1]}\nprompt={prompt}")
    switch = False
    data = await get_data(post_url, size, prompt, proxies)

    if data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败:{data[1]}")
        await process_img.finish(f"{name}的图片生成失败")

    logger.success(Fore.LIGHTGREEN_EX + "{name}的图片生成成功")

    # 把base64字符串转成bytes
    image = b64decode(data[1])
    msg = Message(f"[CQ:at,qq={id_}]") + MessageSegment.image(image)
    switch = True
    await process_img.finish(msg)


@img2img.handle()
async def _(event: MessageEvent, bot: Bot):
    global switch

    if switch is False:
        await process_img.finish("资源占用中！")

    info = str(event.get_message())
    try:
        # 获取图片尺寸
        size = findall(r'size=(?P<size>\d+x\d+)', info)[0]
        # 获取prompt
        prompt = findall(r'prompt=(?P<prompt>.*)', info)[0]
    except IndexError:
        switch = True
        await img2img.finish("缺少参数！")
    else:
        try:
            size = size.split("x")
        except AttributeError:
            size = [512, 768]
        size = [int(size[0]), int(size[1])]
        if size[0] > 1024 or size[1] > 1024:
            switch = True
            await img2img.finish("图片尺寸过大，请重新输入")

        # 获取随机prompt
        if "RandomP" in prompt:
            try:
                num = findall(r'RandomP (?P<num>\d+)', prompt)[0]
            except IndexError:
                switch = True
                await process_img.finish("请输入条数！")
            else:
                prompt = random_prompt(num)

        id_ = get_userid(event)
        img_url = get_userimg(event)

        if img_url is None:
            switch = True
            await img2img.finish(Message(fr"[CQ:at,qq={id_}]请发送图片！"))

        # 下载用户发的图片
        switch = False

        await img2img.send(Message(f"[CQ:at,qq={id_}]正在获取图片"))
        # 获取用户昵称
        name = (await bot.get_stranger_info(user_id=int(id_)))["nickname"]
        logger.info(Fore.LIGHTYELLOW_EX + f"开始获取{name}发送的图片")

        img_data = await AsyncDownloadFile(url=img_url, proxies=proxies, timeout=5)

        if img_data[0] is False:
            switch = True
            logger.error(Fore.LIGHTRED_EX + f"{name}发送的图片获取失败:{img_data[1]}")
            await img2img.finish(Message(fr"[CQ:at,qq={id_}]图片获取失败！"))

        logger.success(Fore.LIGHTGREEN_EX + f"{name}发送的图片获取成功")

        await img2img.send(Message(fr"[CQ:at,qq={id_}]正在生成图片，请稍等..."))

        # 先把bytes转成base64，再把base64编码成字符串
        img = b64encode(img_data[1]).decode()
        mode = "以图生图"
        switch = False
        logger.info(Fore.LIGHTYELLOW_EX + f"\n开始生成{name}的图片：\nsize={size[0]}，{size[1]}\nprompt={prompt}")
        data = await get_data(post_url, size, prompt, proxies, img, mode)

        if data[0] is False:
            switch = True
            logger.error(Fore.LIGHTRED_EX + f"后端请求失败:{data[1]}")
            await img2img.finish(f"生成失败")

        logger.success(Fore.LIGHTGREEN_EX + "图片生成成功")

        image = b64decode(data[1])
        msg = Message(f"[CQ:at,qq={id_}]") + MessageSegment.image(image)
        switch = True
        await img2img.finish(msg)
