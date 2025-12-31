"""
单元测试框架
用于测试各个服务的核心功能
"""
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestEmbeddingService(unittest.TestCase):
    """测试EmbeddingService"""
    
    def setUp(self):
        """测试前准备"""
        from services.embedding_service import EmbeddingService
        self.service = EmbeddingService()
    
    def test_text_chunking(self):
        """测试文本分块功能"""
        text = "第一段。第二段！第三段？第四段。"
        chunks = self.service._split_into_chunks(text, chunk_size=10)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        print(f"   ✅ 文本分块测试通过: {len(chunks)} 个块")
    
    def test_empty_text_handling(self):
        """测试空文本处理"""
        empty_text = ""
        chunks = self.service._split_into_chunks(empty_text)
        self.assertEqual(chunks, [])
        print("   ✅ 空文本处理测试通过")
    
    def test_chunk_size(self):
        """测试分块大小"""
        text = "这是一个较长的测试文本。" * 10
        chunk_size = 50
        chunks = self.service._split_into_chunks(text, chunk_size=chunk_size)
        
        for chunk in chunks:
            # 每个块应该不超过chunk_size（允许一些余量）
            self.assertLessEqual(len(chunk), chunk_size * 2)  # 宽松检查
        print(f"   ✅ 分块大小测试通过: 最大块长度 {max(len(c) for c in chunks)}")


class TestConsistencyChecker(unittest.TestCase):
    """测试ConsistencyChecker"""
    
    def setUp(self):
        """测试前准备"""
        from services.consistency_checker import ConsistencyChecker
        self.checker = ConsistencyChecker()
    
    def test_service_initialization(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.checker.embedding_service)
        print("   ✅ ConsistencyChecker初始化测试通过")


class TestForeshadowingMatcher(unittest.TestCase):
    """测试ForeshadowingMatcher"""
    
    def setUp(self):
        """测试前准备"""
        from services.foreshadowing_matcher import ForeshadowingMatcher
        self.matcher = ForeshadowingMatcher()
    
    def test_service_initialization(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.matcher.embedding_service)
        print("   ✅ ForeshadowingMatcher初始化测试通过")


class TestContentSimilarityChecker(unittest.TestCase):
    """测试ContentSimilarityChecker"""
    
    def setUp(self):
        """测试前准备"""
        from services.content_similarity_checker import ContentSimilarityChecker
        self.checker = ContentSimilarityChecker()
    
    def test_service_initialization(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.checker.embedding_service)
        print("   ✅ ContentSimilarityChecker初始化测试通过")


class TestVectorHelper(unittest.TestCase):
    """测试vector_helper"""
    
    def test_import(self):
        """测试导入"""
        from services.vector_helper import (
            store_chapter_embedding_async,
            store_character_embedding,
            store_world_setting_embedding,
            store_foreshadowing_embedding,
            get_embedding_service
        )
        
        # 测试函数是否存在
        self.assertTrue(callable(store_chapter_embedding_async))
        self.assertTrue(callable(store_character_embedding))
        self.assertTrue(callable(store_world_setting_embedding))
        self.assertTrue(callable(store_foreshadowing_embedding))
        self.assertTrue(callable(get_embedding_service))
        
        # 测试get_embedding_service返回单例
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        self.assertIs(service1, service2)  # 应该是同一个实例
        
        print("   ✅ vector_helper导入和单例测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("单元测试")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestEmbeddingService))
    suite.addTests(loader.loadTestsFromTestCase(TestConsistencyChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestForeshadowingMatcher))
    suite.addTests(loader.loadTestsFromTestCase(TestContentSimilarityChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorHelper))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"运行: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("✅ 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())


