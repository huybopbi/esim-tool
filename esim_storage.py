import json
import os
import sqlite3
import datetime
import uuid
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
    iccid: Optional[str] = None
    used_note: Optional[str] = None

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
                    lpa_string TEXT,
                    iccid TEXT,
                    used_note TEXT
                )
            ''')
            
            # Migration: thêm cột mới cho database cũ chưa có
            cursor.execute("PRAGMA table_info(esim_entries)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            if 'iccid' not in existing_columns:
                cursor.execute('ALTER TABLE esim_entries ADD COLUMN iccid TEXT')
                logger.info("Migrated esim_entries: added iccid column")
            if 'used_note' not in existing_columns:
                cursor.execute('ALTER TABLE esim_entries ADD COLUMN used_note TEXT')
                logger.info("Migrated esim_entries: added used_note column")
            
            # Tạo index cho tìm kiếm nhanh
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON esim_entries(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_added_date ON esim_entries(added_date)')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_esim(self, sm_dp_address: str, activation_code: str = "", description: str = "", iccid: str = "") -> str:
        """Thêm eSIM mới vào kho"""
        try:
            # Tạo LPA string
            if activation_code and activation_code.strip():
                lpa_string = f"LPA:1${sm_dp_address}${activation_code}"
            else:
                lpa_string = f"LPA:1${sm_dp_address}$"
            
            # Tạo ID duy nhất
            esim_id = str(uuid.uuid4())[:8]
            
            # Tạo entry
            entry = eSIMEntry(
                id=esim_id,
                sm_dp_address=sm_dp_address,
                activation_code=activation_code,
                description=description,
                added_date=datetime.datetime.now().isoformat(),
                status='available',
                lpa_string=lpa_string,
                iccid=iccid
            )
            
            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO esim_entries 
                (id, sm_dp_address, activation_code, description, added_date, status, lpa_string, iccid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.id, entry.sm_dp_address, entry.activation_code,
                entry.description, entry.added_date, entry.status, entry.lpa_string, entry.iccid
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added eSIM {esim_id} to storage")
            return esim_id
            
        except Exception as e:
            logger.error(f"Error adding eSIM: {e}")
            raise
    
    def add_esim_from_lpa(self, lpa_string: str, description: str = "", iccid: str = "") -> str:
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
            esim_id = str(uuid.uuid4())[:8]
            
            # Tạo entry
            entry = eSIMEntry(
                id=esim_id,
                sm_dp_address=analysis['sm_dp_address'],
                activation_code=analysis['activation_code'] or "",
                description=description,
                added_date=datetime.datetime.now().isoformat(),
                status='available',
                lpa_string=lpa_string.strip(),
                iccid=iccid
            )
            
            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO esim_entries 
                (id, sm_dp_address, activation_code, description, added_date, status, lpa_string, iccid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.id, entry.sm_dp_address, entry.activation_code,
                entry.description, entry.added_date, entry.status, entry.lpa_string, entry.iccid
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added eSIM {esim_id} from LPA string to storage")
            return esim_id
            
        except Exception as e:
            logger.error(f"Error adding eSIM from LPA: {e}")
            raise

    def add_esims_bulk(self, entries: List[Dict]) -> List[str]:
        """Thêm nhiều eSIM cùng lúc trong một transaction.

        Mỗi entry là dict gồm ``lpa_string`` (bắt buộc), ``sm_dp_address``,
        ``activation_code``, ``iccid``, ``description`` (tùy chọn).
        Trả về danh sách ID đã thêm thành công.
        """
        added_ids: List[str] = []

        if not entries:
            return added_ids

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.datetime.now().isoformat()
            for entry in entries:
                esim_id = str(uuid.uuid4())[:8]
                cursor.execute('''
                    INSERT INTO esim_entries 
                    (id, sm_dp_address, activation_code, description, added_date, status, lpa_string, iccid)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    esim_id,
                    entry.get('sm_dp_address', ''),
                    entry.get('activation_code', ''),
                    entry.get('description', ''),
                    now,
                    'available',
                    entry['lpa_string'],
                    entry.get('iccid', ''),
                ))
                added_ids.append(esim_id)

            conn.commit()
            conn.close()

            logger.info(f"Bulk added {len(added_ids)} eSIMs to storage")
            return added_ids

        except Exception as e:
            logger.error(f"Error bulk adding eSIMs: {e}")
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
                    'lpa_string': row[8],
                    'iccid': row[9] if len(row) > 9 else None,
                    'used_note': row[10] if len(row) > 10 else None
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
                    'lpa_string': row[8],
                    'iccid': row[9] if len(row) > 9 else None,
                    'used_note': row[10] if len(row) > 10 else None
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
                    'lpa_string': row[8],
                    'iccid': row[9] if len(row) > 9 else None,
                    'used_note': row[10] if len(row) > 10 else None
                }
                return eSIMEntry.from_dict(entry_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting eSIM by ID: {e}")
            return None
    
    def mark_esim_used(self, esim_id: str, used_by: str, used_note: str = "") -> bool:
        """Đánh dấu eSIM là đã sử dụng, kèm ghi chú (cài cho ai)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE esim_entries 
                SET status = 'used', used_date = ?, used_by = ?, used_note = ?
                WHERE id = ? AND status = 'available'
            ''', (datetime.datetime.now().isoformat(), used_by, used_note, esim_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                logger.info(f"Marked eSIM {esim_id} as used by {used_by} | note: {used_note or 'N/A'}")
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
    
    def get_all_esims(self) -> List[eSIMEntry]:
        """Lấy toàn bộ eSIM (cả còn trống và đã dùng), mới nhất trước."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM esim_entries ORDER BY added_date DESC')
            rows = cursor.fetchall()
            conn.close()

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
                    'lpa_string': row[8],
                    'iccid': row[9] if len(row) > 9 else None,
                    'used_note': row[10] if len(row) > 10 else None
                }
                entries.append(eSIMEntry.from_dict(entry_dict))

            return entries

        except Exception as e:
            logger.error(f"Error getting all eSIMs: {e}")
            return []

    def delete_used_esims(self) -> int:
        """Xóa toàn bộ eSIM đã dùng. Trả về số bản ghi đã xóa."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM esim_entries WHERE status = 'used'")
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Deleted {rows_affected} used eSIMs")
            return rows_affected

        except Exception as e:
            logger.error(f"Error deleting used eSIMs: {e}")
            return 0

    def delete_all_esims(self) -> int:
        """Xóa toàn bộ eSIM trong kho. Trả về số bản ghi đã xóa."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM esim_entries")
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Deleted ALL {rows_affected} eSIMs from storage")
            return rows_affected

        except Exception as e:
            logger.error(f"Error deleting all eSIMs: {e}")
            return 0

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
