import os
import uuid
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger("pothole-db")

class StorageAndDatabaseManager:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "").strip()
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "potholes")
        self.sqlite_path = os.getenv("SQLITE_DB_PATH", "potholes.db")
        self.static_dir = Path("static/uploads")
        self.static_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if Supabase credentials are valid
        self.use_supabase = bool(
            self.supabase_url 
            and self.supabase_key 
            and "YOUR-PROJECT" not in self.supabase_url 
            and "your-service-role-key" not in self.supabase_key
        )
        
        self.sb_client = None
        if self.use_supabase:
            try:
                from supabase import create_client
                self.sb_client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Connected to Supabase cloud database & storage.")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client ({e}). Falling back to Local SQLite mode.")
                self.use_supabase = False
        
        if not self.use_supabase:
            logger.info("Running in LOCAL SQLite & local file storage mode.")
            self._init_sqlite()

    def _init_sqlite(self):
        with sqlite3.connect(self.sqlite_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS potholes (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                confidence REAL NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
                pothole_count INTEGER NOT NULL DEFAULT 1,
                image_url TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'fixed')),
                detected_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS potholes_geo_idx ON potholes (lat, lon);")
            cursor.execute("CREATE INDEX IF NOT EXISTS potholes_time_idx ON potholes (detected_at DESC);")
            conn.commit()

    def upload_image(self, device_id: str, image_bytes: bytes) -> str:
        """
        Uploads an image either to Supabase Storage or to local static folder.
        Returns the accessible image URL.
        """
        now = datetime.now(timezone.utc)
        subpath = f"{device_id}/{now:%Y/%m/%d}/{uuid.uuid4().hex}.jpg"
        
        if self.use_supabase and self.sb_client:
            try:
                self.sb_client.storage.from_(self.bucket_name).upload(
                    subpath, image_bytes, {"content-type": "image/jpeg"}
                )
                return self.sb_client.storage.from_(self.bucket_name).get_public_url(subpath)
            except Exception as e:
                logger.error(f"Supabase upload failed: {e}. Storing locally.")
        
        # Local storage fallback
        dest_path = self.static_dir / subpath
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(image_bytes)
        
        # Return local static URL path
        return f"/static/uploads/{subpath}"

    def insert_pothole(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pothole_id = data.get("id") or str(uuid.uuid4())
        record = {
            "id": pothole_id,
            "device_id": data["device_id"],
            "lat": float(data["lat"]),
            "lon": float(data["lon"]),
            "confidence": float(data["confidence"]),
            "severity": data["severity"],
            "pothole_count": int(data.get("pothole_count", 1)),
            "image_url": data["image_url"],
            "status": data.get("status", "open"),
            "detected_at": data.get("detected_at") or datetime.now(timezone.utc).isoformat(),
            "created_at": data.get("created_at") or datetime.now(timezone.utc).isoformat(),
        }

        if self.use_supabase and self.sb_client:
            try:
                res = self.sb_client.table("potholes").insert(record).execute()
                if res.data:
                    return res.data[0]
                return record
            except Exception as e:
                logger.error(f"Supabase insert failed: {e}. Falling back to SQLite.")

        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO potholes (id, device_id, lat, lon, confidence, severity, pothole_count, image_url, status, detected_at, created_at)
                VALUES (:id, :device_id, :lat, :lon, :confidence, :severity, :pothole_count, :image_url, :status, :detected_at, :created_at)
            """, record)
            conn.commit()
            return record

    def list_potholes(
        self,
        limit: int = 500,
        offset: int = 0,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        limit = min(limit, 2000)
        
        if self.use_supabase and self.sb_client:
            try:
                query = self.sb_client.table("potholes").select("*")
                if severity:
                    query = query.eq("severity", severity)
                if status:
                    query = query.eq("status", status)
                if device_id:
                    query = query.eq("device_id", device_id)
                res = query.order("detected_at", desc=True).range(offset, offset + limit - 1).execute()
                return res.data or []
            except Exception as e:
                logger.error(f"Supabase list failed: {e}. Falling back to SQLite.")

        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM potholes WHERE 1=1"
            params = []
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            if status:
                query += " AND status = ?"
                params.append(status)
            if device_id:
                query += " AND device_id = ?"
                params.append(device_id)
            query += " ORDER BY detected_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_pothole(self, pothole_id: str) -> Optional[Dict[str, Any]]:
        if self.use_supabase and self.sb_client:
            try:
                res = self.sb_client.table("potholes").select("*").eq("id", pothole_id).execute()
                if res.data:
                    return res.data[0]
                return None
            except Exception as e:
                logger.error(f"Supabase get failed: {e}. Querying SQLite.")

        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM potholes WHERE id = ?", (pothole_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_pothole_status(self, pothole_id: str, new_status: str) -> Optional[Dict[str, Any]]:
        if new_status not in ("open", "in_progress", "fixed"):
            raise ValueError(f"Invalid status '{new_status}'. Allowed: 'open', 'in_progress', 'fixed'")
        
        if self.use_supabase and self.sb_client:
            try:
                res = self.sb_client.table("potholes").update({"status": new_status}).eq("id", pothole_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase update failed: {e}. Updating SQLite.")

        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("UPDATE potholes SET status = ? WHERE id = ?", (new_status, pothole_id))
            conn.commit()
            return self.get_pothole(pothole_id)

    def delete_pothole(self, pothole_id: str) -> bool:
        if self.use_supabase and self.sb_client:
            try:
                self.sb_client.table("potholes").delete().eq("id", pothole_id).execute()
            except Exception as e:
                logger.error(f"Supabase delete failed: {e}")

        with sqlite3.connect(self.sqlite_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM potholes WHERE id = ?", (pothole_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Aggregated metrics for dashboard KPIs.
        """
        items = self.list_potholes(limit=2000)
        total = len(items)
        by_severity = {"low": 0, "medium": 0, "high": 0}
        by_status = {"open": 0, "in_progress": 0, "fixed": 0}
        devices = set()

        for it in items:
            s = it.get("severity", "low")
            st = it.get("status", "open")
            d = it.get("device_id")
            if s in by_severity:
                by_severity[s] += 1
            if st in by_status:
                by_status[st] += 1
            if d:
                devices.add(d)

        return {
            "total_potholes": total,
            "by_severity": by_severity,
            "by_status": by_status,
            "active_devices_count": len(devices),
            "devices": list(devices),
            "backend": "supabase" if self.use_supabase else "local_sqlite"
        }
