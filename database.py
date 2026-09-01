"""SQLite storage layer for iFood orders."""

import json
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/orders.db")
DATA_DIR = Path("data")
PROFILE_NAMES_FILE = DATA_DIR / "profiles.json"

# Chave do perfil conjunto (leitura combinada de todos os bancos, não um banco
# em si). Não pode colidir com nome de arquivo em data/, daí os underscores.
# Compartilhada entre dashboard.py e run.sh — um só lugar de verdade.
CASAL = "__casal__"

DAY_NAMES = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
MONTH_NAMES = [
    "", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
]


def db_path_for(profile: str) -> Path:
    """Resolve o arquivo de banco para um perfil. 'default' mantém orders.db."""
    if not profile or profile.lower() in ("default", "orders"):
        return DB_PATH
    safe = "".join(c for c in profile if c.isalnum() or c in "-_").lower()
    return DATA_DIR / f"{safe}.db"


def list_profiles() -> list[str]:
    """Lista chaves de perfil existentes a partir dos bancos em data/."""
    if not DATA_DIR.exists():
        return []
    profiles = []
    for db in sorted(DATA_DIR.glob("*.db")):
        profiles.append("default" if db.name == "orders.db" else db.stem)
    return profiles


def _load_names() -> dict:
    if PROFILE_NAMES_FILE.exists():
        try:
            return json.loads(PROFILE_NAMES_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def profile_display_name(key: str) -> str:
    """Nome de exibição de um perfil (alias editável). Cai na própria key."""
    names = _load_names()
    if key in names:
        return names[key]
    return "Você (default)" if key == "default" else key


def set_profile_display_name(key: str, name: str):
    """Define/atualiza o nome de exibição de um perfil sem renomear arquivos."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    names = _load_names()
    name = (name or "").strip()
    if name:
        names[key] = name
    else:
        names.pop(key, None)  # nome vazio → volta ao padrão
    PROFILE_NAMES_FILE.write_text(
        json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class Database:
    def __init__(self, db_path: str = None, profile: str = None):
        if db_path:
            self.db_path = Path(db_path)
        elif profile:
            self.db_path = db_path_for(profile)
        else:
            self.db_path = DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS orders (
                    id              TEXT PRIMARY KEY,
                    restaurant_name TEXT NOT NULL DEFAULT 'Unknown',
                    category        TEXT DEFAULT 'Restaurante',
                    ordered_at      TEXT,
                    status          TEXT DEFAULT 'UNKNOWN',
                    subtotal        REAL DEFAULT 0,
                    delivery_fee    REAL DEFAULT 0,
                    service_fee     REAL DEFAULT 0,
                    coupon_discount REAL DEFAULT 0,
                    total           REAL DEFAULT 0,
                    year            INTEGER,
                    month           INTEGER,
                    day_of_week     INTEGER,
                    hour            INTEGER,
                    time_slot       TEXT,
                    price_range     TEXT,
                    scraped_at      TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS order_items (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id    TEXT NOT NULL,
                    item_name   TEXT NOT NULL,
                    quantity    INTEGER DEFAULT 1,
                    unit_price  REAL DEFAULT 0,
                    subtotal    REAL DEFAULT 0,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_orders_restaurant  ON orders(restaurant_name);
                CREATE INDEX IF NOT EXISTS idx_orders_year        ON orders(year);
                CREATE INDEX IF NOT EXISTS idx_orders_month       ON orders(month);
                CREATE INDEX IF NOT EXISTS idx_orders_dow         ON orders(day_of_week);
                CREATE INDEX IF NOT EXISTS idx_items_order        ON order_items(order_id);
            """)
            # Migração leve: adiciona category em bancos antigos (ANTES do índice)
            cols = {r[1] for r in conn.execute("PRAGMA table_info(orders)")}
            if "category" not in cols:
                conn.execute("ALTER TABLE orders ADD COLUMN category TEXT DEFAULT 'Restaurante'")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_category ON orders(category)")

    def order_exists(self, order_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM orders WHERE id = ?", (order_id,)
            ).fetchone()
            return row is not None

    def save_order(self, order: dict):
        items = order.pop("items", [])
        cols = [
            "id", "restaurant_name", "category", "ordered_at", "status", "subtotal",
            "delivery_fee", "service_fee", "coupon_discount", "total",
            "year", "month", "day_of_week", "hour", "time_slot", "price_range",
        ]
        # Ensure all keys exist with defaults
        for col in cols:
            order.setdefault(col, None)

        with self._conn() as conn:
            conn.execute(
                f"""INSERT OR REPLACE INTO orders ({", ".join(cols)})
                    VALUES ({", ".join(":" + c for c in cols)})""",
                {c: order[c] for c in cols},
            )
            if items:
                conn.execute("DELETE FROM order_items WHERE order_id = ?", (order["id"],))
                conn.executemany(
                    "INSERT INTO order_items (order_id, item_name, quantity, unit_price, subtotal)"
                    " VALUES (?, ?, ?, ?, ?)",
                    [
                        (order["id"], i["name"], i["quantity"], i["unit_price"], i["subtotal"])
                        for i in items
                    ],
                )

    def count_orders(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    # ── DataFrame queries ────────────────────────────────────────────────────

    def get_orders_df(self) -> pd.DataFrame:
        with self._conn() as conn:
            df = pd.read_sql("SELECT * FROM orders ORDER BY ordered_at DESC", conn)
        if not df.empty:
            df["ordered_at"] = pd.to_datetime(df["ordered_at"], errors="coerce")
            df["day_name"] = df["day_of_week"].map(
                lambda x: DAY_NAMES[int(x)] if x is not None and not pd.isna(x) else "?"
            )
            df["month_name"] = df["month"].map(
                lambda x: MONTH_NAMES[int(x)] if x is not None and not pd.isna(x) else "?"
            )
        return df

    def get_items_df(self) -> pd.DataFrame:
        with self._conn() as conn:
            return pd.read_sql(
                """SELECT i.*, o.restaurant_name, o.ordered_at, o.year, o.month
                   FROM order_items i
                   JOIN orders o ON i.order_id = o.id
                   ORDER BY o.ordered_at DESC""",
                conn,
            )
