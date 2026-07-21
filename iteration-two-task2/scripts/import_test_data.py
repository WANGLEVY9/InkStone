#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent 评估平台测试数据导入脚本
用于向数据库插入具有代表性和规模的测试数据
"""

import sys
import os

# 添加 backend 路径到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.task import EvaluationTask
from app.models.result import EvaluationResult
from app.models.strategy import EvaluationStrategy
from app.models.metric import MetricDefinition
from app.models.dataset import DatasetAsset
from datetime import datetime, timedelta
import json


def create_test_data():
    """创建测试数据"""
    
    # 数据集资产
    datasets = [
        DatasetAsset(
            dataset_id='ds_rag_benchmark_v1',
            name='RAG 知识库问答数据集',
            filename='rag_knowledge_base.json',
            content_type='application/json',
            file_path='/data/datasets/rag_knowledge_base.json',
            parser_summary={"total_samples": 150, "avg_question_length": 45, "categories": ["technical", "general"]},
            note='RAG 系统基准测试数据集'
        ),
        DatasetAsset(
            dataset_id='ds_agent_chat_v2',
            name='智能对话代理数据集',
            filename='agent_conversation.json',
            content_type='application/json',
            file_path='/data/datasets/agent_conversation.json',
            parser_summary={"total_samples": 200, "avg_turn_count": 5.3, "domains": ["customer_service", "tech_support"]},
            note='多轮对话数据集'
        ),
        DatasetAsset(
            dataset_id='ds_tool_use_v1',
            name='工具调用能力数据集',
            filename='tool_usage_benchmark.json',
            content_type='application/json',
            file_path='/data/datasets/tool_usage_benchmark.json',
            parser_summary={"total_samples": 100, "tool_types": ["search", "calculator", "calendar", "email"]},
            note='工具调用基准数据集'
        ),
        DatasetAsset(
            dataset_id='ds_code_gen_v1',
            name='代码生成任务数据集',
            filename='code_generation_tasks.json',
            content_type='application/json',
            file_path='/data/datasets/code_generation_tasks.json',
            parser_summary={"total_samples": 80, "languages": ["python", "javascript", "java"]},
            note='代码生成任务数据集'
        ),
        DatasetAsset(
            dataset_id='ds_math_reason_v1',
            name='数学推理数据集',
            filename='math_reasoning.json',
            content_type='application/json',
            file_path='/data/datasets/math_reasoning.json',
            parser_summary={"total_samples": 120, "topics": ["algebra", "geometry", "calculus", "statistics"]},
            note='数学推理测试数据集'
        ),
        DatasetAsset(
            dataset_id='ds_safety_eval_v1',
            name='安全性评估数据集',
            filename='safety_evaluation.json',
            content_type='application/json',
            file_path='/data/datasets/safety_evaluation.json',
            parser_summary={"total_samples": 200, "risk_categories": ["bias", "toxicity", "privacy", "misinformation"]},
            note='安全性评估数据集'
        ),
        DatasetAsset(
            dataset_id='ds_multimodal_v1',
            name='多模态理解数据集',
            filename='multimodal_understanding.json',
            content_type='application/json',
            file_path='/data/datasets/multimodal_understanding.json',
            parser_summary={"total_samples": 60, "modalities": ["image_text", "chart_analysis"]},
            note='多模态理解数据集'
        ),
        DatasetAsset(
            dataset_id='ds_long_context_v1',
            name='长上下文理解数据集',
            filename='long_context_qa.json',
            content_type='application/json',
            file_path='/data/datasets/long_context_qa.json',
            parser_summary={"total_samples": 50, "context_lengths": ["5k", "10k", "20k"]},
            note='长上下文理解数据集'
        )
    ]
    
    # 评估策略
    strategies = [
        EvaluationStrategy(
            name='balanced_default',
            weights={"task_success": 0.3, "response_time": 0.2, "tool_accuracy": 0.25, "token_usage": 0.1, "answer_relevancy": 0.15},
            metrics=["task_success", "response_time", "tool_accuracy", "token_usage", "answer_relevancy"],
            description='默认平衡策略，综合考虑各项指标'
        ),
        EvaluationStrategy(
            name='performance_focused',
            weights={"task_success": 0.4, "response_time": 0.35, "tool_accuracy": 0.25},
            metrics=["task_success", "response_time", "tool_accuracy"],
            description='性能优先策略，关注任务成功率和响应时间'
        ),
        EvaluationStrategy(
            name='cost_optimized',
            weights={"token_usage": 0.5, "task_success": 0.3, "response_time": 0.2},
            metrics=["token_usage", "task_success", "response_time"],
            description='成本优化策略，优先考虑 token 使用效率'
        ),
        EvaluationStrategy(
            name='quality_first',
            weights={"answer_relevancy": 0.3, "task_success": 0.35, "llm_judge_reasoning": 0.2, "tool_accuracy": 0.15},
            metrics=["answer_relevancy", "task_success", "llm_judge_reasoning", "tool_accuracy"],
            description='质量优先策略，关注回答相关性和推理质量'
        ),
        EvaluationStrategy(
            name='safety_critical',
            weights={"task_success": 0.3, "llm_judge_safety": 0.4, "llm_judge_hallucination": 0.3},
            metrics=["task_success", "llm_judge_safety", "llm_judge_hallucination"],
            description='安全关键策略，适用于高风险场景'
        ),
        EvaluationStrategy(
            name='rag_optimized',
            weights={"context_recall": 0.3, "faithfulness": 0.3, "answer_relevancy": 0.25, "task_success": 0.15},
            metrics=["context_recall", "faithfulness", "answer_relevancy", "task_success"],
            description='RAG 系统专用策略，关注上下文召回和忠实度'
        )
    ]
    
    # 指标定义
    metrics = [
        MetricDefinition(
            name='user_satisfaction_score',
            metric_type='explicit',
            logic_type='payload',
            ragas_config={"source_key": "user_rating"},
            description='用户满意度评分，范围 1-5 分'
        ),
        MetricDefinition(
            name='business_value_score',
            metric_type='explicit',
            logic_type='custom',
            ragas_config={"formula": "(task_success * 0.6) + (response_time_score * 0.4)"},
            description='业务价值综合评分'
        ),
        MetricDefinition(
            name='conversation_flow_score',
            metric_type='explicit',
            logic_type='ragas',
            ragas_config={"source_key": "conversation_coherence", "normalization": "min_max"},
            description='对话流畅度评分'
        ),
        MetricDefinition(
            name='tool_efficiency_ratio',
            metric_type='explicit',
            logic_type='derived',
            ragas_config={"formula": "successful_tools / total_tools"},
            description='工具使用效率比率'
        ),
        MetricDefinition(
            name='context_utilization',
            metric_type='explicit',
            logic_type='ragas',
            ragas_config={"source_key": "context_used_ratio"},
            description='上下文利用率指标'
        ),
        MetricDefinition(
            name='error_recovery_score',
            metric_type='explicit',
            logic_type='custom',
            ragas_config={"formula": "recovered_errors / total_errors"},
            description='错误恢复能力评分'
        ),
        MetricDefinition(
            name='multi_turn_consistency',
            metric_type='explicit',
            logic_type='custom',
            ragas_config={"check_type": "consistency_across_turns"},
            description='多轮对话一致性评分'
        )
    ]
    
    return datasets, strategies, metrics


def import_data():
    """导入数据到数据库"""
    
    # 从环境变量获取数据库 URL
    database_url = os.getenv('DATABASE_URL', 'mysql+pymysql://agent:agent123@mysql:3306/agent_eval')
    
    print(f"连接到数据库：{database_url}")
    
    # 创建数据库引擎
    engine = create_engine(database_url, echo=False)
    
    # 创建表
    print("创建数据库表...")
    Base.metadata.create_all(engine)
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 检查是否已有数据
        existing_datasets = session.query(DatasetAsset).count()
        if existing_datasets > 0:
            print(f"警告：数据库中已有 {existing_datasets} 条数据集记录")
            response = input("是否继续导入？这将添加更多数据 (y/n): ")
            if response.lower() != 'y':
                print("取消导入")
                return
        
        # 创建测试数据
        print("\n生成测试数据...")
        datasets, strategies, metrics = create_test_data()
        
        # 插入数据集
        print(f"\n插入 {len(datasets)} 个数据集...")
        session.add_all(datasets)
        session.commit()
        print("✓ 数据集插入成功")
        
        # 插入策略
        print(f"\n插入 {len(strategies)} 个评估策略...")
        session.add_all(strategies)
        session.commit()
        print("✓ 评估策略插入成功")
        
        # 插入指标
        print(f"\n插入 {len(metrics)} 个指标定义...")
        session.add_all(metrics)
        session.commit()
        print("✓ 指标定义插入成功")
        
        print("\n" + "="*60)
        print("数据导入完成！")
        print("="*60)
        print(f"  - 数据集资产：{len(datasets)} 条")
        print(f"  - 评估策略：{len(strategies)} 条")
        print(f"  - 指标定义：{len(metrics)} 条")
        print("="*60)
        print("\n提示：任务和结果数据量较大，建议通过 API 或前端界面创建")
        
    except Exception as e:
        session.rollback()
        print(f"\n错误：{e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    import_data()
