CREATE DATABASE IF NOT EXISTS acmecorp;
USE acmecorp;

-- Staff directory (searchable, vulnerable to SQLi)
CREATE TABLE staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(100),
    position VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    ext VARCHAR(10)
);

INSERT INTO staff VALUES
(1, 'James Harrington', 'Engineering',       'Senior Developer',      'j.harrington@acmecorp.local', '555-0101', '101'),
(2, 'Maria Santos',     'Human Resources',   'HR Manager',            'm.santos@acmecorp.local',     '555-0102', '102'),
(3, 'David Park',       'Finance',           'Finance Analyst',       'd.park@acmecorp.local',       '555-0103', '103'),
(4, 'Linda Chen',       'Engineering',       'DevOps Engineer',       'l.chen@acmecorp.local',       '555-0104', '104'),
(5, 'Robert Mills',     'Sales',             'Account Manager',       'r.mills@acmecorp.local',      '555-0105', '105'),
(6, 'Sarah Thompson',   'IT',                'Systems Administrator', 's.thompson@acmecorp.local',   '555-0106', '106'),
(7, 'Ahmed Hassan',     'Engineering',       'Junior Developer',      'a.hassan@acmecorp.local',     '555-0107', '107'),
(8, 'Claire Dubois',    'Marketing',         'Marketing Lead',        'c.dubois@acmecorp.local',     '555-0108', '108');

-- VULN: passwords stored in cleartext
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    role ENUM('user','admin') DEFAULT 'user',
    last_login DATETIME
);

INSERT INTO users VALUES
(1, 'admin',      'C0rp0rate!2021',     'admin@acmecorp.local',       'admin', '2024-03-01 09:12:00'),
(2, 'j.harrington','JamesH@2022',       'j.harrington@acmecorp.local','user',  '2024-02-28 14:30:00'),
(3, 'm.santos',   'HRmanager99',        'm.santos@acmecorp.local',    'user',  '2024-03-01 08:00:00'),
(4, 's.thompson', 'SysAdm1n!',          's.thompson@acmecorp.local',  'user',  '2024-02-20 11:15:00');

-- Admin flag table
CREATE TABLE flags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    value VARCHAR(200)
);

INSERT INTO flags VALUES (1, 'admin_flag', 'FLAG{time_based_sqli_referrer_bypass_cleartext_creds}');
