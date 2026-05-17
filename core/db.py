# core/db.py
# DatabaseInterface — the player's primary tool.
# db.query("SELECT ...") runs real SQL against the game world.
# The world.db IS the mystery: seed data tells the story through patterns.

import sqlite3
import os
import textwrap

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'world.db')


# ── Query result ─────────────────────────────────────────────────────────────

class QueryResult:
    """Returned by db.query(). Behaves a bit like a tiny pandas DataFrame."""

    def __init__(self, rows, columns, sql=""):
        self.rows    = list(rows)
        self.columns = list(columns)
        self.sql     = sql

    # ── pandas-like helpers ───────────────────────────────────────────────────

    def head(self, n=5):
        return QueryResult(self.rows[:n], self.columns, self.sql)

    def tail(self, n=5):
        return QueryResult(self.rows[-n:], self.columns, self.sql)

    def __len__(self):
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    # ── display ───────────────────────────────────────────────────────────────

    def __repr__(self):
        if not self.rows:
            return "(no rows returned)"

        total_width = sum(len(c) for c in self.columns) + 3 * len(self.columns)
        for row in self.rows:
            row_w = sum(len(str(v)) for v in row) + 3 * len(row)
            total_width = max(total_width, row_w)

        # Wide tables (many columns) → vertical card format, much more readable
        if len(self.columns) > 5 or total_width > 90:
            return self._repr_cards()

        # Narrow tables → classic ASCII grid
        return self._repr_grid()

    def _repr_grid(self):
        widths = [len(c) for c in self.columns]
        for row in self.rows:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(str(val)))

        sep   = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        hdr   = "|" + "|".join(f" {c:<{w}} " for c, w in zip(self.columns, widths)) + "|"
        lines = [sep, hdr, sep]
        for row in self.rows:
            lines.append("|" + "|".join(f" {str(v):<{w}} " for v, w in zip(row, widths)) + "|")
        lines.append(sep)
        lines.append(f"  {len(self.rows)} row(s)")
        return "\n".join(lines)

    def _repr_cards(self):
        """Vertical layout — one card per row, key: value format."""
        max_col_w = max(len(c) for c in self.columns)
        lines = []
        for i, row in enumerate(self.rows):
            if i > 0:
                lines.append("")
            lines.append(f"── Row {i + 1} ──")
            for col, val in zip(self.columns, row):
                lines.append(f"  {col:>{max_col_w}} : {val}")
        lines.append(f"\n  {len(self.rows)} row(s)")
        return "\n".join(lines)

    def __str__(self):
        return self.__repr__()


# ── Database interface ────────────────────────────────────────────────────────

class DatabaseInterface:
    """
    The object the player uses in-game.
    Exposed in the exec namespace as `db`.
    """

    def __init__(self, game_state):
        self._game = game_state
        self._conn = None
        self._setup()

    def _connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(DB_PATH)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _setup(self):
        """Create and seed the world database if it doesn't exist."""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = self._connect()
        c    = conn.cursor()

        # Only seed if tables don't exist yet
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        if c.fetchone():
            return

        self._seed(conn)

    def setup_season2(self):
        """Seed Season 2 tables — safe to call multiple times (guards internally)."""
        from core.season2_data import seed_season2
        seed_season2(self._connect())

    def _seed(self, conn):
        conn.executescript("""
        -- ── EMPLOYEES ──────────────────────────────────────────────────────
        CREATE TABLE employees (
            id          INTEGER PRIMARY KEY,
            name        TEXT    NOT NULL,
            email       TEXT,
            department  TEXT,
            title       TEXT,
            salary      REAL,
            manager_id  INTEGER,
            hire_date   TEXT,
            status      TEXT DEFAULT 'active'
        );

        INSERT INTO employees VALUES
          (1,  'Alex Chen',       'a.chen@nexus.co',    'Analytics',        'Junior Analyst',    68000, 3,  '2024-01-08', 'active'),
          (2,  'Diana Reeves',    'd.reeves@nexus.co',  'Analytics',        'Senior Analyst',    95000, 3,  '2021-03-15', 'active'),
          (3,  'Sam Ortega',      's.ortega@nexus.co',  'Analytics',        'Analytics Manager', 118000, 7, '2019-06-01', 'active'),
          (4,  'Marcus Webb',     'm.webb@nexus.co',    'Finance',          'CFO',               310000, 8, '2015-02-28', 'active'),
          (5,  'Priya Nair',      'p.nair@nexus.co',    'Finance',          'Controller',        142000, 4, '2018-09-10', 'active'),
          (6,  'Jordan Lee',      'j.lee@nexus.co',     'Finance',          'Analyst',           78000, 5, '2022-04-20', 'active'),
          (7,  'Rachel Kim',      'r.kim@nexus.co',     'Operations',       'COO',               285000, 8, '2016-07-14', 'active'),
          (8,  'Thomas Harlow',   't.harlow@nexus.co',  'Executive',        'CEO',               450000, NULL,'2012-01-01','active'),
          (9,  'Felix Grant',     'f.grant@nexus.co',   'Special Projects', 'Director',          195000, 4, '2020-11-03', 'active'),
          (10, 'Vanessa Cole',    'v.cole@nexus.co',    'HR',               'HR Director',       135000, 8, '2017-05-22', 'active');

        -- ── DEPARTMENTS ────────────────────────────────────────────────────
        CREATE TABLE departments (
            id      INTEGER PRIMARY KEY,
            name    TEXT,
            budget  REAL,
            head_id INTEGER
        );

        INSERT INTO departments VALUES
          (1, 'Analytics',        850000,  3),
          (2, 'Finance',         1200000,  4),
          (3, 'Operations',      2100000,  7),
          (4, 'HR',               650000, 10),
          (5, 'Executive',        980000,  8),
          (6, 'Special Projects', 4800000, 9);

        -- ── VENDORS ────────────────────────────────────────────────────────
        CREATE TABLE vendors (
            id          INTEGER PRIMARY KEY,
            name        TEXT,
            category    TEXT,
            contact     TEXT,
            address     TEXT,
            verified    INTEGER DEFAULT 1
        );

        INSERT INTO vendors VALUES
          (1,  'CloudScale Inc',       'Software',    'sales@cloudscale.com',   '123 Tech Blvd, Austin TX',   1),
          (2,  'OfficePro Supply',     'Supplies',    'orders@officepro.com',   '45 Commerce St, Dallas TX',  1),
          (3,  'TalentFirst LLC',      'Recruiting',  'hire@talentfirst.com',   '88 Plaza Ave, Chicago IL',   1),
          (4,  'Apex Solutions LLC',   'Consulting',  'info@apex-sol.biz',      '(no address on file)',       0),
          (5,  'DataViz Partners',     'Software',    'hello@dataviz.io',       '500 Main St, Denver CO',     1),
          (6,  'Meridian Consulting',  'Consulting',  'contact@meridian.net',   '77 Harbor Rd, Boston MA',    1),
          (7,  'Pinnacle Strategy',    'Consulting',  'ps@pinnacle-strat.biz',  '(no address on file)',       0),
          (8,  'Nexus Facilities',     'Facilities',  'ops@nexusfacilities.com','900 Park Way, Austin TX',    1);

        -- ── TRANSACTIONS ───────────────────────────────────────────────────
        CREATE TABLE transactions (
            id          INTEGER PRIMARY KEY,
            date        TEXT,
            vendor_id   INTEGER,
            amount      REAL,
            category    TEXT,
            approved_by INTEGER,
            department  TEXT,
            description TEXT
        );

        INSERT INTO transactions VALUES
          -- Normal activity
          (1,  '2023-01-15', 1, 24500,  'Software',    5, 'Analytics',        'Annual CloudScale license'),
          (2,  '2023-01-22', 2, 1240,   'Supplies',    3, 'Analytics',        'Office supplies Q1'),
          (3,  '2023-02-01', 3, 18000,  'Recruiting',  10,'HR',               'Q1 recruiting retainer'),
          (4,  '2023-02-14', 8, 5500,   'Facilities',  7, 'Operations',       'Building maintenance Feb'),
          (5,  '2023-02-28', 5, 9800,   'Software',    3, 'Analytics',        'DataViz annual subscription'),
          -- Suspicious: Apex Solutions
          (6,  '2023-03-03', 4, 87500,  'Consulting',  4, 'Special Projects', 'Strategic consulting Q1'),
          (7,  '2023-03-15', 2, 2100,   'Supplies',    5, 'Finance',          'Finance supplies Q1'),
          (8,  '2023-04-01', 6, 32000,  'Consulting',  7, 'Operations',       'Process optimization'),
          (9,  '2023-04-12', 4, 112000, 'Consulting',  4, 'Special Projects', 'Strategic consulting Q2'),
          (10, '2023-04-30', 8, 5500,   'Facilities',  7, 'Operations',       'Building maintenance Apr'),
          (11, '2023-05-10', 1, 8200,   'Software',    3, 'Analytics',        'CloudScale add-on seats'),
          (12, '2023-05-20', 4, 95000,  'Consulting',  4, 'Special Projects', 'Strategic consulting May'),
          -- Pinnacle Strategy also suspicious
          (13, '2023-06-01', 7, 78000,  'Consulting',  4, 'Special Projects', 'Market analysis project'),
          (14, '2023-06-15', 3, 18000,  'Recruiting',  10,'HR',               'Q2 recruiting retainer'),
          (15, '2023-06-30', 4, 143000, 'Consulting',  4, 'Special Projects', 'Strategic consulting Q2 final'),
          (16, '2023-07-05', 8, 5500,   'Facilities',  7, 'Operations',       'Building maintenance Jul'),
          (17, '2023-07-18', 2, 890,    'Supplies',    3, 'Analytics',        'Printer cartridges'),
          (18, '2023-08-01', 4, 167000, 'Consulting',  4, 'Special Projects', 'Strategic consulting Q3'),
          (19, '2023-08-15', 7, 134000, 'Consulting',  4, 'Special Projects', 'Market analysis phase 2'),
          (20, '2023-09-01', 6, 41000,  'Consulting',  7, 'Operations',       'Supply chain review'),
          (21, '2023-09-12', 4, 198000, 'Consulting',  4, 'Special Projects', 'Strategic consulting Sept'),
          (22, '2023-10-01', 1, 24500,  'Software',    5, 'Analytics',        'Annual CloudScale renewal'),
          (23, '2023-10-15', 4, 211000, 'Consulting',  4, 'Special Projects', 'Strategic consulting Q4'),
          (24, '2023-11-01', 7, 189000, 'Consulting',  4, 'Special Projects', 'Market analysis phase 3'),
          (25, '2023-11-20', 2, 3400,   'Supplies',    5, 'Finance',          'Finance supplies Q4'),
          (26, '2023-12-01', 4, 243000, 'Consulting',  4, 'Special Projects', 'Year-end strategic review'),
          (27, '2023-12-15', 3, 18000,  'Recruiting',  10,'HR',               'Q4 recruiting retainer'),
          (28, '2023-12-29', 7, 212000, 'Consulting',  4, 'Special Projects', 'Year-end market analysis');

        -- ── PLAYER SAVE STATE ──────────────────────────────────────────────
        CREATE TABLE save_state (
            id         INTEGER PRIMARY KEY,
            scene      TEXT    DEFAULT 'your_desk',
            clues      TEXT    DEFAULT '[]',
            objectives TEXT    DEFAULT '[]',
            saved_at   TEXT
        );

        INSERT INTO save_state VALUES (1, 'your_desk', '[]', '[]', datetime('now'));
        """)
        conn.commit()

    # ── Public API (what the player calls) ───────────────────────────────────

    def query(self, sql: str) -> QueryResult:
        """
        Run a SQL query against the Nexus database.
        Returns a QueryResult you can print or inspect.

        Example:
            db.query("SELECT * FROM employees")
            db.query("SELECT name, salary FROM employees WHERE department = 'Finance'")
        """
        try:
            conn = self._connect()
            cur  = conn.execute(sql)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            result = QueryResult(rows, cols, sql)

            # Notify game of query (for objective tracking)
            self._game.on_query(sql, result)
            return result

        except sqlite3.Error as e:
            # Surface the SQLite error as readable feedback
            self._game.on_error(f"SQL error: {e}\n\nCheck your query and try again.")
            return QueryResult([], [], sql)

    def tables(self) -> QueryResult:
        """List all tables in the database."""
        return self.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")

    def schema(self, table: str) -> QueryResult:
        """Show the columns of a table."""
        return self.query(f"PRAGMA table_info({table})")

    def __repr__(self):
        return "<NexusDB — type db.tables() to see what's available>"
