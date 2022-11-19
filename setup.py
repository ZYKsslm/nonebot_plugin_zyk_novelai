from setuptools import setup, find_packages


setup(
    name="nonebot_plugin_zyk_novelai",
    version="2022.11.19.1",
    packages=find_packages(),
    author="ZSSLM",
    author_email="3119964735@qq.com",
    description="This is a simple plugin that is to send your image made by your NovelAI for nonebot2",
    url="https://github.com/ZYKsslm/nonebot_plugin_zyk_novelai",
    license="Apache License 2.0",
    requires=["fake_useragent", "httpx", "nonebot2", "nonebot_adapter_onebot"],
)