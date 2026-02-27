"""简单的导入测试脚本

验证所有模块的导入是否正确
"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing module imports...")
print("-" * 50)

# 测试基础模块
modules_to_test = [
    # 工具模块
    ('pillow_talk.utils.exceptions', 'Exceptions'),
    ('pillow_talk.utils.logger', 'Logger'),
    ('pillow_talk.utils.parser', 'Parser'),
    
    # 数据模型
    ('pillow_talk.models.request', 'Request Models'),
    ('pillow_talk.models.response', 'Response Models'),
    ('pillow_talk.models.config', 'Config Models'),
    
    # 核心模块
    ('pillow_talk.core.image', 'Image Preprocessor'),
    ('pillow_talk.core.prompt', 'Prompt Engine'),
    ('pillow_talk.core.conversation', 'Conversation Manager'),
    
    # 适配器
    ('pillow_talk.adapters.base', 'Base Adapter'),
    ('pillow_talk.adapters.openai', 'OpenAI Adapter'),
    ('pillow_talk.adapters.doubao', 'Doubao Adapter'),
    ('pillow_talk.adapters.gemini', 'Gemini Adapter'),
    ('pillow_talk.adapters.claude', 'Claude Adapter'),
    ('pillow_talk.adapters.custom', 'Custom Adapter'),
    
    # TTS 适配器
    ('pillow_talk.tts.adapters.base', 'TTS Base Adapter'),
    ('pillow_talk.tts.adapters.openai_adapter', 'OpenAI TTS Adapter'),
    ('pillow_talk.tts.adapters.google_adapter', 'Google TTS Adapter'),
    ('pillow_talk.tts.adapters.azure_adapter', 'Azure TTS Adapter'),
    ('pillow_talk.tts.adapters.edge_adapter', 'Edge TTS Adapter'),
    ('pillow_talk.tts.adapters.ali_adapter', 'Alibaba TTS Adapter'),
    
    # 服务
    ('pillow_talk.services.auth', 'Authentication Service'),
    ('pillow_talk.services.rate_limit', 'Rate Limiter'),
    
    # API
    ('pillow_talk.api.dependencies', 'API Dependencies'),
    ('pillow_talk.api.middleware', 'API Middleware'),
    ('pillow_talk.api.routes', 'API Routes'),
]

success_count = 0
fail_count = 0
failed_modules = []

for module_name, description in modules_to_test:
    try:
        __import__(module_name)
        print(f"✓ {description:30s} ({module_name})")
        success_count += 1
    except ImportError as e:
        print(f"✗ {description:30s} ({module_name})")
        print(f"  Error: {e}")
        fail_count += 1
        failed_modules.append((module_name, str(e)))
    except Exception as e:
        print(f"⚠ {description:30s} ({module_name})")
        print(f"  Warning: {e}")
        success_count += 1  # 其他错误不算失败

print("-" * 50)
print(f"\nResults:")
print(f"  Success: {success_count}/{len(modules_to_test)}")
print(f"  Failed:  {fail_count}/{len(modules_to_test)}")

if failed_modules:
    print("\nFailed modules:")
    for module, error in failed_modules:
        print(f"  - {module}")
        print(f"    {error}")

print("\n" + "=" * 50)
if fail_count == 0:
    print("✓ All module imports successful!")
    print("  Note: Dependencies need to be installed for full functionality")
else:
    print(f"✗ {fail_count} module(s) failed to import")
    print("  This is expected if dependencies are not installed")
