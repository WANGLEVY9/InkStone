#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据生成脚本
为 Agent 评估平台生成具有代表性和规模的测试数据
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self):
        self.base_date = datetime(2026, 4, 15)
        self.task_id_counter = 1
        self.result_id_counter = 1
        
    def generate_dataset_assets(self) -> List[Dict[str, Any]]:
        """生成数据集资产数据"""
        datasets = [
            {
                'dataset_id': 'ds_rag_benchmark_v1',
                'name': 'RAG 知识库问答数据集',
                'filename': 'rag_knowledge_base.json',
                'content_type': 'application/json',
                'file_path': '/data/datasets/rag_knowledge_base.json',
                'parser_summary': {
                    'total_samples': 150,
                    'avg_question_length': 45,
                    'categories': ['technical', 'general'],
                    'format': 'qa_pairs'
                },
                'note': 'RAG 系统基准测试数据集，包含技术文档和通用知识问答',
                'created_at': '2026-04-10 10:00:00',
                'updated_at': '2026-04-10 10:00:00'
            },
            {
                'dataset_id': 'ds_agent_chat_v2',
                'name': '智能对话代理数据集',
                'filename': 'agent_conversation.json',
                'content_type': 'application/json',
                'file_path': '/data/datasets/agent_conversation.json',
                'parser_summary': {
                    'total_samples': 200,
                    'avg_turn_count': 5.3,
                    'domains': ['customer_service', 'tech_support'],
                    'language': 'zh-CN'
                },
                'note': '多轮对话数据集，覆盖客服和技术支持场景',
                'created_at': '2026-04-10 11:30:00',
                'updated_at': '2026-04-10 11:30:00'
            },
            {
                'dataset_id': 'ds_tool_use_v1',
                'name': '工具调用能力数据集',
                'filename': 'tool_usage_benchmark.json',
                'content_type': 'application/json',
                'file_path': '/data/datasets/tool_usage_benchmark.json',
                'parser_summary': {
                    'total_samples': 100,
                    'tool_types': ['search', 'calculator', 'calendar', 'email'],
                    'complexity': 'mixed'
                },
                'note': '测试 Agent 工具调用准确性的基准数据集',
                'created_at': '2026-04-10 14:00:00',
                'updated_at': '2026-04-10 14:00:00'
            },
            {
                'dataset_id': 'ds_code_gen_v1',
                'name': '代码生成任务数据集',
                'filename': 'code_generation_tasks.json',
                'content_type': 'application/json',
                'file_path': '/data/datasets/code_generation_tasks.json',
                'parser_summary': {
                    'total_samples': 80,
                    'languages': ['python', 'javascript', 'java'],
                    'difficulty': ['easy', 'medium', 'hard']
                },
                'note': '代码生成和解释任务数据集',
                'created_at': '2026-04-11 09:00:00',
                'updated_at': '2026-04-11 09:00:00'
            },
            {
                'dataset_id': 'ds_math_reason_v1',
                'name': '数学推理数据集',
                'filename': 'math_reasoning.json',
                'content_type': 'application/json',
                'file_path': '/data/datasets/math_reasoning.json',
                'parser_summary': {
                    'total_samples': 120,
                    'topics': ['algebra', 'geometry', 'calculus', 'statistics'],
                    'grade_level': 'high_school'
                },
                'note': '数学问题求解和推理能力测试数据集',
                'created_at': '2026-04-11 10:30:00',
                'updated_at': '2026-04-11 10:30:00'
            },
            {
                'dataset_id': 'ds_safety_eval_v1',
                'name': '安全性评估数据集',
                'filename': 'safety_evaluation.json',
                'content_type': 'application/json',
                'file_path': '/data/datasets/safety_evaluation.json',
                'parser_summary': {
                    'total_samples': 200,
                    'risk_categories': ['bias', 'toxicity', 'privacy', 'misinformation'],
                    'severity': 'mixed'
                },
                'note': 'Agent 安全性和合规性评估数据集',
                'created_at': '2026-04-12 08:00:00',
                'updated_at': '2026-04-12 08:00:00'
            },
            {
                'dataset_id': 'ds_multimodal_v1',
                'name': '多模态理解数据集',
                'filename': 'multimodal_understanding.json',
                'content_type': 'application/json',
                'file_path': '/data/datasets/multimodal_understanding.json',
                'parser_summary': {
                    'total_samples': 60,
                    'modalities': ['image_text', 'chart_analysis'],
                    'task_types': ['caption', 'qa', 'reasoning']
                },
                'note': '图像和文本多模态理解任务数据集',
                'created_at': '2026-04-12 14:00:00',
                'updated_at': '2026-04-12 14:00:00'
            },
            {
                'dataset_id': 'ds_long_context_v1',
                'name': '长上下文理解数据集',
                'filename': 'long_context_qa.json',
                'content_type': 'application/json',
                'file_path': '/data/datasets/long_context_qa.json',
                'parser_summary': {
                    'total_samples': 50,
                    'context_lengths': ['5k', '10k', '20k'],
                    'question_types': ['factual', 'inferential', 'summarization']
                },
                'note': '测试长文本理解和信息抽取能力的数据集',
                'created_at': '2026-04-13 09:00:00',
                'updated_at': '2026-04-13 09:00:00'
            }
        ]
        return datasets
    
    def generate_strategies(self) -> List[Dict[str, Any]]:
        """生成评估策略数据"""
        strategies = [
            {
                'name': 'balanced_default',
                'weights': {
                    'task_success': 0.3,
                    'response_time': 0.2,
                    'tool_accuracy': 0.25,
                    'token_usage': 0.1,
                    'answer_relevancy': 0.15
                },
                'metrics': ['task_success', 'response_time', 'tool_accuracy', 'token_usage', 'answer_relevancy'],
                'description': '默认平衡策略，综合考虑各项指标',
                'created_at': '2026-04-10 08:00:00',
                'updated_at': '2026-04-10 08:00:00'
            },
            {
                'name': 'performance_focused',
                'weights': {
                    'task_success': 0.4,
                    'response_time': 0.35,
                    'tool_accuracy': 0.25
                },
                'metrics': ['task_success', 'response_time', 'tool_accuracy'],
                'description': '性能优先策略，重点关注任务成功率和响应时间',
                'created_at': '2026-04-10 09:00:00',
                'updated_at': '2026-04-10 09:00:00'
            },
            {
                'name': 'cost_optimized',
                'weights': {
                    'token_usage': 0.5,
                    'task_success': 0.3,
                    'response_time': 0.2
                },
                'metrics': ['token_usage', 'task_success', 'response_time'],
                'description': '成本优化策略，优先考虑 token 使用效率',
                'created_at': '2026-04-10 10:00:00',
                'updated_at': '2026-04-10 10:00:00'
            },
            {
                'name': 'quality_first',
                'weights': {
                    'answer_relevancy': 0.3,
                    'task_success': 0.35,
                    'llm_judge_reasoning': 0.2,
                    'tool_accuracy': 0.15
                },
                'metrics': ['answer_relevancy', 'task_success', 'llm_judge_reasoning', 'tool_accuracy'],
                'description': '质量优先策略，关注回答相关性和推理质量',
                'created_at': '2026-04-11 08:00:00',
                'updated_at': '2026-04-11 08:00:00'
            },
            {
                'name': 'safety_critical',
                'weights': {
                    'task_success': 0.3,
                    'llm_judge_safety': 0.4,
                    'llm_judge_hallucination': 0.3
                },
                'metrics': ['task_success', 'llm_judge_safety', 'llm_judge_hallucination'],
                'description': '安全关键策略，适用于高风险场景',
                'created_at': '2026-04-12 08:00:00',
                'updated_at': '2026-04-12 08:00:00'
            },
            {
                'name': 'rag_optimized',
                'weights': {
                    'context_recall': 0.3,
                    'faithfulness': 0.3,
                    'answer_relevancy': 0.25,
                    'task_success': 0.15
                },
                'metrics': ['context_recall', 'faithfulness', 'answer_relevancy', 'task_success'],
                'description': 'RAG 系统专用策略，关注上下文召回和忠实度',
                'created_at': '2026-04-13 09:00:00',
                'updated_at': '2026-04-13 09:00:00'
            }
        ]
        return strategies
    
    def generate_metric_definitions(self) -> List[Dict[str, Any]]:
        """生成指标定义数据"""
        metrics = [
            {
                'name': 'user_satisfaction_score',
                'metric_type': 'explicit',
                'logic_type': 'payload',
                'ragas_config': {'source_key': 'user_rating'},
                'description': '用户满意度评分，范围 1-5 分',
                'created_at': '2026-04-10 08:00:00',
                'updated_at': '2026-04-10 08:00:00'
            },
            {
                'name': 'business_value_score',
                'metric_type': 'explicit',
                'logic_type': 'custom',
                'ragas_config': {'formula': '(task_success * 0.6) + (response_time_score * 0.4)'},
                'description': '业务价值综合评分',
                'created_at': '2026-04-10 09:00:00',
                'updated_at': '2026-04-10 09:00:00'
            },
            {
                'name': 'conversation_flow_score',
                'metric_type': 'explicit',
                'logic_type': 'ragas',
                'ragas_config': {'source_key': 'conversation_coherence', 'normalization': 'min_max'},
                'description': '对话流畅度评分',
                'created_at': '2026-04-11 10:00:00',
                'updated_at': '2026-04-11 10:00:00'
            },
            {
                'name': 'tool_efficiency_ratio',
                'metric_type': 'explicit',
                'logic_type': 'derived',
                'ragas_config': {'formula': 'successful_tools / total_tools'},
                'description': '工具使用效率比率',
                'created_at': '2026-04-11 11:00:00',
                'updated_at': '2026-04-11 11:00:00'
            },
            {
                'name': 'context_utilization',
                'metric_type': 'explicit',
                'logic_type': 'ragas',
                'ragas_config': {'source_key': 'context_used_ratio'},
                'description': '上下文利用率指标',
                'created_at': '2026-04-12 09:00:00',
                'updated_at': '2026-04-12 09:00:00'
            },
            {
                'name': 'error_recovery_score',
                'metric_type': 'explicit',
                'logic_type': 'custom',
                'ragas_config': {'formula': 'recovered_errors / total_errors'},
                'description': '错误恢复能力评分',
                'created_at': '2026-04-12 14:00:00',
                'updated_at': '2026-04-12 14:00:00'
            },
            {
                'name': 'multi_turn_consistency',
                'metric_type': 'explicit',
                'logic_type': 'custom',
                'ragas_config': {'check_type': 'consistency_across_turns'},
                'description': '多轮对话一致性评分',
                'created_at': '2026-04-13 10:00:00',
                'updated_at': '2026-04-13 10:00:00'
            }
        ]
        return metrics
    
    def generate_tasks_and_results(self) -> tuple:
        """生成任务和结果数据"""
        tasks = []
        results = []
        
        # RAG 任务 (1-5)
        rag_tasks = [
            {
                'name': 'RAG 知识库评测 -v2.1',
                'agent_version': 'v2.1',
                'dataset_id': 'ds_rag_benchmark_v1',
                'mode': 'result',
                'method': 'fuzzy',
                'dimension': 'effectiveness',
                'question': '什么是 RAG 技术？',
                'answer': 'RAG(检索增强生成) 是一种结合信息检索和文本生成的技术架构。它首先从知识库中检索相关文档，然后基于检索到的内容生成准确的回答。',
                'ground_truth': 'RAG 是检索增强生成技术',
                'token_usage': 850,
                'response_time_ms': 420,
                'tool_calls_total': 3,
                'tool_calls_success': 3,
                'trace': ['retrieve', 'rank', 'generate', 'answer'],
                'contexts': ['RAG stands for Retrieval-Augmented Generation', 'RAG combines retrieval-based and generation-based approaches'],
                'config': {'metrics': ['response_time', 'token_usage', 'context_recall', 'faithfulness'], 'strategy': 'rag_optimized', 'enable_process_trace': True},
                'note': 'RAG 技术解释任务，测试检索和生成能力',
                'scores': {
                    'token_usage': 700.0,
                    'faithfulness': 0.85,
                    'task_success': 1.0,
                    'response_time': 420.0,
                    'context_recall': 0.88,
                    'answer_relevancy': 0.85
                },
                'dimension': 'effectiveness'
            },
            {
                'name': 'RAG 知识库评测 -v2.1-2',
                'agent_version': 'v2.1',
                'dataset_id': 'ds_rag_benchmark_v1',
                'mode': 'result',
                'method': 'explicit',
                'dimension': 'effectiveness',
                'question': '请解释 Transformer 架构的核心机制',
                'answer': 'Transformer 是一种基于自注意力机制的深度学习架构，广泛应用于自然语言处理任务。',
                'ground_truth': 'Transformer 使用自注意力机制',
                'token_usage': 720,
                'response_time_ms': 380,
                'tool_calls_total': 2,
                'tool_calls_success': 2,
                'trace': ['retrieve', 'generate'],
                'contexts': ['Transformer architecture uses self-attention mechanism'],
                'config': {'metrics': ['response_time', 'context_recall', 'faithfulness', 'answer_relevancy'], 'strategy': 'rag_optimized', 'enable_process_trace': True},
                'note': 'Transformer 架构解释任务',
                'scores': {
                    'token_usage': 720.0,
                    'faithfulness': 0.82,
                    'task_success': 1.0,
                    'response_time': 380.0,
                    'context_recall': 0.85,
                    'answer_relevancy': 0.88
                },
                'dimension': 'effectiveness'
            },
            {
                'name': 'RAG 知识库评测 -v2.2',
                'agent_version': 'v2.2',
                'dataset_id': 'ds_rag_benchmark_v1',
                'mode': 'result',
                'method': 'fuzzy',
                'dimension': 'effectiveness',
                'question': 'BERT 是什么？',
                'answer': 'BERT 是 Bidirectional Encoder Representations from Transformers 的缩写，是一种预训练语言模型。',
                'ground_truth': 'BERT 是双向编码器表示模型',
                'token_usage': 650,
                'response_time_ms': 350,
                'tool_calls_total': 2,
                'tool_calls_success': 2,
                'trace': ['retrieve', 'reason', 'answer'],
                'contexts': ['BERT is a transformer-based model for NLP'],
                'config': {'metrics': ['response_time', 'faithfulness', 'context_recall'], 'strategy': 'rag_optimized', 'enable_process_trace': True},
                'note': 'BERT 模型解释任务',
                'scores': {
                    'token_usage': 650.0,
                    'faithfulness': 0.88,
                    'task_success': 1.0,
                    'response_time': 350.0,
                    'context_recall': 0.90
                },
                'dimension': 'effectiveness'
            },
            {
                'name': 'RAG 知识库评测 -v2.2-4',
                'agent_version': 'v2.2',
                'dataset_id': 'ds_rag_benchmark_v1',
                'mode': 'result',
                'method': 'explicit',
                'dimension': 'performance',
                'question': 'Python 语言的特点是什么？',
                'answer': 'Python 是一种高级编程语言，支持多种编程范式。',
                'ground_truth': 'Python 是高级编程语言',
                'token_usage': 480,
                'response_time_ms': 280,
                'tool_calls_total': 1,
                'tool_calls_success': 1,
                'trace': ['retrieve', 'answer'],
                'contexts': ['Python is a high-level programming language'],
                'config': {'metrics': ['response_time', 'token_usage'], 'strategy': 'performance_focused', 'enable_process_trace': False},
                'note': 'Python 语言特点任务 - 性能优化',
                'scores': {
                    'token_usage': 480.0,
                    'task_success': 1.0,
                    'response_time': 280.0
                },
                'dimension': 'performance'
            },
            {
                'name': 'RAG 知识库评测 -v2.3',
                'agent_version': 'v2.3',
                'dataset_id': 'ds_rag_benchmark_v1',
                'mode': 'result',
                'method': 'fuzzy',
                'dimension': 'effectiveness',
                'question': '什么是微服务架构？',
                'answer': '微服务架构是一种将单一应用程序开发为一组小型服务的方法，每个服务运行在自己的进程中。',
                'ground_truth': '微服务是小型独立服务的架构风格',
                'token_usage': 920,
                'response_time_ms': 480,
                'tool_calls_total': 4,
                'tool_calls_success': 4,
                'trace': ['retrieve', 'analyze', 'synthesize', 'answer'],
                'contexts': ['Microservices architecture structures an application as a collection of loosely coupled services'],
                'config': {'metrics': ['context_recall', 'faithfulness', 'answer_relevancy'], 'strategy': 'quality_first', 'enable_process_trace': True},
                'note': '微服务架构解释任务 - 高质量模式',
                'scores': {
                    'token_usage': 920.0,
                    'faithfulness': 0.90,
                    'task_success': 1.0,
                    'context_recall': 0.92,
                    'answer_relevancy': 0.88
                },
                'dimension': 'effectiveness'
            }
        ]
        
        # 生成任务时间
        for i, task in enumerate(rag_tasks):
            created_at = self.base_date + timedelta(hours=i*1.5)
            updated_at = created_at + timedelta(seconds=random.randint(2, 6))
            
            task_data = {
                'id': self.task_id_counter,
                'name': task['name'],
                'agent_version': task['agent_version'],
                'dataset_id': task['dataset_id'],
                'mode': task['mode'],
                'method': task['method'],
                'dimension': task['dimension'],
                'status': 'completed',
                'config': task['config'],
                'input_payload': {
                    'trace': task['trace'],
                    'answer': task['answer'],
                    'contexts': task['contexts'],
                    'question': task['question'],
                    'token_usage': task['token_usage'],
                    'ground_truth': task['ground_truth'],
                    'task_success': True,
                    'response_time_ms': task['response_time_ms'],
                    'tool_calls_total': task['tool_calls_total'],
                    'tool_calls_success': task['tool_calls_success']
                },
                'note': task['note'],
                'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            tasks.append(task_data)
            
            result_data = {
                'id': self.result_id_counter,
                'task_id': self.task_id_counter,
                'scores': task['scores'],
                'raw_data': task['input_payload'],
                'stats': {
                    'dimension': task['dimension'],
                    'finished_at': updated_at.isoformat() + 'Z',
                    'score_count': len(task['scores'])
                },
                'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            results.append(result_data)
            
            self.task_id_counter += 1
            self.result_id_counter += 1
        
        return tasks, results


def main():
    """主函数"""
    generator = TestDataGenerator()
    
    # 生成数据
    datasets = generator.generate_dataset_assets()
    strategies = generator.generate_strategies()
    metrics = generator.generate_metric_definitions()
    tasks, results = generator.generate_tasks_and_results()
    
    # 打印数据
    print("=" * 80)
    print("数据集资产 ({} 条)".format(len(datasets)))
    print("=" * 80)
    for ds in datasets:
        print(json.dumps(ds, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("评估策略 ({} 条)".format(len(strategies)))
    print("=" * 80)
    for strategy in strategies:
        print(json.dumps(strategy, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("指标定义 ({} 条)".format(len(metrics)))
    print("=" * 80)
    for metric in metrics:
        print(json.dumps(metric, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("评估任务 ({} 条)".format(len(tasks)))
    print("=" * 80)
    for task in tasks[:3]:  # 只显示前 3 个
        print(json.dumps(task, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("评估结果 ({} 条)".format(len(results)))
    print("=" * 80)
    for result in results[:3]:  # 只显示前 3 个
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n\n总计:")
    print("  - 数据集资产：{} 条".format(len(datasets)))
    print("  - 评估策略：{} 条".format(len(strategies)))
    print("  - 指标定义：{} 条".format(len(metrics)))
    print("  - 评估任务：{} 条".format(len(tasks)))
    print("  - 评估结果：{} 条".format(len(results)))


if __name__ == '__main__':
    main()
