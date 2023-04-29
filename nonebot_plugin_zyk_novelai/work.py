from httpx import AsyncClient, ConnectTimeout
from fake_useragent import UserAgent
import random
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


def random_prompt(order):
    num = int(order)
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "resource", "novelai_tags.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    offset = random.randint(0, 1000 - num)
    cur.execute(f"select 英文词条 from main_tags limit {num} offset {offset}")
    tags = cur.fetchall()

    prompt = "{masterpiece}, best quality, highly detailed"
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
        except Exception as error:
            return False, error
        info = resp.text

        # 获取错误
        if "data:" not in info:
            return False, info

        # 获取返回的图片base64
        base64_img = findall(r'data:(?P<base64>.*)', info)[0]
        return True, base64_img
