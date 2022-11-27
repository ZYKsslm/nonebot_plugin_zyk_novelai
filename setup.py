from setuptools import setup, find_packages


setup(
    name="nonebot_plugin_zyk_novelai",
    version="2.6.1",
    packages=find_packages(),
    author="ZSSLM",
    author_email="3119964735@qq.com",
    long_description="This is a simple plugin that is to send your image made by your NovelAI for nonebot2",
    url="https://github.com/ZYKsslm/nonebot_plugin_zyk_novelai",
    license="MIT License",
    requires=["fake_useragent", "httpx", "colorama", "nonebot2", "nonebot_adapter_onebot"],
    package_data={"nonebot_plugin_zyk_novelai": ["resource/*"]}
)
