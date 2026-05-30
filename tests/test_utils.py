"""
测试工具函数
"""

import tempfile
import pytest
from pathlib import Path


class TestUtils:
    """测试 utils.py 中的工具函数"""

    def test_safe_filename_basic(self):
        """测试安全文件名生成"""
        from src.utils import safe_filename

        result = safe_filename("test<>file:name", ".txt")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_safe_filename_empty(self):
        """测试空文件名处理"""
        from src.utils import safe_filename

        result = safe_filename("", ".txt")
        assert len(result) > 0  # 应该有默认值

    def test_get_platform(self):
        """测试平台识别"""
        from src.utils import get_platform

        assert get_platform("https://www.douyin.com/video/123") == "douyin"
        assert get_platform("https://www.tiktok.com/@user/video/123") == "tiktok"

    def test_get_platform_unknown(self):
        """测试未知平台"""
        from src.utils import get_platform

        assert get_platform("https://example.com/video/123") == "other"


class TestVideoClassifier:
    """测试视频分类器"""

    def test_classify_video_function_exists(self):
        """测试分类函数存在"""
        from src.video_classifier import classify_video

        assert callable(classify_video)

    def test_get_prompt_for_type_function_exists(self):
        """测试获取提示模板函数存在"""
        from src.video_classifier import get_prompt_for_type

        assert callable(get_prompt_for_type)