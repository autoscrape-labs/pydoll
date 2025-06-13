import asyncio
from pydoll.fingerprint import Chrome


async def basic_example():
    # 启用指纹伪装只需要设置一个参数
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()

        # 正常使用浏览器，指纹伪装自动生效
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')

        # 查看生成的指纹信息
        summary = browser.get_fingerprint_summary()
        print("当前指纹:", summary)


asyncio.run(basic_example())
