from httpx import AsyncClient
from fake_useragent import UserAgent
import random
from re import compile, findall
import sqlite3
import os


async def AsyncDownloadFile(url, proxies=None, timeout=None, headers=None):
    if headers is None:
        headers = {"User-Agent": UserAgent().random}
    async with AsyncClient(headers=headers, proxies=proxies, timeout=timeout) as client:
        try:
            file = await client.get(url)
        except Exception as error:
            return False, error
        else:
            return True, file.content


def get_userid(event):
    info = str(event.get_session_id())
    try:
        res = findall(r"group_(?P<group_id>\d+)_(?P<member_id>\d+)", info)[0]
    except IndexError:
        id_ = info
    else:
        id_ = res[1]

    return id_


def get_userimg(event):
    img_info = str(event.get_message())
    url_pattern = compile(r'url=(?P<url>.*?)]')
    try:
        img_url = findall(url_pattern, img_info)[0]
    except IndexError:
        return None
    else:
        return img_url


def random_prompt(num):
    db_path = os.path.abspath(os.path.dirname(__file__)) + r"\resource\novelai_tags.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    off = random.randint(0, 1000-num)
    cur.execute(f"select * from  main_tags limit {num} offset {off}")
    tags = cur.fetchall()

    prompt = "{{{Masterpiece}}}, {{best quality}}, beautifully painted, highly detailed, highres, Stunning art"
    for tag in tags:
        prompt += ", " + tag[0]

    return prompt


async def search_tags(tag, proxies):
    headers = {
        "User-Agent": UserAgent().random,
        "origin": "http://www.cerfai.com",
        "referer": "http://www.cerfai.com/"
    }
    data = {
        "keyword": tag
    }
    async with AsyncClient(headers=headers, proxies=proxies) as client:
        try:
            res = await client.post(url="https://api.cerfai.com/search_tags", json=data)
        except Exception as error:
            return False, error
        res = res.json()["data"]
        tags = ""
        for tag in res:
            tags += f"\n{tag['name']} {tag['t_name']}"

    return True, tags


async def get_data(post_url, size, prompt, proxies, img=None, mode=None):
    # 低质量prompt
    uc = "(((deformed))), blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, (mutated hands and fingers:1.5), (long body :1.3), (mutation, poorly drawn :1.2), black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, (((missing arms))), missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, (blurry), disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, safety knickers, beard, furry, pony, pubic hair, mosaic, testis, (((deformed))), blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing, broken legs censor, censored, censor_bar, multiple breasts, (mutated hands and fingers:1.5), (long body :1.3), (mutation, poorly drawn :1.2), black-white, bad anatomy, liquid body, liquidtongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, missingbreasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs, fusedears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, fused animal ears, bad animal ears, poorly drawn animal ears, extra animal ears, liquidanimal ears, heavy animal ears, missing animal ears, text, ui, error, missing fingers, missing limb, fused fingers, one hand with more than 5 fingers, one hand with less than5 fingers, one hand with more than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, fused digit, missing digit, bad digit, liquid digit, colorful tongue, blacktongue, cropped, watermark, username, blurry, JPEG artifacts, signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, extra feet, bad feet, poorly drawnfeet, fused feet, missing feet, extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, big face, long face, badeyes, fused eyes poorly drawn eyes, extra eyes, malformed limbs, more than 2 nipples, missing nipples, different nipples, fused nipples, bad nipples, poorly drawnnipples, black nipples, colorful nipples, gross proportions. short arm, (((missing arms))), missing thighs, missing calf, missing legs, mutation, duplicate, morbid, mutilated, poorly drawn hands, more than 1 left hand, more than 1 right hand, deformed, (blurry), disfigured, missing legs, extra arms, extra thighs, more than 2 thighs, extra calf,fused calf, extra legs, bad knee, extra knee, more than 2 legs, bad tails, bad mouth, fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, too longtongue, black tongue, big mouth, cracked mouth, bad mouth, dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, fused cloth, poorly drawn cloth, badpantie, yellow teeth, thick lips, bad camel toe, colorful camel toe, bad asshole, poorly drawn asshole, fused asshole, missing asshole, bad anus, bad pussy, bad crotch, badcrotch seam, fused anus, fused pussy, fused anus, fused crotch, poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, poorly drawn crotch, poorlydrawn crotch seam, bad thigh gap, missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh gap, poorly drawn anus, bad collarbone, fused collarbone, missing collarbone, liquid collarbone, strong girl, obesity, worst quality, low quality, normal quality, liquid tentacles, bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, missing clit, bad clit, fused clit, colorful clit, black clit, liquid clit, QR code, bar code, censored, safety panties, beard, pony, mosaic"
    data = {
        "width": size[0],
        "height": size[1],
        "n_samples": 1,
        "prompt": prompt,
        "sampler": "k_euler_ancestral",
        "scale": 12,
        "seed": random.randint(0, pow(2, 32)),
        "steps": 28,
        "uc": uc,
        "ucPreset": 0,
    }
    headers = {
        "User-Agent": UserAgent().random
    }

    if mode == "以图生图":
        data.update(
            {
                "strength": 0.7,
                "noise": 0.2,
                "image": img
            }
        )

    async with AsyncClient(headers=headers, proxies=proxies) as client:
        try:
            resp = await client.post(url=post_url, json=data, timeout=90)
        except Exception as error:
            return False, error
        info = resp.text

        # 获取错误原因
        if "error" in info:
            error = findall(r'"error":"(?P<error>.*?)"', info)[0]
            return False, error

        # 获取返回的图片base64
        base64_img = findall(r'data:(?P<base64>.*)', info)[0]
        return True, base64_img
