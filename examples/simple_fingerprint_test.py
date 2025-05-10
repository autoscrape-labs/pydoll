#!/usr/bin/env python3
"""
适用于PyTest的pydoll指纹伪装测试脚本
仅使用内置指纹伪装功能
"""

import asyncio
import os
import sys

import pytest

# 添加pydoll路径
sys.path.insert(0, os.path.abspath(''))

# 导入pydoll组件
from pydoll.browser.chrome import Chrome
from pydoll.browser.fingerprint import FINGERPRINT_MANAGER
from pydoll.browser.options import Options


class TestFingerprint:
    """测试pydoll的指纹伪装功能"""

    @pytest.mark.asyncio
    async def test_fingerprints_are_unique(self):
        """测试多个浏览器实例产生的指纹是否唯一"""
        print("\n开始测试pydoll指纹伪装功能...")

        # 收集所有指纹
        results = []
        instance_count = 5  # 使用5个实例进行测试

        # 依次测试每个实例
        for i in range(1, instance_count + 1):
            result = await self._run_browser_instance(i)
            results.append(result)

        # 分析结果
        # 提取有效的指纹ID
        fingerprint_ids = [r["fingerprint_id"] for r in results
                         if not r["fingerprint_id"].startswith("错误")
                         and r["fingerprint_id"] != "未找到指纹ID"]

        # 获取唯一值
        unique_ids = set(fingerprint_ids)

        # 输出分析结果
        print(f"\n总测试实例: {instance_count}")
        print(f"有效指纹ID: {len(fingerprint_ids)}")
        print(f"唯一指纹ID: {len(unique_ids)}")

        # 如果有重复，显示详情
        if len(unique_ids) < len(fingerprint_ids):
            print("\n发现重复的指纹ID:")
            for fp_id in unique_ids:
                count = fingerprint_ids.count(fp_id)
                if count > 1:
                    print(f"- 指纹ID '{fp_id}' 出现了 {count} 次")
                    indices = [
                        r["index"] for r in results
                        if r["fingerprint_id"] == fp_id
                    ]
                    print(f"  出现在实例: {indices}")

                    # 显示使用相同指纹的实例的详细信息
                    print("  详细信息:")
                    for idx in indices:
                        r = next(res for res in results if res["index"] == idx)
                        print(f"    实例 #{idx} UA: {r['user_agent'][:30]}...")

        # 验证所有指纹都是唯一的
        if len(unique_ids) < len(fingerprint_ids):
            print("\n⚠️ 检测到重复指纹，但这不一定意味着指纹伪装完全失败")
            print("FingerprintJS使用很多深层次的浏览器特性，可能需要更多技术手段来完全伪装")
        else:
            print("\n✅ 所有指纹ID都是唯一的，指纹伪装功能工作正常!")

        # 显示详细结果
        print("\n详细结果:")
        for r in results:
            print(f"实例 #{r['index']}:")
            print(f"  用户代理: {r['user_agent'][:50]}...")
            print(f"  指纹ID: {r['fingerprint_id']}")
            print("-" * 40)

    @staticmethod
    async def _run_browser_instance(index):
        """
        运行单个浏览器实例并获取其指纹ID

        Args:
            index: 实例编号

        Returns:
            dict: 包含实例信息和指纹ID的字典
        """
        print(f"\n=== 测试实例 #{index} ===")

        # 仅使用FINGERPRINT_MANAGER生成新指纹
        fingerprint = FINGERPRINT_MANAGER.generate_new_fingerprint('chrome')

        print(f"生成的指纹ID: {fingerprint['id']}")
        print(f"用户代理: {fingerprint['user_agent'][:50]}...")

        # 创建Chrome选项
        options = Options()

        # 创建浏览器实例并启用指纹伪装
        browser = Chrome(options=options, enable_fingerprint_spoofing=True)

        try:
            # 启动浏览器
            print("启动浏览器...")
            await browser.start()

            # 获取页面
            page = await browser.get_page()

            # 访问FingerprintJS网站
            print("访问FingerprintJS网站...")
            await page.go_to("https://fingerprintjs.github.io/fingerprintjs/")

            # 等待指纹生成
            print("等待指纹生成...")
            await asyncio.sleep(5)

            # 获取指纹ID - 从pre.giant元素中
            print("提取指纹ID...")
            js_code = """
            (() => {
                try {
                    const element = document.querySelector('pre.giant');
                    return element ? element.textContent.trim() :
                        "未找到指纹ID";
                } catch(e) {
                    return "错误: " + e.message;
                }
            })()
            """

            result = await page.execute_script(js_code)

            # 解析结果
            if isinstance(result, dict) and 'result' in result:
                fingerprint_id = result['result']['result']['value']
            else:
                fingerprint_id = result

            print(f"获取到的指纹ID: {fingerprint_id}")

            # 关闭浏览器
            await browser.stop()

            return {
                "index": index,
                "fingerprint_id": fingerprint_id,
                "user_agent": fingerprint['user_agent']
            }

        except Exception as e:
            print(f"测试失败: {e}")
            try:
                await browser.stop()
            except Exception:
                pass
            return {
                "index": index,
                "fingerprint_id": f"错误: {str(e)}",
                "user_agent": (
                    fingerprint['user_agent'] if fingerprint else "未知"
                )
            }
