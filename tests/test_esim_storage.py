import os
import sqlite3
import tempfile
import unittest

from esim_storage import eSIMStorage


class ESIMStorageBulkTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)
        self.storage = eSIMStorage(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_bulk_add_persists_entries_with_iccid(self):
        entries = [
            {
                "sm_dp_address": "rsp.esim.exchange",
                "activation_code": "CODE-1",
                "iccid": "1111",
                "lpa_string": "LPA:1$rsp.esim.exchange$CODE-1",
            },
            {
                "sm_dp_address": "rsp.esim.exchange",
                "activation_code": "CODE-2",
                "iccid": "2222",
                "lpa_string": "LPA:1$rsp.esim.exchange$CODE-2",
            },
        ]

        added_ids = self.storage.add_esims_bulk(entries)

        self.assertEqual(len(added_ids), 2)

        available = self.storage.get_available_esims()
        self.assertEqual(len(available), 2)
        iccids = {e.iccid for e in available}
        self.assertEqual(iccids, {"1111", "2222"})

        stats = self.storage.get_storage_stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["available"], 2)

    def test_add_esim_from_lpa_stores_iccid(self):
        esim_id = self.storage.add_esim_from_lpa(
            "LPA:1$rsp.truphone.com$CODE123",
            description="test",
            iccid="9999",
        )

        entry = self.storage.get_esim_by_id(esim_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.iccid, "9999")
        self.assertEqual(entry.activation_code, "CODE123")


class ESIMStorageMigrationTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_legacy_db(self):
        """Tạo database theo schema cũ (chưa có cột iccid)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE esim_entries (
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
            """
        )
        cursor.execute(
            """
            INSERT INTO esim_entries
            (id, sm_dp_address, activation_code, description, added_date, status, lpa_string)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy01",
                "rsp.truphone.com",
                "OLDCODE",
                "legacy",
                "2024-01-01T00:00:00",
                "available",
                "LPA:1$rsp.truphone.com$OLDCODE",
            ),
        )
        conn.commit()
        conn.close()

    def test_migration_adds_iccid_column_and_preserves_data(self):
        self._create_legacy_db()

        storage = eSIMStorage(db_path=self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(esim_entries)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        self.assertIn("iccid", columns)

        entry = storage.get_esim_by_id("legacy01")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.activation_code, "OLDCODE")
        self.assertIsNone(entry.iccid)

        new_id = storage.add_esim_from_lpa(
            "LPA:1$rsp.esim.exchange$NEWCODE",
            iccid="5555",
        )
        new_entry = storage.get_esim_by_id(new_id)
        self.assertEqual(new_entry.iccid, "5555")


if __name__ == "__main__":
    unittest.main()
