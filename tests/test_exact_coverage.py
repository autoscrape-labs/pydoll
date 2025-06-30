"""
精确测试来覆盖 Codecov 报告中未覆盖的代码行：
- pydoll/fingerprint/generator.py#L335 (fallback browser type)
- pydoll/fingerprint/manager.py#L55 (return current_fingerprint)  
- pydoll/fingerprint/manager.py#L262 (return False when file doesn't exist)
- pydoll/browser/managers/browser_options_manager.py#L71 (early return when no fingerprint manager)

这个文件合并了 test_additional_coverage.py 和 test_exact_coverage.py 的所有测试。
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from pydoll.fingerprint.generator import FingerprintGenerator
from pydoll.fingerprint.manager import FingerprintManager
from pydoll.fingerprint.models import FingerprintConfig
from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions


class TestExactCoverage:
    """精确测试未覆盖的代码行"""

    def test_generator_line_335_fallback_browser_type(self):
        """
        测试 generator.py#L335 - _generate_user_agent 中的 fallback 情况
        当 browser_type 既不是 'chrome' 也不是 'edge' 时
        """
        # 创建一个配置，设置 browser_type 为非 chrome/edge 的值
        config = FingerprintConfig()
        config.browser_type = 'firefox'  # 这会触发 fallback 到 Chrome
        config.is_mobile = False
        
        generator = FingerprintGenerator(config)
        
        # 模拟操作系统信息和浏览器版本
        os_info = {'name': 'Windows', 'version': '10.0'}
        browser_version = '120.0.6099.129'
        
        # 调用 _generate_user_agent，这应该命中第335行的 fallback
        user_agent = generator._generate_user_agent(os_info, browser_version)
        
        # 验证生成了 Chrome 用户代理（fallback 行为）
        assert 'Chrome' in user_agent
        assert 'Windows NT 10.0' in user_agent
        assert browser_version in user_agent

    def test_generator_unique_properties_method(self):
        """测试 _generate_unique_properties 静态方法的调用"""
        # 直接调用静态方法确保被执行
        result = FingerprintGenerator._generate_unique_properties()
        
        # 验证返回值结构
        assert isinstance(result, dict)
        assert "unique_id" in result
        assert isinstance(result["unique_id"], str)
        assert len(result["unique_id"]) > 0
        
        # 多次调用确保生成不同的值
        result2 = FingerprintGenerator._generate_unique_properties()
        assert result["unique_id"] != result2["unique_id"]

    def test_manager_line_55_return_current_fingerprint(self):
        """
        测试 manager.py#L55 - get_current_fingerprint 返回当前指纹
        """
        manager = FingerprintManager()
        
        # 首先确保 current_fingerprint 是 None
        assert manager.current_fingerprint is None
        result = manager.get_current_fingerprint()
        assert result is None
        
        # 生成一个指纹
        fingerprint = manager.generate_new_fingerprint()
        assert manager.current_fingerprint is not None
        
        # 现在调用 get_current_fingerprint - 这应该命中第55行
        current = manager.get_current_fingerprint()
        
        # 验证返回的是同一个指纹
        assert current is fingerprint
        assert current == manager.current_fingerprint

    def test_manager_line_262_delete_nonexistent_return_false(self):
        """
        测试 manager.py#L262 - delete_fingerprint 当文件不存在时返回 False
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # 尝试删除不存在的文件 - 这应该命中第262行的 return False
            result = manager.delete_fingerprint("definitely_does_not_exist")
            
            # 验证返回 False
            assert result is False
            
            # 验证没有文件被创建
            files = list(manager.storage_dir.glob("*.json"))
            assert len(files) == 0

    def test_browser_options_manager_line_71_no_fingerprint_manager(self):
        """测试 browser_options_manager.py#L71 - 当没有fingerprint manager时的早期返回"""
        # 创建一个没有启用指纹欺骗的管理器
        manager = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        manager.options = ChromiumOptions()
        
        # 手动设置 fingerprint_manager 为 None 以确保命中第71行
        manager.fingerprint_manager = None
        
        # 调用 _apply_fingerprint_spoofing - 应该在第71行早期返回
        result = manager._apply_fingerprint_spoofing()
        assert result is None

    def test_comprehensive_coverage_verification(self):
        """
        综合测试确保所有4行都被覆盖
        """
        # 1. 测试 generator fallback (line 335)
        config = FingerprintConfig()
        config.browser_type = 'unknown_browser'  # 触发 fallback
        generator = FingerprintGenerator(config)
        
        os_info = {'name': 'Linux', 'version': 'x86_64'}
        user_agent = generator._generate_user_agent(os_info, '120.0.0.0')
        assert 'Chrome' in user_agent  # 应该 fallback 到 Chrome
        
        # 2. 测试 unique properties 
        unique_props = FingerprintGenerator._generate_unique_properties()
        assert "unique_id" in unique_props
        
        # 3. 测试 manager get_current_fingerprint (line 55)
        manager = FingerprintManager()
        fp = manager.generate_new_fingerprint()
        current = manager.get_current_fingerprint()
        assert current is fp
        
        # 4. 测试 manager delete_fingerprint 返回 False (line 262)
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.storage_dir = Path(temp_dir)
            assert manager.delete_fingerprint("nonexistent") is False
            
        # 5. 测试 browser options manager (line 71)
        options_manager = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        options_manager.fingerprint_manager = None
        result = options_manager._apply_fingerprint_spoofing()
        assert result is None

    def test_browser_type_variations_for_fallback(self):
        """
        测试各种 browser_type 值来确保 fallback 被触发
        """
        test_cases = [
            'firefox',
            'safari',
            'opera', 
            'unknown',
            'invalid',
            None,  # 如果为 None，应该也触发 fallback
        ]
        
        for browser_type in test_cases:
            config = FingerprintConfig()
            config.browser_type = browser_type
            config.is_mobile = False
            
            generator = FingerprintGenerator(config)
            
            os_info = {'name': 'Windows', 'version': '10.0'}
            browser_version = '120.0.0.0'
            
            # 这应该都触发第335行的 fallback
            user_agent = generator._generate_user_agent(os_info, browser_version)
            
            # 验证都 fallback 到了 Chrome
            assert 'Chrome' in user_agent
            assert 'Windows NT 10.0' in user_agent

    def test_manager_state_transitions(self):
        """
        测试 manager 状态转换来覆盖第55行
        """
        manager = FingerprintManager()
        
        # 初始状态：None
        assert manager.get_current_fingerprint() is None
        
        # 生成指纹后
        fp1 = manager.generate_new_fingerprint()
        assert manager.get_current_fingerprint() is fp1  # 命中第55行
        
        # 强制生成新指纹
        fp2 = manager.generate_new_fingerprint(force=True)
        assert manager.get_current_fingerprint() is fp2  # 再次命中第55行
        
        # 清除后
        manager.clear_current_fingerprint()
        assert manager.get_current_fingerprint() is None

    def test_delete_operations_coverage(self):
        """
        测试删除操作来覆盖第262行
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # 多次尝试删除不同的不存在文件
            test_names = [
                "nonexistent1",
                "nonexistent2", 
                "fake_fingerprint",
                "",  # 空字符串
                "very_long_name_that_definitely_does_not_exist",
            ]
            
            for name in test_names:
                # 每次都应该命中第262行的 return False
                result = manager.delete_fingerprint(name)
                assert result is False

    def test_edge_cases_for_complete_coverage(self):
        """额外的边界测试确保100%覆盖所有目标行"""
        
        # 测试多次调用 unique properties
        props1 = FingerprintGenerator._generate_unique_properties()
        props2 = FingerprintGenerator._generate_unique_properties()
        props3 = FingerprintGenerator._generate_unique_properties()
        
        # 确保它们都是不同的
        unique_ids = [props1["unique_id"], props2["unique_id"], props3["unique_id"]]
        assert len(set(unique_ids)) == 3  # 所有都应该是唯一的
        
        # 测试 manager 状态转换
        manager = FingerprintManager()
        
        # 当为 None 时多次调用
        assert manager.get_current_fingerprint() is None
        assert manager.get_current_fingerprint() is None
        
        # 生成后测试多次调用
        fp = manager.generate_new_fingerprint()
        assert manager.get_current_fingerprint() is fp
        assert manager.get_current_fingerprint() is fp
        
        # 清除并再次测试
        manager.clear_current_fingerprint()
        assert manager.get_current_fingerprint() is None
        
        # 测试删除操作
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.storage_dir = Path(temp_dir)
            
            # 多次删除不存在文件的尝试
            assert manager.delete_fingerprint("file1") is False
            assert manager.delete_fingerprint("file2") is False
            assert manager.delete_fingerprint("") is False

    def test_fingerprint_integration_complete_workflow(self):
        """完整的指纹集成工作流测试"""
        # 测试完整的工作流程，应该覆盖所有行
        
        # 1. 测试 unique properties 生成 
        unique_props = FingerprintGenerator._generate_unique_properties()
        assert "unique_id" in unique_props
        
        # 2. 测试 fingerprint manager 工作流 (line 55 和 262)
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = FingerprintManager()
            manager.storage_dir = Path(temp_dir)
            
            # 初始时没有指纹
            assert manager.get_current_fingerprint() is None
            
            # 生成一个
            fingerprint = manager.generate_new_fingerprint()
            
            # 测试第55行 - 返回当前指纹
            current = manager.get_current_fingerprint()
            assert current is fingerprint
            
            # 测试第262行 - 删除不存在的文件
            assert manager.delete_fingerprint("fake") is False
            
        # 3. 测试 browser options manager (line 71)
        options_manager = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        options_manager.fingerprint_manager = None
        result = options_manager._apply_fingerprint_spoofing()
        assert result is None
        
        # 4. 测试 generator fallback (line 335)
        config = FingerprintConfig()
        config.browser_type = 'unsupported_browser'
        config.is_mobile = False
        generator = FingerprintGenerator(config)
        
        os_info = {'name': 'Windows', 'version': '10.0'}
        user_agent = generator._generate_user_agent(os_info, '120.0.0.0')
        assert 'Chrome' in user_agent  # 应该 fallback 到 Chrome

    def test_various_browser_options_scenarios(self):
        """测试各种浏览器选项场景"""
        # 测试启用指纹欺骗但手动设置为None的情况
        manager_enabled = ChromiumOptionsManager(enable_fingerprint_spoofing=True)
        manager_enabled.options = ChromiumOptions()
        manager_enabled.fingerprint_manager = None  # 手动设置为None
        
        # 这应该命中第71行的早期返回
        result = manager_enabled._apply_fingerprint_spoofing()
        assert result is None
        
        # 测试禁用指纹欺骗的情况
        manager_disabled = ChromiumOptionsManager(enable_fingerprint_spoofing=False)
        manager_disabled.options = ChromiumOptions()
        assert manager_disabled.fingerprint_manager is None
        
        # 这也应该命中第71行
        result = manager_disabled._apply_fingerprint_spoofing()
        assert result is None 