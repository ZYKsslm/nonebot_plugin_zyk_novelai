#!usr/bin/env python3
# -*- coding: utf-8 -*-
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment, GROUP, PRIVATE_FRIEND
from nonebot.typing import T_State
from nonebot.permission import SUPERUSER
from nonebot import on_regex, on_fullmatch, on_startswith
from nonebot.log import logger
from work import get_data, get_userid, get_userimg, AsyncDownloadFile
from config import proxy_port, get_url
from base64 import b64encode, b64decode
from re import findall

# 构造响应器
set_port = on_regex(pattern=r'set_port:(?P<port>\d+)', permission=SUPERUSER, priority=5, block=True)
set_url = on_regex(pattern=r'set_url:(?P<url>.*/)', permission=SUPERUSER, priority=5, block=True)
img2img = on_startswith(msg=("以图生图", "img2img"), permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)
check_state = on_fullmatch(msg="check state", permission=SUPERUSER, priority=5, block=True)
process_img = on_regex(pattern=r"^(?P<mode>ai绘图|AI绘图|ai作图|AI作图) size=(?P<size>\d+x\d+) prompt=(?P<prompt>.*)",
                       permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)

port = proxy_port
post_url = get_url + "generate-stream"
# 设置一个全局变量，记录bot的状态，（同时控制bot只能同时处理一次请求）
switch = True

proxies = {
    "http://": f"http://127.0.0.1:{port}",
    "https://": f"http://127.0.0.1:{port}"
}


@check_state.handle()
async def _():
    await check_state.finish(f"当前后端url为：{post_url}，本地代理端口号为：{port}")


@set_port.handle()
async def _(state: T_State):
    global port, proxies
    info = list(state["_matched_groups"])
    port = info[0]
    proxies = {
        "http://": f"http://127.0.0.1:{port}",
        "https://": f"http://127.0.0.1:{port}"
    }
    logger.success(f"your local proxy port:{port}")
    await set_port.finish("本地代理端口设置成功，设置将在下一次请求时启用")


@set_url.handle()
async def _(state: T_State):
    global post_url
    info = list(state["_matched_groups"])
    url = info[0]
    post_url = url + "generate-stream"
    logger.success(f"your post url:{post_url}")
    await set_url.finish(f"url设置成功，设置将在下一次请求时启用")


@process_img.handle()
async def _(event: MessageEvent, state: T_State):
    global switch
    if switch is False:
        await process_img.finish("资源占用中！")

    info = list(state["_matched_groups"])
    # 生成的图片尺寸
    size = info[1]
    # 术士
    prompt = info[2]

    try:
        size = size.split("x")
    except AttributeError:
        size = [512, 768]
    size = [int(size[0]), int(size[1])]
    if size[0] > 1024 or size[1] > 1024:
        switch = True
        await process_img.finish("图片尺寸过大，请重新输入")

    # 获取用户id，发送提示信息
    id_ = get_userid(event=event)
    await process_img.send(Message(fr"[CQ:at,qq={id_}]正在生成图片，请稍等..."))

    switch = False
    mode = None
    img = None
    data = await get_data(post_url, mode, size, prompt, proxies, img)

    if data[0] is False:
        switch = True
        logger.error(f"后端请求失败:{data[1]}")
        await process_img.finish(f"生成失败")

    # 把base64字符串转成bytes
    image = b64decode(data[1])

    # 发送消息部分
    msg = Message(f"[CQ:at,qq={id_}]") + MessageSegment.image(image)
    switch = True
    await process_img.finish(msg)


@img2img.handle()
async def _(event: MessageEvent):
    global switch
    if switch is False:
        await process_img.finish("资源占用中！")

    info = str(event.get_message())
    try:
        # 生成的图片尺寸
        size = findall(r'size=(?P<size>\d+x\d+)', info)[0]
        # 术士
        prompt = findall(r'prompt=(?P<prompt>.*)', info)[0]
    except IndexError:
        switch = True
        await img2img.finish("缺少参数，请按要求输入！")
    else:
        try:
            size = size.split("x")
        except AttributeError:
            size = [512, 768]
        size = [int(size[0]), int(size[1])]
        if size[0] > 1024 or size[1] > 1024:
            switch = True
            await img2img.finish("图片尺寸过大，请重新输入")

        # 获取用户id
        id_ = get_userid(event=event)
        img_url = get_userimg(event)
        if img_url is None:
            switch = True
            await img2img.finish(Message(fr"[CQ:at,qq={id_}]请发送图片！"))
        # 下载用户发的图片
        switch = False
        img_data = await AsyncDownloadFile(url=img_url, proxies=proxies)
        if img_data[0] is False:
            switch = True
            logger.error(f"用户图片获取失败:{img_data[1]}")
            await img2img.finish(Message(fr"[CQ:at,qq={id_}]图片下载失败！"))

        await img2img.send(Message(fr"[CQ:at,qq={id_}]正在生成图片，请稍等..."))
        # 先把bytes转成base64，再把base64编码成字符串
        img = b64encode(img_data[1]).decode()
        switch = False
        mode = "以图生图"
        data = await get_data(post_url, mode, size, prompt, proxies, img)

        if data[0] is False:
            switch = True
            logger.error(f"后端请求失败:{data[1]}")
            await img2img.finish(f"生成失败")

        image = b64decode(data[1])

        # 发送消息部分
        msg = Message(f"[CQ:at,qq={id_}]") + MessageSegment.image(image)
        switch = True
        await img2img.finish(msg)
