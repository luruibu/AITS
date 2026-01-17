#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库维护工具
用于清理、优化和管理 tree_generator.db 数据库
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

import argparse
from pathlib import Path
from database import db
import json

def print_stats():
    """显示数据库统计信息"""
    print("\n" + "="*60)
    print("📊 数据库统计信息")
    print("="*60)
    
    stats = db.get_database_stats()
    
    print(f"\n💾 数据库文件:")
    print(f"   路径: {db.db_path}")
    print(f"   大小: {stats['database_size_mb']} MB ({stats['database_size']:,} bytes)")
    
    print(f"\n📁 数据统计:")
    print(f"   创作树数量: {stats['trees_count']}")
    print(f"   节点总数: {stats['nodes_count']}")
    print(f"   有图像节点: {stats['nodes_with_images']}")
    print(f"   任务记录: {stats['tasks_count']}")
    print(f"   关键词缓存: {stats['cache_count']}")
    
    print(f"\n🖼️ 图像数据:")
    print(f"   图像数据大小: {stats['image_data_size_mb']} MB ({stats['image_data_size']:,} bytes)")
    print(f"   占数据库比例: {(stats['image_data_size'] / stats['database_size'] * 100):.1f}%")
    
    print(f"\n⚠️ 问题统计:")
    print(f"   失败任务: {stats['failed_tasks']}")
    print(f"   待处理任务: {stats['pending_tasks']}")
    
    if stats['oldest_tree']:
        print(f"\n📅 时间范围:")
        print(f"   最早创作: {stats['oldest_tree']}")
        print(f"   最新创作: {stats['newest_tree']}")
    
    print("\n" + "="*60 + "\n")

def cleanup_image_data(keep_days=7):
    """清理图像数据"""
    print(f"\n🗑️ 清理 {keep_days} 天前的图像数据...")
    
    result = db.cleanup_image_data(keep_days)
    print(f"✅ {result['message']}")
    
    return result['cleaned_nodes']

def cleanup_old_data(days=30):
    """清理旧数据"""
    print(f"\n🗑️ 清理 {days} 天前的旧数据...")
    
    db.cleanup_old_data(days)
    print(f"✅ 已清理旧的已完成任务和低频关键词缓存")

def cleanup_failed_tasks():
    """清理失败的任务"""
    print("\n🧹 清理失败的任务记录...")
    
    deleted = db.cleanup_failed_tasks()
    print(f"✅ 已清理 {deleted} 个失败的任务")
    
    return deleted

def cleanup_orphaned_nodes():
    """清理孤立节点"""
    print("\n🧹 清理孤立节点...")
    
    deleted = db.cleanup_orphaned_nodes()
    print(f"✅ 已清理 {deleted} 个孤立节点")
    
    return deleted

def vacuum_database():
    """优化数据库"""
    print("\n⚡ 优化数据库 (VACUUM)...")
    print("   这可能需要几分钟时间，请耐心等待...")
    
    result = db.vacuum_database()
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"   优化前: {result['before_size_mb']} MB")
        print(f"   优化后: {result['after_size_mb']} MB")
        print(f"   节省空间: {result['saved_size_mb']} MB")
    else:
        print(f"❌ 优化失败: {result['error']}")
    
    return result['success']

def show_large_trees(min_nodes=20):
    """显示大型树"""
    print(f"\n📊 大型树列表 (节点数 >= {min_nodes}):")
    print("="*80)
    
    trees = db.get_large_trees(min_nodes)
    
    if not trees:
        print("   没有找到大型树")
        return
    
    for i, tree in enumerate(trees, 1):
        print(f"\n{i}. {tree['root_prompt'][:60]}...")
        print(f"   树ID: {tree['tree_id']}")
        print(f"   节点数: {tree['node_count']}")
        print(f"   图像大小: {tree['total_image_size_mb']} MB")
        print(f"   创建时间: {tree['created_at']}")
    
    print("\n" + "="*80)

def batch_delete_old_trees(days=30, keep_count=10):
    """批量删除旧树"""
    print(f"\n🗑️ 批量删除旧树...")
    print(f"   删除 {days} 天前的树，保留最近 {keep_count} 个")
    
    # 确认操作
    confirm = input("\n⚠️ 警告：此操作不可撤销！确定要继续吗？(yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    result = db.batch_delete_old_trees(days, keep_count)
    print(f"✅ {result['message']}")
    
    return result['deleted_trees']

def full_cleanup():
    """完整清理流程"""
    print("\n" + "="*60)
    print("🧹 开始完整清理流程")
    print("="*60)
    
    # 1. 显示当前状态
    print_stats()
    
    # 2. 清理图像数据
    cleanup_image_data(7)
    
    # 3. 清理失败任务
    cleanup_failed_tasks()
    
    # 4. 清理孤立节点
    cleanup_orphaned_nodes()
    
    # 5. 清理旧数据
    cleanup_old_data(30)
    
    # 6. 优化数据库
    vacuum_database()
    
    # 7. 显示清理后状态
    print("\n" + "="*60)
    print("✅ 清理完成！")
    print("="*60)
    print_stats()

def export_metadata(tree_id, output_file):
    """导出树的元数据"""
    print(f"\n📤 导出树元数据: {tree_id}")
    
    metadata = db.export_tree_metadata(tree_id)
    
    if not metadata:
        print(f"❌ 树不存在: {tree_id}")
        return False
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 元数据已导出到: {output_file}")
    return True

def main():
    parser = argparse.ArgumentParser(
        description='数据库维护工具 - 管理 tree_generator.db',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --stats                    # 显示数据库统计信息
  %(prog)s --cleanup-images 7         # 清理7天前的图像数据
  %(prog)s --cleanup-old 30           # 清理30天前的旧数据
  %(prog)s --vacuum                   # 优化数据库
  %(prog)s --full-cleanup             # 执行完整清理流程
  %(prog)s --large-trees 20           # 显示节点数>=20的大型树
  %(prog)s --batch-delete 30 10       # 批量删除30天前的树，保留最近10个
        """
    )
    
    parser.add_argument('--stats', action='store_true',
                        help='显示数据库统计信息')
    parser.add_argument('--cleanup-images', type=int, metavar='DAYS',
                        help='清理N天前的图像数据')
    parser.add_argument('--cleanup-old', type=int, metavar='DAYS',
                        help='清理N天前的旧数据')
    parser.add_argument('--cleanup-failed', action='store_true',
                        help='清理失败的任务记录')
    parser.add_argument('--cleanup-orphaned', action='store_true',
                        help='清理孤立节点')
    parser.add_argument('--vacuum', action='store_true',
                        help='优化数据库 (VACUUM)')
    parser.add_argument('--full-cleanup', action='store_true',
                        help='执行完整清理流程')
    parser.add_argument('--large-trees', type=int, metavar='MIN_NODES',
                        help='显示大型树列表')
    parser.add_argument('--batch-delete', nargs=2, type=int, metavar=('DAYS', 'KEEP'),
                        help='批量删除旧树')
    parser.add_argument('--export-metadata', nargs=2, metavar=('TREE_ID', 'OUTPUT'),
                        help='导出树的元数据')
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    try:
        if args.stats:
            print_stats()
        
        if args.cleanup_images:
            cleanup_image_data(args.cleanup_images)
        
        if args.cleanup_old:
            cleanup_old_data(args.cleanup_old)
        
        if args.cleanup_failed:
            cleanup_failed_tasks()
        
        if args.cleanup_orphaned:
            cleanup_orphaned_nodes()
        
        if args.vacuum:
            vacuum_database()
        
        if args.full_cleanup:
            full_cleanup()
        
        if args.large_trees:
            show_large_trees(args.large_trees)
        
        if args.batch_delete:
            batch_delete_old_trees(args.batch_delete[0], args.batch_delete[1])
        
        if args.export_metadata:
            export_metadata(args.export_metadata[0], args.export_metadata[1])
        
        print("\n✅ 操作完成！\n")
        
    except KeyboardInterrupt:
        print("\n\n❌ 操作已中断\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
