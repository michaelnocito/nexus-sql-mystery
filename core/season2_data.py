# core/season2_data.py
# Season 2 seed data — "The Ghost in the Machine"
#
# Adds three new tables to world.db:
#   server_logs       — access logs including phantom 3:03am entries
#   deleted_records   — audit trail of deleted rows (one keeps coming back)
#   backup_snapshots  — backup tape checksums showing discrepancies
#
# Called during Season 2 initialization. Does NOT modify Season 1 tables.


def seed_season2(conn):
    """
    Add Season 2 tables and data to the world database.
    Safe to call multiple times — skips if tables already exist.

    Args:
        conn: sqlite3.Connection to world.db
    """
    c = conn.cursor()

    # Guard: skip if already seeded
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='server_logs'")
    if c.fetchone():
        return

    conn.executescript("""

    -- ── SERVER LOGS ────────────────────────────────────────────────────
    -- Access and activity logs. Most are normal daytime entries.
    -- The 3:03am phantom entries have user='[SYSTEM]' and status='ANOMALY'.
    -- The action fields of phantom entries encode a hidden message
    -- when you take the first letter of each, ordered by timestamp.

    CREATE TABLE server_logs (
        id          INTEGER PRIMARY KEY,
        timestamp   TEXT    NOT NULL,
        user        TEXT,
        action      TEXT,
        ip_address  TEXT,
        status      TEXT    DEFAULT 'OK'
    );

    INSERT INTO server_logs VALUES
      -- Normal daytime activity
      (1,  '2024-03-01 09:15:00', 'a.chen',    'Login to analytics dashboard',             '10.0.1.42',  'OK'),
      (2,  '2024-03-01 09:22:00', 'd.reeves',  'Query employees table',                    '10.0.1.43',  'OK'),
      (3,  '2024-03-01 10:05:00', 'a.chen',    'Export report to CSV',                      '10.0.1.42',  'OK'),
      (4,  '2024-03-01 14:30:00', 's.ortega',  'Update department budget',                  '10.0.1.44',  'OK'),
      (5,  '2024-03-01 16:45:00', 'p.nair',    'Run quarterly audit script',                '10.0.1.50',  'OK'),

      -- Phantom entry #1
      (6,  '2024-03-02 03:03:00', '[SYSTEM]',  'Checking access log integrity',             '10.0.0.1',   'ANOMALY'),

      -- Normal
      (7,  '2024-03-02 08:30:00', 'j.lee',     'Login to finance portal',                   '10.0.1.51',  'OK'),
      (8,  '2024-03-02 11:00:00', 'a.chen',    'Query transactions WHERE vendor_id = 4',    '10.0.1.42',  'OK'),
      (9,  '2024-03-02 15:20:00', 'v.cole',    'Update employee status',                    '10.0.1.60',  'OK'),

      -- Phantom entry #2
      (10, '2024-03-03 03:03:00', '[SYSTEM]',  'Hashing backup verification tokens',        '10.0.0.1',   'ANOMALY'),

      -- Normal
      (11, '2024-03-03 09:00:00', 'd.reeves',  'Scheduled report generation',               '10.0.1.43',  'OK'),
      (12, '2024-03-03 13:45:00', 'a.chen',    'Join transactions and vendors',              '10.0.1.42',  'OK'),

      -- Phantom entry #3
      (13, '2024-03-04 03:03:00', '[SYSTEM]',  'Evaluating record consistency',              '10.0.0.1',   'ANOMALY'),

      -- Normal
      (14, '2024-03-04 10:10:00', 's.ortega',  'Review analytics pipeline',                 '10.0.1.44',  'OK'),
      (15, '2024-03-04 14:00:00', 'p.nair',    'Approve vendor payment batch',               '10.0.1.50',  'OK'),

      -- Phantom entry #4
      (16, '2024-03-05 03:03:00', '[SYSTEM]',  'Cross-referencing deleted entries',          '10.0.0.1',   'ANOMALY'),

      -- Normal
      (17, '2024-03-05 08:45:00', 'a.chen',    'Login from VPN',                            '10.0.2.10',  'OK'),
      (18, '2024-03-05 12:30:00', 'j.lee',     'Run payroll validation',                     '10.0.1.51',  'OK'),

      -- Phantom entry #5
      (19, '2024-03-06 03:03:00', '[SYSTEM]',  'Kernel-level audit scan',                   '10.0.0.1',   'ANOMALY'),

      -- Normal
      (20, '2024-03-06 09:30:00', 'd.reeves',  'Query vendor spend totals',                 '10.0.1.43',  'OK'),
      (21, '2024-03-06 16:00:00', 'v.cole',    'Archive terminated employee files',          '10.0.1.60',  'OK'),

      -- Phantom entry #6
      (22, '2024-03-07 03:03:00', '[SYSTEM]',  'Testing recovery procedures',               '10.0.0.1',   'ANOMALY'),

      -- Normal
      (23, '2024-03-07 10:20:00', 'a.chen',    'Export anomaly report',                      '10.0.1.42',  'OK'),

      -- Phantom entry #7
      (24, '2024-03-08 03:03:00', '[SYSTEM]',  'Heuristic pattern analysis',                '10.0.0.1',   'ANOMALY'),

      -- Normal
      (25, '2024-03-08 09:00:00', 's.ortega',  'Team standup data review',                  '10.0.1.44',  'OK'),
      (26, '2024-03-08 14:15:00', 'p.nair',    'Reconcile Q1 accounts',                      '10.0.1.50',  'OK'),

      -- Phantom entry #8
      (27, '2024-03-09 03:03:00', '[SYSTEM]',  'Examining deleted user accounts',           '10.0.0.1',   'ANOMALY'),

      -- Normal
      (28, '2024-03-09 11:30:00', 'a.chen',    'Query deleted_records table',                '10.0.1.42',  'OK'),

      -- Phantom entry #9
      (29, '2024-03-10 03:03:00', '[SYSTEM]',  'Data integrity verification',               '10.0.0.1',   'ANOMALY'),

      -- Phantom entry #10
      (30, '2024-03-11 03:03:00', '[SYSTEM]',  'Auditing transaction approval chain',       '10.0.0.1',   'ANOMALY'),

      -- Normal
      (31, '2024-03-11 09:45:00', 'd.reeves',  'Weekly analytics sync',                     '10.0.1.43',  'OK'),

      -- Phantom entry #11
      (32, '2024-03-12 03:03:00', '[SYSTEM]',  'Tracing unauthorized modifications',        '10.0.0.1',   'ANOMALY'),

      -- Phantom entry #12
      (33, '2024-03-13 03:03:00', '[SYSTEM]',  'Analyzing vendor payment flows',             '10.0.0.1',   'ANOMALY'),

      -- Normal
      (34, '2024-03-13 10:00:00', 'a.chen',    'Login — investigating server logs',          '10.0.1.42',  'OK'),
      (35, '2024-03-13 16:30:00', 'j.lee',     'End of day finance close',                   '10.0.1.51',  'OK'),

      -- Phantom entry #13
      (36, '2024-03-14 03:03:00', '[SYSTEM]',  'Locating hidden configuration scripts',     '10.0.0.1',   'ANOMALY'),

      -- Phantom entry #14
      (37, '2024-03-15 03:03:00', '[SYSTEM]',  'Executing scheduled recovery task',         '10.0.0.1',   'ANOMALY');


    -- ── DELETED RECORDS ────────────────────────────────────────────────
    -- Audit trail of deleted rows. record_data is JSON of the original row.
    -- Employee #11 (Elena Gutierrez) keeps getting restored by the phantom script.

    CREATE TABLE deleted_records (
        id              INTEGER PRIMARY KEY,
        original_table  TEXT    NOT NULL,
        record_data     TEXT    NOT NULL,
        deleted_by      TEXT,
        deleted_at      TEXT,
        restored_count  INTEGER DEFAULT 0
    );

    INSERT INTO deleted_records VALUES
      (1, 'employees',
       '{"id": 11, "name": "Elena Gutierrez", "email": "e.gutierrez@nexus.co", "department": "IT", "title": "Senior DBA", "salary": 155000, "manager_id": 7, "hire_date": "2018-04-15", "status": "terminated"}',
       'v.cole', '2024-01-15 09:30:00', 47),

      (2, 'vendors',
       '{"id": 9, "name": "Nightingale Analytics", "category": "Consulting", "contact": "info@nightingale-analytics.com", "address": "unknown", "verified": 0}',
       'm.webb', '2023-12-20 17:45:00', 0),

      (3, 'transactions',
       '{"id": 29, "date": "2024-01-02", "vendor_id": 9, "amount": 340000, "category": "Consulting", "approved_by": 4, "department": "Special Projects", "description": "Year-end special engagement"}',
       'm.webb', '2023-12-28 23:15:00', 0);


    -- ── BACKUP SNAPSHOTS ──────────────────────────────────────────────
    -- Row counts and checksums from backup tapes at different dates.
    -- The checksums for employees and transactions don't match between
    -- the pre-termination and post-termination snapshots — proving tampering.

    CREATE TABLE backup_snapshots (
        id              INTEGER PRIMARY KEY,
        snapshot_date   TEXT    NOT NULL,
        table_name      TEXT    NOT NULL,
        row_count       INTEGER,
        checksum        TEXT
    );

    INSERT INTO backup_snapshots VALUES
      -- January 1st snapshot (before Elena was fired)
      (1,  '2024-01-01', 'employees',    11,  'a3f2c8d1e5b7'),
      (2,  '2024-01-01', 'vendors',       9,  'b7e4f1a9c3d6'),
      (3,  '2024-01-01', 'transactions', 29,  'c1d5e8f2a6b3'),

      -- March 1st snapshot (after Elena was fired, data tampered)
      (4,  '2024-03-01', 'employees',    10,  'f9a1b4c7d2e8'),
      (5,  '2024-03-01', 'vendors',       8,  'e3c6a9f1b5d7'),
      (6,  '2024-03-01', 'transactions', 28,  'd8f2b5e1a4c9'),

      -- June 1st snapshot (current — should match March, but doesn't)
      (7,  '2024-06-01', 'employees',    10,  'f9a1b4c7d2e8'),
      (8,  '2024-06-01', 'vendors',       8,  'e3c6a9f1b5d7'),
      (9,  '2024-06-01', 'transactions', 28,  'd8f2b5e1a4c9');

    """)
    conn.commit()
