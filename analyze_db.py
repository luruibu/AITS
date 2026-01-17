#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库详细分析工具
深入分析数据库各部分的空间占用
"""

import sys
import os

# Windows编码兼容性设置
if sys.platform.startswith('win'):
    import codecs
    try:
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import sqlite3
from pathlib import Path

def format_size(bytes_size):
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def analyze_database(db_path='tree_generator.db'):
    """详细分析数据库"""
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    # 获取文件大小
    total_size = Path(db_path).stat().st_size
    
    print("\n" + "="*80)
    print("🔍 数据库详细分析报告")
    print("="*80)
    
    print(f"\n📁 数据库文件: {db_path}")
    print(f"💾 总大小: {format_size(total_size)} ({total_size:,} bytes)")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 分析各表的记录数和大小
    print("\n" + "="*80)
    print("📊 表结构分析")
    print("="*80)
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    table_stats = []
    
    for table in tables:
        # 获取记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        # 估算表大小（通过实际数据大小）
        # 获取所有列
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 计算所有列的总大小
        size_query = " + ".join([f"COALESCE(LENGTH({col}), 0)" for col in columns])
        cursor.execute(f"SELECT SUM({size_query}) FROM {table}")
        result = cursor.fetchone()
        size = result[0] if result[0] else 0
        
        table_stats.append({
            'name': table,
            'count': count,
            'size': size,
            'percent': (size / total_size * 100) if total_size > 0 else 0
        })
    
    # 按大小排序
    table_stats.sort(key=lambda x: x['size'], reverse=True)
    
    print(f"\n{'表名':<30} {'记录数':>10} {'大小':>15} {'占比':>10}")
    print("-" * 80)
    
    for stat in table_stats:
        print(f"{stat['name']:<30} {stat['count']:>10,} {format_size(stat['size']):>15} {stat['percent']:>9.2f}%")
    
    # 2. 详细分析nodes表（通常是最大的）
    print("\n" + "="*80)
    print("🔍 nodes表详细分析")
    print("="*80)
    
    # 统计有图像数据的节点
    cursor.execute("SELECT COUNT(*) FROM nodes WHERE image_data IS NOT NULL")
    nodes_with_images = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM nodes WHERE image_data IS NULL")
    nodes_without_images = cursor.fetchone()[0]
    
    print(f"\n节点总数: {nodes_with_images + nodes_without_images:,}")
    print(f"  - 有图像数据: {nodes_with_images:,}")
    print(f"  - 无图像数据: {nodes_without_images:,}")
    
    # 计算图像数据总大小
    cursor.execute("SELECT SUM(LENGTH(image_data)) FROM nodes WHERE image_data IS NOT NULL")
    result = cursor.fetchone()
    image_data_size = result[0] if result[0] else 0
    
    print(f"\n图像数据总大小: {format_size(image_data_size)} ({image_data_size:,} bytes)")
    print(f"图像数据占比: {(image_data_size / total_size * 100):.2f}%")
    
    if nodes_with_images > 0:
        avg_image_size = image_data_size / nodes_with_images
        print(f"平均每张图像: {format_size(avg_image_size)}")
    
    # 计算其他字段的大小
    cursor.execute("""
        SELECT 
            SUM(LENGTH(prompt)) as prompt_size,
            SUM(LENGTH(keywords)) as keywords_size,
            SUM(LENGTH(branch_info)) as branch_info_size,
            SUM(LENGTH(image_path)) as image_path_size
        FROM nodes
    """)
    result = cursor.fetchone()
    
    if result:
        prompt_size, keywords_size, branch_info_size, image_path_size = result
        prompt_size = prompt_size or 0
        keywords_size = keywords_size or 0
        branch_info_size = branch_info_size or 0
        image_path_size = image_path_size or 0
        
        print(f"\n其他字段大小:")
        print(f"  - 提示词 (prompt): {format_size(prompt_size)}")
        print(f"  - 关键词 (keywords): {format_size(keywords_size)}")
        print(f"  - 分支信息 (branch_info): {format_size(branch_info_size)}")
        print(f"  - 图像路径 (image_path): {format_size(image_path_size)}")
    
    # 3. 分析keyword_cache表
    print("\n" + "="*80)
    print("🔍 keyword_cache表分析")
    print("="*80)
    
    cursor.execute("SELECT COUNT(*) FROM keyword_cache")
    cache_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(LENGTH(keywords)) FROM keyword_cache")
    result = cursor.fetchone()
    cache_size = result[0] if result[0] else 0
    
    print(f"\n缓存记录数: {cache_count:,}")
    print(f"缓存数据大小: {format_size(cache_size)}")
    print(f"缓存占比: {(cache_size / total_size * 100):.2f}%")
    
    # 分析使用频率
    cursor.execute("""
        SELECT 
            COUNT(*) as count,
            SUM(CASE WHEN usage_count = 1 THEN 1 ELSE 0 END) as single_use,
            SUM(CASE WHEN usage_count > 1 THEN 1 ELSE 0 END) as multi_use
        FROM keyword_cache
    """)
    result = cursor.fetchone()
    if result:
        total, single, multi = result
        print(f"\n使用频率分析:")
        print(f"  - 仅使用1次: {single:,} ({(single/total*100):.1f}%)")
        print(f"  - 使用多次: {multi:,} ({(multi/total*100):.1f}%)")
    
    # 4. 分析generation_tasks表
    print("\n" + "="*80)
    print("🔍 generation_tasks表分析")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            SUM(LENGTH(result)) as result_size,
            SUM(LENGTH(error_message)) as error_size
        FROM generation_tasks
        GROUP BY status
    """)
    
    print(f"\n{'状态':<15} {'数量':>10} {'结果大小':>15} {'错误信息大小':>15}")
    print("-" * 80)
    
    for row in cursor.fetchall():
        status, count, result_size, error_size = row
        result_size = result_size or 0
        error_size = error_size or 0
        print(f"{status:<15} {count:>10,} {format_size(result_size):>15} {format_size(error_size):>15}")
    
    # 5. 数据库内部结构分析
    print("\n" + "="*80)
    print("🔍 数据库内部结构")
    print("="*80)
    
    # 获取页面统计
    cursor.execute("PRAGMA page_count")
    page_count = cursor.fetchone()[0]
    
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    
    cursor.execute("PRAGMA freelist_count")
    freelist_count = cursor.fetchone()[0]
    
    used_pages = page_count - freelist_count
    used_size = used_pages * page_size
    free_size = freelist_count * page_size
    
    print(f"\n页面信息:")
    print(f"  - 页面大小: {format_size(page_size)}")
    print(f"  - 总页面数: {page_count:,}")
    print(f"  - 使用页面: {used_pages:,} ({format_size(used_size)})")
    print(f"  - 空闲页面: {freelist_count:,} ({format_size(free_size)})")
    print(f"  - 空间利用率: {(used_size / total_size * 100):.2f}%")
    
    if freelist_count > 0:
        print(f"\n💡 提示: 有 {format_size(free_size)} 的空闲空间可以通过 VACUUM 回收")
    
    # 6. 索引分析
    print("\n" + "="*80)
    print("🔍 索引分析")
    print("="*80)
    
    cursor.execute("""
        SELECT name, tbl_name 
        FROM sqlite_master 
        WHERE type='index' AND sql IS NOT NULL
        ORDER BY tbl_name, name
    """)
    
    indexes = cursor.fetchall()
    
    print(f"\n索引总数: {len(indexes)}")
    
    index_stats = []
    for idx_name, tbl_name in indexes:
        # 简化：索引大小难以精确计算，使用估算
        size = 0  # 暂时设为0，因为无法精确计算
        index_stats.append({
            'name': idx_name,
            'table': tbl_name,
            'size': size
        })
    
    index_stats.sort(key=lambda x: x['size'], reverse=True)
    
    total_index_size = sum(s['size'] for s in index_stats)
    
    # 估算索引大小为数据大小的10-20%
    estimated_index_size = int(total_size * 0.15)
    
    print(f"索引估算大小: {format_size(estimated_index_size)} (约占 15%)")
    
    if len(index_stats) > 0:
        print(f"\n索引列表:")
        print(f"{'索引名':<40} {'表名':<20}")
        print("-" * 80)
        
        for stat in index_stats[:10]:  # 只显示前10个
            print(f"{stat['name']:<40} {stat['table']:<20}")
    
    # 7. 总结和建议
    print("\n" + "="*80)
    print("💡 分析总结和建议")
    print("="*80)
    
    print("\n📊 空间占用排名:")
    
    # 计算其他开销（数据库元数据、索引等）
    accounted_size = image_data_size + cache_size + free_size
    other_overhead = total_size - accounted_size
    
    components = [
        ('图像数据', image_data_size),
        ('数据库开销(索引/元数据等)', other_overhead),
        ('关键词缓存', cache_size),
        ('空闲空间', free_size),
    ]
    
    components.sort(key=lambda x: x[1], reverse=True)
    
    for i, (name, size) in enumerate(components, 1):
        percent = (size / total_size * 100) if total_size > 0 else 0
        print(f"{i}. {name}: {format_size(size)} ({percent:.2f}%)")
    
    print("\n🎯 优化建议:")
    
    suggestions = []
    
    if image_data_size > total_size * 0.5:
        suggestions.append("⚠️ 图像数据占比超过50%，建议清理旧图像数据")
        suggestions.append("   命令: python db_maintenance.py --cleanup-images 7")
    
    if freelist_count > page_count * 0.1:
        suggestions.append("⚠️ 空闲空间超过10%，建议执行VACUUM优化")
        suggestions.append("   命令: python db_maintenance.py --vacuum")
    
    if cache_count > 1000:
        cursor.execute("SELECT COUNT(*) FROM keyword_cache WHERE usage_count = 1")
        single_use = cursor.fetchone()[0]
        if single_use > cache_count * 0.5:
            suggestions.append("⚠️ 超过50%的缓存仅使用1次，建议清理")
            suggestions.append("   命令: python db_maintenance.py --cleanup-old 30")
    
    cursor.execute("SELECT COUNT(*) FROM generation_tasks WHERE status = 'failed'")
    failed_tasks = cursor.fetchone()[0]
    if failed_tasks > 0:
        suggestions.append(f"⚠️ 有 {failed_tasks} 个失败任务，建议清理")
        suggestions.append("   命令: python db_maintenance.py --cleanup-failed")
    
    if not suggestions:
        suggestions.append("✅ 数据库状态良好，暂无优化建议")
    
    for suggestion in suggestions:
        print(suggestion)
    
    # 8. 预期优化效果
    if image_data_size > 0 or freelist_count > 0:
        print("\n📈 预期优化效果:")
        
        potential_savings = 0
        
        if image_data_size > total_size * 0.5:
            # 假设清理70%的图像数据
            image_savings = image_data_size * 0.7
            potential_savings += image_savings
            print(f"  - 清理图像数据: 可节省约 {format_size(image_savings)}")
        
        if freelist_count > 0:
            potential_savings += free_size
            print(f"  - VACUUM优化: 可节省约 {format_size(free_size)}")
        
        if potential_savings > 0:
            final_size = total_size - potential_savings
            print(f"\n  总计可节省: {format_size(potential_savings)} ({(potential_savings / total_size * 100):.1f}%)")
            print(f"  优化后大小: {format_size(final_size)}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ 分析完成")
    print("="*80 + "\n")

if __name__ == '__main__':
    analyze_database()
