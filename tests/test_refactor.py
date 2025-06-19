#!/usr/bin/env python3
"""
验证重构后指纹伪装功能的测试文件
"""

def test_imports():
    """测试所有导入是否正常"""
    print("=== 测试导入 ===")
    
    # 测试浏览器类导入
    from pydoll.browser.chromium.chrome import Chrome
    from pydoll.browser.chromium.edge import Edge
    print("✓ 浏览器类导入成功")
    
    # 测试指纹配置导入
    from pydoll.fingerprint import FingerprintConfig, FingerprintManager
    print("✓ 指纹配置导入成功")
    
    # 测试旧的导入是否已删除
    try:
        from pydoll.fingerprint.browser_options import FingerprintBrowserOptionsManager
        print("✗ 错误：旧的FingerprintBrowserOptionsManager仍然存在")
        assert False, "旧的FingerprintBrowserOptionsManager仍然存在"
    except ImportError:
        print("✓ 旧的FingerprintBrowserOptionsManager已正确删除")

def test_chrome_initialization():
    """测试Chrome浏览器初始化"""
    print("\n=== 测试Chrome浏览器 ===")
    
    from pydoll.browser.chromium.chrome import Chrome
    from pydoll.fingerprint import FingerprintConfig
    
    # 测试基本初始化
    chrome = Chrome()
    print(f"✓ Chrome基本初始化: fingerprint_spoofing={chrome.enable_fingerprint_spoofing}")
    assert chrome.enable_fingerprint_spoofing == False
    
    # 测试启用指纹伪装
    chrome_fp = Chrome(enable_fingerprint_spoofing=True)
    print(f"✓ Chrome指纹伪装: enabled={chrome_fp.enable_fingerprint_spoofing}, manager={chrome_fp.fingerprint_manager is not None}")
    assert chrome_fp.enable_fingerprint_spoofing == True
    assert chrome_fp.fingerprint_manager is not None
    
    # 测试自定义配置
    config = FingerprintConfig(browser_type="chrome", enable_webgl_spoofing=True)
    chrome_custom = Chrome(enable_fingerprint_spoofing=True, fingerprint_config=config)
    print(f"✓ Chrome自定义配置: enabled={chrome_custom.enable_fingerprint_spoofing}")
    assert chrome_custom.enable_fingerprint_spoofing == True

def test_edge_initialization():
    """测试Edge浏览器初始化"""
    print("\n=== 测试Edge浏览器 ===")
    
    from pydoll.browser.chromium.edge import Edge
    from pydoll.fingerprint import FingerprintConfig
    
    # 测试基本初始化
    edge = Edge()
    print(f"✓ Edge基本初始化: fingerprint_spoofing={edge.enable_fingerprint_spoofing}")
    assert edge.enable_fingerprint_spoofing == False
    
    # 测试启用指纹伪装
    edge_fp = Edge(enable_fingerprint_spoofing=True)
    print(f"✓ Edge指纹伪装: enabled={edge_fp.enable_fingerprint_spoofing}, manager={edge_fp.fingerprint_manager is not None}")
    assert edge_fp.enable_fingerprint_spoofing == True
    assert edge_fp.fingerprint_manager is not None

def test_options_manager():
    """测试选项管理器"""
    print("\n=== 测试选项管理器 ===")
    
    from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
    from pydoll.fingerprint import FingerprintConfig
    
    # 测试基本管理器
    manager = ChromiumOptionsManager()
    print(f"✓ 基本管理器: fingerprint_spoofing={getattr(manager, 'enable_fingerprint_spoofing', False)}")
    assert getattr(manager, 'enable_fingerprint_spoofing', False) == False
    
    # 测试启用指纹伪装的管理器
    config = FingerprintConfig(browser_type="chrome", enable_webgl_spoofing=True)
    manager_fp = ChromiumOptionsManager(enable_fingerprint_spoofing=True, fingerprint_config=config)
    print(f"✓ 指纹管理器: enabled={manager_fp.enable_fingerprint_spoofing}, manager={manager_fp.fingerprint_manager is not None}")
    assert manager_fp.enable_fingerprint_spoofing == True
    assert manager_fp.fingerprint_manager is not None
    
    # 测试选项初始化
    options = manager_fp.initialize_options()
    print(f"✓ 选项初始化: 参数数量={len(options.arguments)}")
    assert len(options.arguments) >= 2  # 至少应该有默认参数

def main():
    """运行所有测试"""
    print("🔧 重构验证测试")
    print("=" * 50)
    
    # 直接运行测试，不需要收集返回值
    test_imports()
    test_chrome_initialization()
    test_edge_initialization()
    test_options_manager()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过! 重构成功!")

if __name__ == "__main__":
    main() 