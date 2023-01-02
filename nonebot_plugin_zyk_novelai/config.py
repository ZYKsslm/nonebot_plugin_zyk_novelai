from nonebot import get_driver
from random import randint


# 获取全局配置
# 获取本地代理端口
try:
    port = get_driver().config.novelai_proxy_port
except AttributeError:
    port = None
    proxies = None
else:
    try:
        int(port)
    except ValueError:
        port = None
        proxies = None
    else:
        proxies = {
            "http://": f"http://127.0.0.1:{port}",
            "https://": f"http://127.0.0.1:{port}"
        }

# 获取生图时间限制
try:
    img_time = get_driver().config.novelai_img_time
except AttributeError:
    img_time = None
else:
    try:
        img_time = int(img_time)
    except ValueError:
        img_time = None

# 获取撤回时间
try:
    withdraw_time = get_driver().config.novelai_withdraw_time
except AttributeError:
    withdraw_time = None
else:
    try:
        withdraw_time = float(withdraw_time)
    except ValueError:
        withdraw_time = None

# 获取CD时间
try:
    cd_time = get_driver().config.novelai_cd_time
except AttributeError:
    cd_time = 10
else:
    try:
        cd_time = float(cd_time)
    except ValueError:
        cd_time = 10

# 获取白名单
try:
    white_list = get_driver().config.novelai_white_list
except AttributeError:
    white_list = []

# 获取黑名单
try:
    black_list = get_driver().config.novelai_black_list
except AttributeError:
    black_list = []

# 获取超级用户
superusers = get_driver().config.superusers

# 获取Bot昵称
nickname_list = list(get_driver().config.nickname)
nickname = nickname_list[randint(0, len(nickname_list)-1)]