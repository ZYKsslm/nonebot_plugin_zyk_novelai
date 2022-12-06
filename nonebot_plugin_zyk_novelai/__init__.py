#!usr/bin/env python3
# -*- coding: utf-8 -*-
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment, GROUP, PRIVATE_FRIEND, Bot
from nonebot import on_regex, on_fullmatch, on_startswith, get_driver, on_command
from nonebot.params import CommandArg, RegexGroup, RegexDict
from nonebot.permission import SUPERUSER
from nonebot.log import logger

from .work import get_data, get_userid, get_userimg, AsyncDownloadFile, random_prompt, search_tags
from base64 import b64encode, b64decode
from re import findall
from random import randint
from colorama import init, Fore

__version__ = "2.8"

# 构造响应器
check_state = on_fullmatch(msg="check state", permission=SUPERUSER, priority=5, block=True)
set_port = on_regex(pattern=r'set_port:(?P<port>.*)', permission=SUPERUSER, priority=5, block=True)
set_url = on_regex(pattern=r'set_url:(?P<url>.*/)', permission=SUPERUSER, priority=5, block=True)
search_tag = on_command(cmd="补魔", aliases={"召唤魔咒", "搜索魔咒"}, permission=SUPERUSER, priority=5, block=True)
img2img = on_startswith(msg=("以图生图", "img2img"), permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)
# 普通生图正则
pattern = r'^(?P<mode>ai绘图|AI绘图|ai作图|AI作图)( scale=(?P<scale>\d+))?( steps=(?P<steps>\d+))?( size=(?P<size>\d+x\d+))?( seed=(?P<seed>\d+))?( prompt=(?P<prompt>.+))?'
process_img = on_regex(pattern=pattern, permission=GROUP | PRIVATE_FRIEND, priority=10, block=True)

# 获取全局配置
try:
    port = get_driver().config.novelai_proxy_port
    post_url = str(get_driver().config.novelai_post_url) + "generate-stream"
except AttributeError:
    logger.warning(Fore.LIGHTYELLOW_EX + "缺少env配置项！")
else:
    if port == "None":
        proxies = None
    else:
        try:
            int(port)
        except ValueError:
            logger.warning(Fore.LIGHTYELLOW_EX + "novelai_proxy_port配置格式错误！")
            proxies = None
        else:
            proxies = {
                "http://": f"http://127.0.0.1:{port}",
                "https://": f"http://127.0.0.1:{port}"
            }

# 初始化一个全局变量，记录bot的状态（控制bot只能同时接受并处理一次请求）
switch = True

# 初始化字体样式（自动重置字体样式）
init(autoreset=True)

logger.success(Fore.LIGHTGREEN_EX + f"成功导入本插件，插件版本为{__version__}")


# 查看后端状态信息
@check_state.handle()
async def _():
    await check_state.send(f"当前后端URL为：{post_url}，本地代理端口号为：{port}")
    logger.info(Fore.LIGHTCYAN_EX + f"当前后端URL为：{post_url}，本地代理端口号为：{port}")


# 设置本地端口
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
async def _(msg: Message = CommandArg()):
    tag = str(msg)
    tags = await search_tags(tag, proxies)

    if tags[0] is False:
        await search_tag.finish("魔咒搜索失败！")
    else:
        await search_tag.finish(f"魔咒搜索结果：{tags[1]}")


# 普通生图
@process_img.handle()
async def _(event: MessageEvent, bot: Bot, regex: dict = RegexDict()):
    global switch
    if switch is False:
        await process_img.finish("资源占用中！")

    seed = regex["seed"]
    scale = regex["scale"]
    steps = regex["steps"]
    size = regex["size"]
    prompt = regex["prompt"]
    uc = "deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra_limb, ugly, poorly drawn hands, fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, mutated hands and fingers:1.5, long body :1.3, mutation, poorly drawn :1.2, black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, missing arms, missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, blurry, disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, safety knickers, beard, furry, pony, pubic hair, mosaic, testis, deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra_limb, ugly, poorly drawn hands, fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, mutated hands and fingers:1.5, long body :1.3, mutation, poorly drawn :1.2, black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, missing arms, missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, blurry, disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, beard, pony, mosaic"

    if seed is None:
        seed = randint(0, pow(2, 32))
    if scale is None:
        scale = 12
    if steps is None:
        steps = 28
    if size is None:
        size = "512x512"
    if prompt is None:
        if_randomP = True
        num = randint(0, 1000)
        prompt = random_prompt(num)

    else:
        try:
            uc = findall(r'uc=(?P<uc>.+)', prompt)[0]
        except IndexError:
            uc = "deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra_limb, ugly, poorly drawn hands, fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, mutated hands and fingers:1.5, long body :1.3, mutation, poorly drawn :1.2, black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, missing arms, missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, blurry, disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, safety knickers, beard, furry, pony, pubic hair, mosaic, testis, deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra_limb, ugly, poorly drawn hands, fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, mutated hands and fingers:1.5, long body :1.3, mutation, poorly drawn :1.2, black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, missing arms, missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, blurry, disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, beard, pony, mosaic"
        # 获取随机prompt
        if "RandomP" in prompt:
            if_randomP = True
            try:
                num = findall(r'RandomP (?P<num>\d+)', prompt)[0]
            except IndexError:
                switch = True
                await process_img.finish("请输入条数！")
            else:
                prompt = random_prompt(num)
        else:
            if_randomP = False

    # 处理图片尺寸
    try:
        size = size.split("x")
    except AttributeError:
        size = [512, 512]
    size = [int(size[0]), int(size[1])]
    if size[0] > 1024 or size[1] > 1024:
        switch = True
        await process_img.finish("图片尺寸过大，请重新输入！")

    # 获取用户信息
    id_ = get_userid(event)
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
    data = await get_data(post_url=post_url, size=size, prompt=prompt, proxies=proxies, uc=uc, steps=steps, scale=scale, seed=seed)

    if data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败:{data[1]}")
        await process_img.finish(f"{name}的图片生成失败")

    logger.success(Fore.LIGHTGREEN_EX + f"{name}的图片生成成功")

    # 把base64字符串转成bytes
    image = b64decode(data[1])
    msg = Message(f"[CQ:at,qq={id_}]\n{prompt}") + MessageSegment.image(image) if if_randomP == True else Message(f"[CQ:at,qq={id_}]") + MessageSegment.image(image)
    switch = True
    await process_img.finish(msg)


@img2img.handle()
async def _(event: MessageEvent, bot: Bot):
    global switch
    if switch is False:
        await process_img.finish("资源占用中！")
    info = str(event.get_message())

    try:
        # 获取size
        size = findall(r'size=(?P<size>\d+x\d+)', info)[0]
    except IndexError:
        size = "512x512"
    else:
        # 处理图片尺寸
        try:
            size = size.split("x")
        except AttributeError:
            size = [512, 768]
        size = [int(size[0]), int(size[1])]
        if size[0] > 1024 or size[1] > 1024:
            switch = True
            await img2img.finish("图片尺寸过大，请重新输入")

    try:
        # 获取strength
        strength = findall(r'strength=(?P<strength>\d\.\d)', info)[0]
    except IndexError:
        strength = 0.7
    else:
        try:
            fs = float(strength)
        except ValueError:
            await img2img.finish("请输入正确的strength！")
        else:
            strength = fs
        if strength > 0.99:
            await img2img.finish("strength过大！（不能超过0.99）")

    try:
        # 获取noise
        noise = findall(r'noise=(?P<noise>\d\.\d)', info)[0]
    except IndexError:
        noise = 0.2
    else:
        try:
            fn = float(noise)
        except ValueError:
            await img2img.finish("请输入正确的noise！")
        else:
            noise = fn
        if noise > 0.99:
            await img2img.finish("noise过大！（不能超过0.99）")

    try:
        # 获取scale
        scale = findall(r'scale=(?P<scale>\d+)', info)[0]
    except IndexError:
        scale = 12

    try:
        # 获取seed
        seed = findall(r'seed=(?P<seed>\d+)', info)[0]
    except IndexError:
        seed = randint(0, pow(2, 32))

    uc = "deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra_limb, ugly, poorly drawn hands, fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, mutated hands and fingers:1.5, long body :1.3, mutation, poorly drawn :1.2, black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, missing arms, missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, blurry, disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, safety knickers, beard, furry, pony, pubic hair, mosaic, testis, deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra_limb, ugly, poorly drawn hands, fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, mutated hands and fingers:1.5, long body :1.3, mutation, poorly drawn :1.2, black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, missing arms, missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, blurry, disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, beard, pony, mosaic"

    try:
        # 获取prompt
        prompt = findall(r'prompt=(?P<prompt>.*)', info)[0]
    except IndexError:
        if_randomP = True
        num = randint(0, 1000)
        prompt = random_prompt(num)
    else:
        # 获取随机prompt
        if "RandomP" in prompt:
            if_randomP = True
            try:
                num = findall(r'RandomP (?P<num>\d+)', prompt)[0]
            except IndexError:
                switch = True
                await process_img.finish("请输入条数！")
            else:
                prompt = random_prompt(num)
        else:
            if_randomP = False

        try:
            # 获取uc
            uc = findall(r'uc=(?P<uc>.+)', prompt)[0]
        except IndexError:
            uc = "deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra_limb, ugly, poorly drawn hands, fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, mutated hands and fingers:1.5, long body :1.3, mutation, poorly drawn :1.2, black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, missing arms, missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, blurry, disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, safety knickers, beard, furry, pony, pubic hair, mosaic, testis, deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra_limb, ugly, poorly drawn hands, fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, mutated hands and fingers:1.5, long body :1.3, mutation, poorly drawn :1.2, black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, missing arms, missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, blurry, disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, beard, pony, mosaic"

    # 获取用户ID
    id_ = get_userid(event)
    # 获取图片URL
    img_url = get_userimg(event)

    if img_url is None:
        switch = True
        await img2img.finish(Message(fr"[CQ:at,qq={id_}]请发送图片！"))

    switch = False
    await img2img.send(Message(f"[CQ:at,qq={id_}]正在获取图片"))
    name = (await bot.get_stranger_info(user_id=int(id_)))["nickname"]
    logger.info(Fore.LIGHTYELLOW_EX + f"开始获取{name}发送的图片")
    # 下载用户发的图片
    img_data = await AsyncDownloadFile(url=img_url, proxies=proxies, timeout=5)

    if img_data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"{name}发送的图片获取失败:{img_data[1]}")
        await img2img.finish(Message(fr"[CQ:at,qq={id_}]图片获取失败！"))

    logger.success(Fore.LIGHTGREEN_EX + f"{name}发送的图片获取成功")

    await img2img.send(Message(fr"[CQ:at,qq={id_}]正在生成图片，请稍等..."))

    # 先把bytes转成base64，再给base64编码
    img = b64encode(img_data[1]).decode("utf-8")
    mode = "以图生图"
    steps = 50
    switch = False
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
    data = await get_data(post_url=post_url, size=size, prompt=prompt, proxies=proxies, img=img, mode=mode,
                          strength=strength, noise=noise, scale=scale, steps=steps, seed=seed, uc=uc)

    if data[0] is False:
        switch = True
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败:{data[1]}")
        await img2img.finish(f"生成失败")

    logger.success(Fore.LIGHTGREEN_EX + f"{name}的图片生成成功")

    image = b64decode(data[1])
    msg = Message(f"[CQ:at,qq={id_}]\n{prompt}") + MessageSegment.image(image) if if_randomP == True else Message(f"[CQ:at,qq={id_}]") + MessageSegment.image(image)
    switch = True
    await img2img.finish(msg)
