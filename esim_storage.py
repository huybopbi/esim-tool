import json
import os
import sqlite3
import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class eSIMEntry:
    """Class đại diện cho một eSIM entry"""
    id: str
    sm_dp_address: str
    activation_code: str
    description: str
    added_date: str
    status: str  # 'available', 'used'
    used_date: Optional[str] = None
    used_by: Optional[str] = None
    lpa_string: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'eSIMEntry':
        return cls(**data)

class eSIMStorage:
    """Class quản lý lưu trữ eSIM"""
    
    def __init__(self, db_path: str = "esim_storage.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Khởi tạo database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tạo bảng esim_entries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS esim_entries (
                    id TEXT PRIMARY KEY,
                    sm_dp_address TEXT NOT NULL,
                    activation_code TEXT,
                    description TEXT,
                    added_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'available',
                    used_date TEXT,
                    used_by TEXT,
                    lpa_string TEXT
                )
            ''')
            
            # Tạo index cho tìm kiếm nhanh
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON esim_entries(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_added_date ON esim_entries(added_date)')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_esim(self, sm_dp_address: str, activation_code: str = "", description: str = "") -> str:
        """Thêm eSIM mới vào kho"""
        try:
            # Tạo LPA string
            if activation_code and activation_code.strip():
                lpa_string = f"LPA:1${sm_dp_address}${activation_code}"
            else:
                lpa_string = f"LPA:1${sm_dp_address}$"
            
            # Tạo ID duy nhất
            import uuid
            esim_id = str(uuid.uuid4())[:8]
            
            # Tạo entry
            entry = eSIMEntry(
                id=esim_id,
                sm_dp_address=sm_dp_address,
                activation_code=activation_code,
                description=description,
                added_date=datetime.datetime.now().isoformat(),
                status='available',
                lpa_string=lpa_string
            )
            
            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO esim_entries 
                (id, sm_dp_address, activation_code, description, added_date, status, lpa_string)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.id, entry.sm_dp_address, entry.activation_code,
                entry.description, entry.added_date, entry.status, entry.lpa_string
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added eSIM {esim_id} to storage")
            return esim_id
            
        except Exception as e:
            logger.error(f"Error adding eSIM: {e}")
            raise
    
    def add_esim_from_lpa(self, lpa_string: str, description: str = "") -> str:
        """Thêm eSIM từ LPA string vào kho"""
        try:
            # Import esim_tools để validate và extract thông tin
            from esim_tools import esim_tools
            
            # Validate LPA string
            is_valid, message = esim_tools.validate_lpa_string(lpa_string)
            if not is_valid:
                raise ValueError(f"LPA string không hợp lệ: {message}")
            
            # Extract thông tin từ LPA string
            analysis = esim_tools.extract_sm_dp_and_activation(lpa_string)
            
            if not analysis['sm_dp_address']:
                raise ValueError("Không thể extract SM-DP+ address từ LPA string")
            
            # Tạo ID duy nhất
            import uuid
            esim_id = str(uuid.uuid4())[:8]
            
            # Tạo entry
            entry = eSIMEntry(
                id=esim_id,
                sm_dp_address=analysis['sm_dp_address'],
                activation_code=analysis['activation_code'] or "",
                description=description,
                added_date=datetime.datetime.now().isoformat(),
                status='available',
                lpa_string=lpa_string.strip()
            )
            
            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO esim_entries 
                (id, sm_dp_address, activation_code, description, added_date, status, lpa_string)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.id, entry.sm_dp_address, entry.activation_code,
                entry.description, entry.added_date, entry.status, entry.lpa_string
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added eSIM {esim_id} from LPA string to storage")
            return esim_id
            
        except Exception as e:
            logger.error(f"Error adding eSIM from LPA: {e}")
            raise
    
    def get_available_esims(self) -> List[eSIMEntry]:
        """Lấy danh sách eSIM còn available"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM esim_entries 
                WHERE status = 'available' 
                ORDER BY added_date DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to eSIMEntry objects
            entries = []
            for row in rows:
                entry_dict = {
                    'id': row[0],
                    'sm_dp_address': row[1],
                    'activation_code': row[2],
                    'description': row[3],
                    'added_date': row[4],
                    'status': row[5],
                    'used_date': row[6],
                    'used_by': row[7],
                    'lpa_string': row[8]
                }
                entries.append(eSIMEntry.from_dict(entry_dict))
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting available eSIMs: {e}")
            return []
    
    def get_used_esims(self) -> List[eSIMEntry]:
        """Lấy danh sách eSIM đã sử dụng"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM esim_entries 
                WHERE status = 'used' 
                ORDER BY used_date DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to eSIMEntry objects
            entries = []
            for row in rows:
                entry_dict = {
                    'id': row[0],
                    'sm_dp_address': row[1],
                    'activation_code': row[2],
                    'description': row[3],
                    'added_date': row[4],
                    'status': row[5],
                    'used_date': row[6],
                    'used_by': row[7],
                    'lpa_string': row[8]
                }
                entries.append(eSIMEntry.from_dict(entry_dict))
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting used eSIMs: {e}")
            return []
    
    def get_esim_by_id(self, esim_id: str) -> Optional[eSIMEntry]:
        """Lấy eSIM theo ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM esim_entries WHERE id = ?', (esim_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                entry_dict = {
                    'id': row[0],
                    'sm_dp_address': row[1],
                    'activation_code': row[2],
                    'description': row[3],
                    'added_date': row[4],
                    'status': row[5],
                    'used_date': row[6],
                    'used_by': row[7],
                    'lpa_string': row[8]
                }
                return eSIMEntry.from_dict(entry_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting eSIM by ID: {e}")
            return None
    
    def mark_esim_used(self, esim_id: str, used_by: str) -> bool:
        """Đánh dấu eSIM là đã sử dụng"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE esim_entries 
                SET status = 'used', used_date = ?, used_by = ?
                WHERE id = ? AND status = 'available'
            ''', (datetime.datetime.now().isoformat(), used_by, esim_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                logger.info(f"Marked eSIM {esim_id} as used by {used_by}")
                return True
            else:
                logger.warning(f"Could not mark eSIM {esim_id} as used (not available)")
                return False
            
        except Exception as e:
            logger.error(f"Error marking eSIM as used: {e}")
            return False
    
    def delete_esim(self, esim_id: str) -> bool:
        """Xóa eSIM khỏi kho"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM esim_entries WHERE id = ?', (esim_id,))
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                logger.info(f"Deleted eSIM {esim_id}")
                return True
            else:
                logger.warning(f"Could not delete eSIM {esim_id} (not found)")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting eSIM: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, int]:
        """Lấy thống kê kho eSIM"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Đếm available
            cursor.execute('SELECT COUNT(*) FROM esim_entries WHERE status = "available"')
            available_count = cursor.fetchone()[0]
            
            # Đếm used
            cursor.execute('SELECT COUNT(*) FROM esim_entries WHERE status = "used"')
            used_count = cursor.fetchone()[0]
            
            # Tổng
            total_count = available_count + used_count
            
            conn.close()
            
            return {
                'total': total_count,
                'available': available_count,
                'used': used_count
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {'total': 0, 'available': 0, 'used': 0}

# Khởi tạo storage instance
esim_storage = eSIMStorage()
