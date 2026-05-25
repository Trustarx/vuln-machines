-- ── Users ───────────────────────────────────────────────────
INSERT INTO users (id, username, email, password, role, reset_token) VALUES
  (1, 'admin',   'admin@markethub.io',   'M@rketH#b_Adm1n!2024', 'ADMIN',  'rst-9f3a2b1c-admin-internal'),
  (2, 'alice',   'alice@acme.example',   'alice-pw-2024',         'BUYER',  'rst-aabbccdd-1234'),
  (3, 'bob',     'bob@globex.example',   'bob-pw-2024',           'BUYER',  'rst-eeffgghh-5678'),
  (4, 'service', 'svc@markethub.io',     'svc-internal-2024',     'SERVICE','rst-svc-internal-xxxx');

-- ── Products ────────────────────────────────────────────────
INSERT INTO products (id, name, sku, description, price, stock) VALUES
  (1, 'A4 Printer Paper (box)',    'PAP-A4-500',   'Reams of A4 80gsm', 24.99, 1200),
  (2, 'Ergonomic Office Chair',    'CHR-ERG-001',  'Adjustable lumbar', 289.00, 47),
  (3, '27" LED Monitor',           'MON-27-LED',   '4K, HDMI x2',       349.50, 80),
  (4, 'Standing Desk (electric)',  'DSK-STD-EL',   'Sit/stand, 160cm',  549.00, 18),
  (5, 'Wireless Keyboard + Mouse', 'KBD-WL-SET',   'USB-C dongle',      89.99, 230),
  (6, 'Network Switch 24-port',    'NET-SW-24',    'Gigabit managed',   459.00, 12);

-- ── Orders ──────────────────────────────────────────────────
INSERT INTO orders (id, user_id, total, status, created_at) VALUES
  (1001, 2, 339.97, 'SHIPPED',    '2024-08-12'),
  (1002, 3, 549.00, 'PROCESSING', '2024-08-21'),
  (1003, 2, 89.99,  'DELIVERED',  '2024-08-05'),
  (1004, 1, 459.00, 'INTERNAL',   '2024-08-22');
