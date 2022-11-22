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
    off = random.randint(0, 39194)
    cur.execute(f"select * from  tags limit {num} offset {off}")
    res = cur.fetchall()

    prompt = "{{{Masterpiece}}}, {{best quality}}, beautifully painted, highly detailed, highres, Stunning art"
    for i in res:
        prompt += ", " + i[0]

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

    return tags


async def get_data(post_url, size, prompt, proxies, img=None, mode=None):
    # 低质量prompt
    uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, " \
         "worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, lowres, " \
         "bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, " \
         "low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, bad feet"
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
