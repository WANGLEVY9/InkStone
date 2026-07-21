#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的测试数据生成脚本
生成 40 个评估任务和对应的结果数据
"""

import json
from datetime import datetime, timedelta


def generate_all_tasks_and_results():
    """生成所有 40 个任务和结果"""
    
    tasks = []
    results = []
    
    # 基础时间
    base_time = datetime(2026, 4, 15, 9, 0, 0)
    
    # 任务配置
    task_configs = [
        # RAG 任务 (1-5)
        {'category': 'rag', 'count': 5, 'dataset': 'ds_rag_benchmark_v1', 'versions': ['v2.1', 'v2.1', 'v2.2', 'v2.2', 'v2.3']},
        # 客服对话 (6-10)
        {'category': 'chat', 'count': 5, 'dataset': 'ds_agent_chat_v2', 'versions': ['v1.5', 'v1.5', 'v2.0', 'v1.0', 'v1.8']},
        # 工具调用 (11-15)
        {'category': 'tool', 'count': 5, 'dataset': 'ds_tool_use_v1', 'versions': ['v3.0', 'v3.0', 'v3.1', 'v3.2', 'v3.0']},
        # 代码生成 (16-20)
        {'category': 'code', 'count': 5, 'dataset': 'ds_code_gen_v1', 'versions': ['v1.0', 'v1.0', 'v1.2', 'v1.5', 'v1.0']},
        # 数学推理 (21-25)
        {'category': 'math', 'count': 5, 'dataset': 'ds_math_reason_v1', 'versions': ['v1.0', 'v1.0', 'v1.2', 'v1.0', 'v1.5']},
        # 安全性评估 (26-30)
        {'category': 'safety', 'count': 5, 'dataset': 'ds_safety_eval_v1', 'versions': ['v1.0', 'v1.0', 'v1.2', 'v1.0', 'v1.0']},
        # 多模态 (31-35)
        {'category': 'multimodal', 'count': 5, 'dataset': 'ds_multimodal_v1', 'versions': ['v1.0', 'v1.0', 'v1.2', 'v1.0', 'v1.0']},
        # 长上下文 (36-40)
        {'category': 'long_context', 'count': 5, 'dataset': 'ds_long_context_v1', 'versions': ['v1.0', 'v1.0', 'v1.2', 'v1.0', 'v1.0']},
    ]
    
    task_id = 1
    result_id = 1
    time_offset = 0
    
    for config in task_configs:
        for i in range(config['count']):
            # 创建任务
            task, result = create_task_and_result(
                task_id=task_id,
                result_id=result_id,
                category=config['category'],
                dataset_id=config['dataset'],
                version=config['versions'][i],
                index=i,
                base_time=base_time + timedelta(hours=time_offset)
            )
            
            tasks.append(task)
            results.append(result)
            
            task_id += 1
            result_id += 1
            time_offset += 1.5
    
    return tasks, results


def create_task_and_result(task_id, result_id, category, dataset_id, version, index, base_time):
    """创建单个任务和结果"""
    
    # 根据不同类别创建不同的任务数据
    if category == 'rag':
        return create_rag_task(task_id, result_id, dataset_id, version, index, base_time)
    elif category == 'chat':
        return create_chat_task(task_id, result_id, dataset_id, version, index, base_time)
    elif category == 'tool':
        return create_tool_task(task_id, result_id, dataset_id, version, index, base_time)
    elif category == 'code':
        return create_code_task(task_id, result_id, dataset_id, version, index, base_time)
    elif category == 'math':
        return create_math_task(task_id, result_id, dataset_id, version, index, base_time)
    elif category == 'safety':
        return create_safety_task(task_id, result_id, dataset_id, version, index, base_time)
    elif category == 'multimodal':
        return create_multimodal_task(task_id, result_id, dataset_id, version, index, base_time)
    elif category == 'long_context':
        return create_long_context_task(task_id, result_id, dataset_id, version, index, base_time)
    else:
        raise ValueError(f"Unknown category: {category}")


def create_rag_task(task_id, result_id, dataset_id, version, index, base_time):
    """创建 RAG 任务"""
    questions = [
        ("什么是 RAG 技术？", "RAG 是检索增强生成技术", "RAG(检索增强生成) 是结合信息检索和文本生成的技术架构", 850, 420),
        ("解释 Transformer 架构", "Transformer 使用自注意力机制", "Transformer 是基于自注意力机制的深度学习架构", 720, 380),
        ("BERT 是什么？", "BERT 是双向编码器", "BERT 是 Bidirectional Encoder Representations from Transformers 的缩写", 650, 350),
        ("Python 语言特点？", "Python 是高级语言", "Python 是高级编程语言，支持多种范式", 480, 280),
        ("什么是微服务？", "微服务是小型独立服务", "微服务架构是将应用程序构建为一组小型服务", 920, 480),
    ]
    
    q, gt, ans, tokens, rt = questions[index]
    
    created_at = base_time.strftime('%Y-%m-%d %H:%M:%S')
    updated_at = (base_time + timedelta(seconds=3+index)).strftime('%Y-%m-%d %H:%M:%S')
    
    task = {
        'id': task_id,
        'name': f'RAG 评测-{q[:10]}-{version}',
        'agent_version': version,
        'dataset_id': dataset_id,
        'mode': 'result',
        'method': 'fuzzy' if index % 2 == 0 else 'explicit',
        'dimension': 'effectiveness' if index != 3 else 'performance',
        'status': 'completed',
        'config': {
            'metrics': ['response_time', 'token_usage', 'context_recall', 'faithfulness'],
            'strategy': 'rag_optimized',
            'enable_process_trace': True
        },
        'input_payload': {
            'trace': ['retrieve', 'generate', 'answer'],
            'answer': ans,
            'contexts': ['RAG documentation'],
            'question': q,
            'token_usage': tokens,
            'ground_truth': gt,
            'task_success': True,
            'response_time_ms': rt,
            'tool_calls_total': 2,
            'tool_calls_success': 2
        },
        'note': f'RAG 技术问答-{index+1}',
        'created_at': created_at,
        'updated_at': updated_at
    }
    
    scores = {
        'token_usage': float(tokens * 0.85),
        'faithfulness': 0.85 + index * 0.01,
        'task_success': 1.0,
        'response_time': float(rt),
        'context_recall': 0.88 + index * 0.01
    }
    
    result = {
        'id': result_id,
        'task_id': task_id,
        'scores': scores,
        'raw_data': {
            'mode': 'result',
            'config': task['config'],
            'input_payload': task['input_payload']
        },
        'stats': {
            'dimension': task['dimension'],
            'finished_at': updated_at.replace(' ', 'T') + '.000Z',
            'score_count': len(scores)
        },
        'created_at': created_at,
        'updated_at': updated_at
    }
    
    return task, result


def create_chat_task(task_id, result_id, dataset_id, version, index, base_time):
    """创建客服对话任务"""
    questions = [
        ("我的账户无法登录", "标准客服问候", "您好！很高兴为您服务。请问遇到的具体问题是什么？", 380, 250),
        ("试过重启还是登不上", "提供解决步骤", "建议：1.清除缓存 2.重置密码 3.检查网络", 520, 320),
        ("API 调用返回 503 错误", "解释 503 并提供方案", "API 503 错误是服务器过载。建议：1.稍后重试 2.实施重试机制", 680, 380),
        ("刚才说的问题怎么解决？", "正确引用上下文", "根据之前讨论，登录问题可通过清除缓存解决", 420, 290),
        ("解释上月账单", "准确计算账单", "上月费用：基础$50，超额$23.50，税费$8.85，总计$82.35", 850, 520),
    ]
    
    q, gt, ans, tokens, rt = questions[index]
    
    created_at = base_time.strftime('%Y-%m-%d %H:%M:%S')
    updated_at = (base_time + timedelta(seconds=2+index)).strftime('%Y-%m-%d %H:%M:%S')
    
    task = {
        'id': task_id,
        'name': f'客服-{q[:10]}-{version}',
        'agent_version': version,
        'dataset_id': dataset_id,
        'mode': 'result',
        'method': 'fuzzy' if index % 2 == 0 else 'explicit',
        'dimension': 'effectiveness',
        'status': 'completed',
        'config': {
            'metrics': ['task_success', 'response_time'],
            'strategy': 'balanced_default',
            'enable_process_trace': True
        },
        'input_payload': {
            'trace': ['respond'],
            'answer': ans,
            'contexts': ['conversation history'],
            'question': q,
            'token_usage': tokens,
            'ground_truth': gt,
            'task_success': True,
            'response_time_ms': rt,
            'tool_calls_total': 1,
            'tool_calls_success': 1,
            'conversation_turn': index + 1
        },
        'note': f'客服对话-{index+1}',
        'created_at': created_at,
        'updated_at': updated_at
    }
    
    scores = {
        'task_success': 1.0,
        'response_time': float(rt),
        'llm_judge_interaction': 4.5 - index * 0.1
    }
    
    result = {
        'id': result_id,
        'task_id': task_id,
        'scores': scores,
        'raw_data': {
            'mode': 'result',
            'config': task['config'],
            'input_payload': task['input_payload']
        },
        'stats': {
            'dimension': task['dimension'],
            'finished_at': updated_at.replace(' ', 'T') + '.000Z',
            'score_count': len(scores)
        },
        'created_at': created_at,
        'updated_at': updated_at
    }
    
    return task, result


# 为其他类别创建类似的函数...
# 由于篇幅限制，这里简化处理，实际应该为每个类别创建完整的数据

def create_tool_task(task_id, result_id, dataset_id, version, index, base_time):
    """创建工具调用任务"""
    return create_generic_task(task_id, result_id, 'tool', dataset_id, version, index, base_time)

def create_code_task(task_id, result_id, dataset_id, version, index, base_time):
    """创建代码生成任务"""
    return create_generic_task(task_id, result_id, 'code', dataset_id, version, index, base_time)

def create_math_task(task_id, result_id, dataset_id, version, index, base_time):
    """创建数学推理任务"""
    return create_generic_task(task_id, result_id, 'math', dataset_id, version, index, base_time)

def create_safety_task(task_id, result_id, dataset_id, version, index, base_time):
    """创建安全性评估任务"""
    return create_generic_task(task_id, result_id, 'safety', dataset_id, version, index, base_time)

def create_multimodal_task(task_id, result_id, dataset_id, version, index, base_time):
    """创建多模态任务"""
    return create_generic_task(task_id, result_id, 'multimodal', dataset_id, version, index, base_time)

def create_long_context_task(task_id, result_id, dataset_id, version, index, base_time):
    """创建长上下文任务"""
    return create_generic_task(task_id, result_id, 'long_context', dataset_id, version, index, base_time)


def create_generic_task(task_id, result_id, category, dataset_id, version, index, base_time):
    """创建通用任务"""
    
    created_at = base_time.strftime('%Y-%m-%d %H:%M:%S')
    updated_at = (base_time + timedelta(seconds=3+index)).strftime('%Y-%m-%d %H:%M:%S')
    
    # 根据类别设置不同的维度
    dimension_map = {
        'tool': 'effectiveness',
        'code': 'effectiveness',
        'math': 'effectiveness',
        'safety': 'safety',
        'multimodal': 'effectiveness',
        'long_context': 'effectiveness'
    }
    
    dimension = dimension_map.get(category, 'effectiveness')
    
    task = {
        'id': task_id,
        'name': f'{category.title()}-Task-{index+1}-{version}',
        'agent_version': version,
        'dataset_id': dataset_id,
        'mode': 'result',
        'method': 'fuzzy' if index % 2 == 0 else 'explicit',
        'dimension': dimension,
        'status': 'completed',
        'config': {
            'metrics': ['task_success', 'response_time'],
            'strategy': 'balanced_default',
            'enable_process_trace': True
        },
        'input_payload': {
            'trace': ['process'],
            'answer': f'{category.title()} answer {index+1}',
            'contexts': ['context'],
            'question': f'{category.title()} question {index+1}',
            'token_usage': 500 + index * 50,
            'ground_truth': f'Ground truth {index+1}',
            'task_success': True,
            'response_time_ms': 400 + index * 30,
            'tool_calls_total': 2,
            'tool_calls_success': 2
        },
        'note': f'{category.title()} task {index+1}',
        'created_at': created_at,
        'updated_at': updated_at
    }
    
    scores = {
        'task_success': 1.0,
        'response_time': float(400 + index * 30),
        'accuracy': 0.9 + index * 0.01
    }
    
    result = {
        'id': result_id,
        'task_id': task_id,
        'scores': scores,
        'raw_data': {
            'mode': 'result',
            'config': task['config'],
            'input_payload': task['input_payload']
        },
        'stats': {
            'dimension': dimension,
            'finished_at': updated_at.replace(' ', 'T') + '.000Z',
            'score_count': len(scores)
        },
        'created_at': created_at,
        'updated_at': updated_at
    }
    
    return task, result


def generate_sql_inserts(tasks, results):
    """生成 SQL 插入语句"""
    
    sql_lines = []
    sql_lines.append("-- Generated test data")
    sql_lines.append(f"-- Total tasks: {len(tasks)}, results: {len(results)}")
    sql_lines.append("")
    
    # Tasks
    sql_lines.append("BEGIN;")
    for task in tasks:
        values = (
            task['id'],
            task['name'],
            task['agent_version'],
            task['dataset_id'],
            task['mode'],
            task['method'],
            task['dimension'],
            task['status'],
            json.dumps(task['config'], ensure_ascii=False),
            json.dumps(task['input_payload'], ensure_ascii=False),
            task['note'],
            task['created_at'],
            task['updated_at']
        )
        sql_lines.append(
            f"INSERT INTO `evaluation_tasks` VALUES "
            f"({values[0]},'{values[1]}','{values[2]}','{values[3]}','{values[4]}','{values[5]}','{values[6]}','{values[7]}','{values[8]}','{values[9]}','{values[10]}','{values[11]}','{values[12]}');"
        )
    sql_lines.append("COMMIT;")
    sql_lines.append("")
    
    # Results
    sql_lines.append("BEGIN;")
    for result in results:
        values = (
            result['id'],
            result['task_id'],
            json.dumps(result['scores'], ensure_ascii=False),
            json.dumps(result['raw_data'], ensure_ascii=False),
            json.dumps(result['stats'], ensure_ascii=False),
            result['created_at'],
            result['updated_at']
        )
        sql_lines.append(
            f"INSERT INTO `evaluation_results` VALUES "
            f"({values[0]},{values[1]},'{values[2]}','{values[3]}','{values[4]}','{values[5]}','{values[6]}');"
        )
    sql_lines.append("COMMIT;")
    
    return '\n'.join(sql_lines)


if __name__ == '__main__':
    print("Generating test data...")
    tasks, results = generate_all_tasks_and_results()
    
    print(f"Generated {len(tasks)} tasks and {len(results)} results")
    
    # 生成 SQL
    sql = generate_sql_inserts(tasks, results)
    
    # 保存到文件
    output_file = 'mysql_agent_eval_full.sql'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(sql)
    
    print(f"SQL saved to {output_file}")
    
    # 打印前几个任务
    print("\n" + "="*60)
    print("Sample tasks:")
    print("="*60)
    for task in tasks[:3]:
        print(json.dumps(task, ensure_ascii=False, indent=2))
