"""
违规判定器

整合场景识别和规则管理，执行违规检查，输出违规结果。
这是整个模块的唯一入口。
"""

from typing import List, Optional
from pathlib import Path
import sys
import logging

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from env_node.env_model import EnvironmentModel
from traffic_rule.models import Violation, SceneType, SceneResult
from traffic_rule.scene_identifier import SceneIdentifier
from traffic_rule.rule_manager import RuleManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ViolationDetector:
    """
    违规判定器 - 模块唯一入口
    
    整合场景识别和规则管理，执行违规检查，输出违规结果。
    
    Usage:
        detector = ViolationDetector()
        
        for env_model in trajectory:
            violations = detector.check_violations(env_model)
            for v in violations:
                print(f"违规: {v.rule_name} - {v.description}")
    """
    
    def __init__(self):
        """初始化违规判定器"""
        self.scene_identifier = SceneIdentifier()
        self.rule_manager = RuleManager()
        
        # 统计信息
        self._total_checks = 0
        self._total_violations = 0
        
        logger.info("ViolationDetector 初始化完成")
    
    def check_violations(self, env_model: EnvironmentModel) -> List[Violation]:
        """
        检查违规（唯一外部接口）
        
        ⚠️ 这是交规判断模块的唯一外部接口
        - 轨迹检查由外部（allnode.py）负责调度
        - 模块只负责单帧检查
        
        Args:
            env_model: env_node 输出的环境模型
            
        Returns:
            List[Violation]: 违规列表
        """
        violations = []
        
        try:
            # 1. 场景识别（第一级过滤准备）
            scene_result = self.scene_identifier.identify_scene(env_model)
            scene_type = scene_result.scene_type
            
            # 2. 第一级过滤：查表获取候选规则
            candidate_rules = self.rule_manager.get_rules_to_check(scene_type)
            
            # 3. 执行检查（规则内部会调用 should_check 进行第二级过滤）
            for rule in candidate_rules:
                try:
                    violation = rule.check(env_model)  # ← 规则内部调用 should_check
                    if violation:
                        violations.append(violation)
                        self._total_violations += 1
                        logger.warning(
                            f"检测到违规: {violation.rule_name} - "
                            f"{violation.description} (时间: {violation.timestamp:.2f}s)"
                        )
                except Exception as e:
                    logger.error(f"规则 {rule.id} 检查失败: {e}")
                    continue
            
            self._total_checks += 1
            
        except Exception as e:
            logger.error(f"违规检查失败: {e}")
        
        return violations
    
    def reset_statistics(self):
        """重置统计信息"""
        self._total_checks = 0
        self._total_violations = 0
        
        # 重置所有规则的状态
        for rule in self.rule_manager.get_all_rules():
            if hasattr(rule, 'reset_state'):
                rule.reset_state()
    
    def get_statistics(self) -> dict:
        """
        获取统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            'total_checks': self._total_checks,
            'total_violations': self._total_violations,
            'violation_rate': self._total_violations / max(self._total_checks, 1)
        }
    
    def print_summary(self):
        """打印检查摘要"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("交规检查摘要")
        print("=" * 60)
        print(f"总检查帧数: {stats['total_checks']}")
        print(f"检测到的违规数: {stats['total_violations']}")
        print(f"违规率: {stats['violation_rate']:.2%}")
        print("=" * 60)
