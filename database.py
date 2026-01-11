#!/usr/bin/env python3
"""
简单的SQLite数据库管理系统
用于存储生成任务、树结构和优化性能
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class TreeDatabase:
    """树状图像生成数据库"""
    
    def __init__(self, db_path: str = "tree_generator.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trees (
                    tree_id TEXT PRIMARY KEY,
                    root_prompt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    tree_id TEXT NOT NULL,
                    parent_id TEXT,
                    prompt TEXT NOT NULL,
                    image_path TEXT,
                    image_data TEXT,
                    keywords TEXT,
                    quality_score REAL DEFAULT 0.0,
                    accuracy_score REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending',
                    branch_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tree_id) REFERENCES trees (tree_id),
                    FOREIGN KEY (parent_id) REFERENCES nodes (node_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS generation_tasks (
                    task_id TEXT PRIMARY KEY,
                    tree_id TEXT NOT NULL,
                    node_id TEXT,
                    task_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (tree_id) REFERENCES trees (tree_id),
                    FOREIGN KEY (node_id) REFERENCES nodes (node_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS keyword_cache (
                    prompt_hash TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 1
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引优化查询性能
            conn.execute('CREATE INDEX IF NOT EXISTS idx_nodes_tree_id ON nodes (tree_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_nodes_parent_id ON nodes (parent_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON generation_tasks (status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_keyword_cache_hash ON keyword_cache (prompt_hash)')
            
            conn.commit()
    
    def create_tree(self, root_prompt: str, metadata: Dict = None) -> str:
        """创建新的生成树"""
        tree_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO trees (tree_id, root_prompt, metadata)
                VALUES (?, ?, ?)
            ''', (tree_id, root_prompt, json.dumps(metadata or {})))
            
            # 创建根节点
            root_id = str(uuid.uuid4())
            branch_info = {
                'level': 0,
                'branch_index': 0,
                'branch_direction': 'root',
                'version': 'v1.0'
            }
            
            conn.execute('''
                INSERT INTO nodes (node_id, tree_id, parent_id, prompt, branch_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (root_id, tree_id, None, root_prompt, json.dumps(branch_info)))
            
            conn.commit()
        
        return tree_id
    
    def add_node(self, tree_id: str, prompt: str, parent_id: str = None, 
                 branch_direction: str = None) -> str:
        """添加新节点"""
        node_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            # 计算分支信息
            if parent_id:
                parent_info = conn.execute('''
                    SELECT branch_info FROM nodes WHERE node_id = ?
                ''', (parent_id,)).fetchone()
                
                if parent_info:
                    parent_branch = json.loads(parent_info[0] or '{}')
                    parent_level = parent_branch.get('level', 0)
                    
                    # 计算同级节点数量
                    sibling_count = conn.execute('''
                        SELECT COUNT(*) FROM nodes WHERE parent_id = ?
                    ''', (parent_id,)).fetchone()[0]
                    
                    branch_info = {
                        'level': parent_level + 1,
                        'branch_index': sibling_count,
                        'branch_direction': branch_direction or f'分支{sibling_count + 1}',
                        'version': f'v{parent_level + 1}.{sibling_count + 1}'
                    }
                else:
                    branch_info = {'level': 1, 'branch_index': 0, 'branch_direction': 'branch', 'version': 'v2.1'}
            else:
                branch_info = {'level': 0, 'branch_index': 0, 'branch_direction': 'root', 'version': 'v1.0'}
            
            conn.execute('''
                INSERT INTO nodes (node_id, tree_id, parent_id, prompt, branch_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (node_id, tree_id, parent_id, prompt, json.dumps(branch_info)))
            
            conn.commit()
        
        return node_id
    
    def update_node(self, node_id: str, **kwargs):
        """更新节点信息"""
        if not kwargs:
            return
        
        # 构建更新语句
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['image_path', 'image_data', 'status', 'quality_score', 'accuracy_score', 'prompt']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
            elif key == 'keywords':
                set_clauses.append("keywords = ?")
                values.append(json.dumps(value) if value else None)
            elif key == 'branch_info':
                set_clauses.append("branch_info = ?")
                values.append(json.dumps(value) if value else None)
        
        if set_clauses:
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(node_id)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f'''
                    UPDATE nodes SET {', '.join(set_clauses)}
                    WHERE node_id = ?
                ''', values)
                conn.commit()
    
    def get_tree(self, tree_id: str) -> Optional[Dict]:
        """获取完整的树结构"""
        with sqlite3.connect(self.db_path) as conn:
            # 获取树信息
            tree_info = conn.execute('''
                SELECT tree_id, root_prompt, created_at, status, metadata
                FROM trees WHERE tree_id = ?
            ''', (tree_id,)).fetchone()
            
            if not tree_info:
                return None
            
            # 获取所有节点
            nodes_data = conn.execute('''
                SELECT node_id, parent_id, prompt, image_path, image_data,
                       keywords, quality_score, accuracy_score, status,
                       branch_info, created_at
                FROM nodes WHERE tree_id = ?
                ORDER BY created_at
            ''', (tree_id,)).fetchall()
            
            # 构建树结构
            nodes = {}
            root_id = None
            
            for node_data in nodes_data:
                node_id, parent_id, prompt, image_path, image_data, keywords_json, \
                quality_score, accuracy_score, status, branch_info_json, created_at = node_data
                
                node = {
                    'node_id': node_id,
                    'prompt': prompt,
                    'parent_id': parent_id,
                    'children': [],
                    'image_path': image_path,
                    'image_data': image_data,
                    'keywords': json.loads(keywords_json) if keywords_json else [],
                    'quality_score': quality_score or 0.0,
                    'accuracy_score': accuracy_score or 0.0,
                    'status': status,
                    'branch_info': json.loads(branch_info_json) if branch_info_json else {},
                    'created_at': created_at
                }
                
                nodes[node_id] = node
                
                if not parent_id:  # 根节点
                    root_id = node_id
            
            # 构建父子关系
            for node_id, node in nodes.items():
                if node['parent_id'] and node['parent_id'] in nodes:
                    nodes[node['parent_id']]['children'].append(node_id)
            
            return {
                'tree_id': tree_id,
                'root_id': root_id,
                'nodes': nodes,
                'created_at': tree_info[2],
                'status': tree_info[3],
                'metadata': json.loads(tree_info[4] or '{}')
            }
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """获取单个节点信息"""
        with sqlite3.connect(self.db_path) as conn:
            node_data = conn.execute('''
                SELECT node_id, tree_id, parent_id, prompt, image_path, image_data,
                       keywords, quality_score, accuracy_score, status, branch_info
                FROM nodes WHERE node_id = ?
            ''', (node_id,)).fetchone()
            
            if not node_data:
                return None
            
            node_id, tree_id, parent_id, prompt, image_path, image_data, \
            keywords_json, quality_score, accuracy_score, status, branch_info_json = node_data
            
            return {
                'node_id': node_id,
                'tree_id': tree_id,
                'parent_id': parent_id,
                'prompt': prompt,
                'image_path': image_path,
                'image_data': image_data,
                'keywords': json.loads(keywords_json) if keywords_json else [],
                'quality_score': quality_score or 0.0,
                'accuracy_score': accuracy_score or 0.0,
                'status': status,
                'branch_info': json.loads(branch_info_json) if branch_info_json else {}
            }
    
    def create_task(self, tree_id: str, task_type: str, node_id: str = None) -> str:
        """创建生成任务"""
        task_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO generation_tasks (task_id, tree_id, node_id, task_type)
                VALUES (?, ?, ?, ?)
            ''', (task_id, tree_id, node_id, task_type))
            conn.commit()
        
        return task_id
    
    def update_task(self, task_id: str, status: str, result: Any = None, error: str = None):
        """更新任务状态"""
        with sqlite3.connect(self.db_path) as conn:
            if status == 'completed':
                conn.execute('''
                    UPDATE generation_tasks 
                    SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                ''', (status, json.dumps(result) if result else None, task_id))
            else:
                conn.execute('''
                    UPDATE generation_tasks 
                    SET status = ?, error_message = ?
                    WHERE task_id = ?
                ''', (status, error, task_id))
            conn.commit()
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        with sqlite3.connect(self.db_path) as conn:
            task_data = conn.execute('''
                SELECT task_id, tree_id, node_id, task_type, status, result, error_message
                FROM generation_tasks WHERE task_id = ?
            ''', (task_id,)).fetchone()
            
            if not task_data:
                return None
            
            return {
                'task_id': task_data[0],
                'tree_id': task_data[1],
                'node_id': task_data[2],
                'task_type': task_data[3],
                'status': task_data[4],
                'result': json.loads(task_data[5]) if task_data[5] else None,
                'error': task_data[6]
            }
    
    def cache_keywords(self, prompt: str, keywords: List[Dict]):
        """缓存关键词提取结果"""
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            # 检查是否已存在
            existing = conn.execute('''
                SELECT usage_count FROM keyword_cache WHERE prompt_hash = ?
            ''', (prompt_hash,)).fetchone()
            
            if existing:
                # 更新使用次数
                conn.execute('''
                    UPDATE keyword_cache SET usage_count = usage_count + 1
                    WHERE prompt_hash = ?
                ''', (prompt_hash,))
            else:
                # 插入新记录
                conn.execute('''
                    INSERT INTO keyword_cache (prompt_hash, prompt, keywords)
                    VALUES (?, ?, ?)
                ''', (prompt_hash, prompt, json.dumps(keywords)))
            
            conn.commit()
    
    def get_cached_keywords(self, prompt: str) -> Optional[List[Dict]]:
        """获取缓存的关键词"""
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute('''
                SELECT keywords FROM keyword_cache WHERE prompt_hash = ?
            ''', (prompt_hash,)).fetchone()
            
            if result:
                return json.loads(result[0])
            return None
    
    def get_recent_trees(self, limit: int = 10) -> List[Dict]:
        """获取最近的生成树"""
        with sqlite3.connect(self.db_path) as conn:
            trees_data = conn.execute('''
                SELECT tree_id, root_prompt, created_at, status
                FROM trees 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,)).fetchall()
            
            return [
                {
                    'tree_id': row[0],
                    'root_prompt': row[1],
                    'created_at': row[2],
                    'status': row[3]
                }
                for row in trees_data
            ]
    
    def delete_tree(self, tree_id: str) -> bool:
        """删除生成树及其所有相关数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取所有节点的图像路径，用于删除文件
                image_paths = conn.execute('''
                    SELECT image_path FROM nodes 
                    WHERE tree_id = ? AND image_path IS NOT NULL
                ''', (tree_id,)).fetchall()
                
                # 删除相关的任务记录
                conn.execute('''
                    DELETE FROM generation_tasks WHERE tree_id = ?
                ''', (tree_id,))
                
                # 删除所有节点
                conn.execute('''
                    DELETE FROM nodes WHERE tree_id = ?
                ''', (tree_id,))
                
                # 删除树记录
                conn.execute('''
                    DELETE FROM trees WHERE tree_id = ?
                ''', (tree_id,))
                
                conn.commit()
                
                # 删除图像文件
                deleted_files = 0
                for (image_path,) in image_paths:
                    try:
                        if image_path and Path(image_path).exists():
                            Path(image_path).unlink()
                            deleted_files += 1
                    except Exception as e:
                        logger.warning(f"删除图像文件失败 {image_path}: {e}")
                
                # 尝试删除树的专用文件夹
                try:
                    tree_folder = Path("web_generated_images") / f"tree_{tree_id}"
                    if tree_folder.exists():
                        import shutil
                        shutil.rmtree(tree_folder)
                        logger.info(f"已删除树文件夹: {tree_folder}")
                except Exception as e:
                    logger.warning(f"删除树文件夹失败: {e}")
                
                logger.info(f"成功删除树 {tree_id}，删除了 {deleted_files} 个图像文件")
                return True
                
        except Exception as e:
            logger.error(f"删除树失败 {tree_id}: {e}")
            return False
    
    def save_user_setting(self, key: str, value: Any):
        """保存用户设置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_settings (setting_key, setting_value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, json.dumps(value)))
                conn.commit()
                logger.info(f"用户设置已保存: {key}")
        except Exception as e:
            logger.error(f"保存用户设置失败 {key}: {e}")
    
    def get_user_setting(self, key: str, default_value: Any = None) -> Any:
        """获取用户设置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute('''
                    SELECT setting_value FROM user_settings WHERE setting_key = ?
                ''', (key,)).fetchone()
                
                if result:
                    return json.loads(result[0])
                return default_value
        except Exception as e:
            logger.error(f"获取用户设置失败 {key}: {e}")
            return default_value
    
    def get_all_user_settings(self) -> Dict[str, Any]:
        """获取所有用户设置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                results = conn.execute('''
                    SELECT setting_key, setting_value FROM user_settings
                ''').fetchall()
                
                settings = {}
                for key, value in results:
                    try:
                        settings[key] = json.loads(value)
                    except json.JSONDecodeError:
                        logger.warning(f"设置值解析失败: {key}")
                        continue
                
                return settings
        except Exception as e:
            logger.error(f"获取所有用户设置失败: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        with sqlite3.connect(self.db_path) as conn:
            # 清理旧的已完成任务
            conn.execute('''
                DELETE FROM generation_tasks 
                WHERE status = 'completed' 
                AND datetime(completed_at) < datetime('now', '-{} days')
            '''.format(days))
            
            # 清理低使用频率的关键词缓存
            conn.execute('''
                DELETE FROM keyword_cache 
                WHERE usage_count = 1 
                AND datetime(created_at) < datetime('now', '-{} days')
            '''.format(days))
            
            conn.commit()

# 全局数据库实例
db = TreeDatabase()