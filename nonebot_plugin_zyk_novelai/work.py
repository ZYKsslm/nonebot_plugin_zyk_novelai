from httpx import AsyncClient, ConnectTimeout
from fake_useragent import UserAgent
import random
from PIL import Image
from io import BytesIO
from re import findall
import sqlite3
import os


async def AsyncDownloadFile(url, proxies=None, headers=None):
    if headers is None:
        headers = {"User-Agent": UserAgent().random}
    async with AsyncClient(headers=headers, proxies=proxies, timeout=None) as client:
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


def random_prompt(order):
    num = int(order)
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "resource", "novelai_tags.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    off = random.randint(0, 1000 - num)
    cur.execute(f"select 英文词条 from  main_tags limit {num} offset {off}")
    tags = cur.fetchall()

    prompt = "masterpiece, best quality, highly detailed"
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
    async with AsyncClient(headers=headers, proxies=proxies, timeout=None) as client:
        try:
            res = await client.post(url="https://api.cerfai.com/search_tags", json=data)
        except Exception as error:
            return False, error
        res = res.json()["data"]
        tags = ""
        for tag in res:
            tags += f"\n{tag['name']} {tag['t_name']}"

    return True, tags


def set_size(image):
    # 人类的本质就是复读机，这段代码写得真辣鸡，应该可以用个什么算法吧，但是我懒
    img = Image.open(BytesIO(image))
    width, height = img.size

    if width == 512 or width < 512:
        width = 512
    elif width == 640:
        pass
    elif width == 768:
        pass
    elif width == 1024 or width > 1024:
        width = 1024
    elif 512 < width < 640:
        width1 = width - 512
        width2 = abs(width - 640)
        if width1 > width2:
            width = 640
        else:
            width = 512
    elif 640 < width < 768:
        width1 = width - 640
        width2 = abs(width - 768)
        if width1 > width2:
            width = 768
        else:
            width = 640
    elif 768 < width < 1024:
        width1 = width - 768
        width2 = abs(width - 1024)
        if width1 > width2:
            width = 1024
        else:
            width = 768

    if height == 512 or height < 512:
        height = 512
    elif height == 640:
        pass
    elif height == 768:
        pass
    elif height == 1024 or height > 1024:
        height = 1024
    elif 512 < height < 640:
        height1 = height - 512
        height2 = abs(height - 640)
        if height1 > height2:
            height = 640
        else:
            height = 512
    elif 640 < height < 768:
        height1 = height - 640
        height2 = abs(height - 768)
        if height1 > height2:
            height = 768
        else:
            height = 640
    elif 768 < height < 1024:
        height1 = height - 768
        height2 = abs(height - 1024)
        if height1 > height2:
            height = 1024
        else:
            height = 768

    return width, height


async def get_data(
        post_url, prompt, proxies, timeout,
        img=None, mode=None, strength=None,
        noise=None, size=None, uc=None,
        scale=None, steps=None, seed=None
):
    data = {
        "width": size[0],
        "height": size[1],
        "n_samples": 1,
        "prompt": prompt,
        "sampler": "k_euler_ancestral",
        "scale": scale,
        "seed": seed,
        "steps": steps,
        "uc": uc,
        "ucPreset": 0,
    }

    headers = {
        "User-Agent": UserAgent().random
    }

    if mode == "以图生图":
        data.update(
            {
                "strength": strength,
                "noise": noise,
                "image": img
            }
        )

    async with AsyncClient(headers=headers, proxies=proxies, timeout=timeout) as client:
        try:
            resp = await client.post(url=post_url, json=data)
        except ConnectTimeout:
            return False, "时间超过限制！"
        info = resp.text

        # 获取错误
        if "data:" not in info:
            return False, info

        # 获取返回的图片base64
        base64_img = findall(r'data:(?P<base64>.*)', info)[0]
        return True, base64_img
