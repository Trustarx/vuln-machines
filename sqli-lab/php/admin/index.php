<?php
session_start();
if (empty($_SESSION['user_id'])) {
    header('Location: login.php');
    exit();
}
require_once '../config/db.php';

$flag_row = $conn->query("SELECT value FROM flags WHERE name='admin_flag'")->fetch_assoc();
$flag = $flag_row['value'] ?? 'FLAG_NOT_FOUND';

$users = $conn->query("SELECT id, username, email, role, last_login FROM users ORDER BY id")->fetch_all(MYSQLI_ASSOC);
?>
<!DOCTYPE html>
<html>
<head>
    <title>Staff Dashboard — OutForm Portal</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body { background: #fff3ee; }
        .topbar { background: #f26522; color: #fff; padding: 12px 24px; display:flex; justify-content:space-between; align-items:center; }
        .flag-box { background: #1e272e; color: #2ecc71; font-family: monospace; padding: 16px 20px; border-radius: 6px; font-size: 15px; margin: 20px 0; border: 1px solid #2ecc71; }
        .container { max-width: 960px; margin-top: 30px; }
    </style>
</head>
<body>
<div class="topbar">
    <div><strong>✉️ OutForm</strong> &mdash; Staff Dashboard</div>
    <div>Logged in as: <strong><?= htmlspecialchars($_SESSION['username']) ?></strong>
    &nbsp;|&nbsp; <a href="logout.php" style="color:#e74c3c;">Logout</a></div>
</div>

<div class="container">
    <div class="flag-box">
        🏁 <?= htmlspecialchars($flag) ?>
    </div>

    <div class="card mb-4">
        <div class="card-header"><strong>👤 User Accounts</strong></div>
        <div class="card-body p-0">
            <table class="table table-sm mb-0">
                <thead class="thead-light">
                    <tr><th>#</th><th>Username</th><th>Email</th><th>Role</th><th>Last Login</th></tr>
                </thead>
                <tbody>
                <?php foreach ($users as $u): ?>
                    <tr>
                        <td><?= $u['id'] ?></td>
                        <td><strong><?= htmlspecialchars($u['username']) ?></strong></td>
                        <td><?= htmlspecialchars($u['email']) ?></td>
                        <td><span class="badge badge-<?= $u['role']==='admin'?'danger':'secondary' ?>"><?= $u['role'] ?></span></td>
                        <td><small class="text-muted"><?= $u['last_login'] ?? 'Never' ?></small></td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    </div>

    <div class="card mb-4">
        <div class="card-header"><strong>📋 Staff Records</strong></div>
        <div class="card-body">
            <p class="text-muted mb-0">
                <?= $conn->query("SELECT COUNT(*) AS c FROM staff")->fetch_assoc()['c'] ?> staff members on record.
                <a href="../directory/index.php">View Directory</a>
            </p>
        </div>
    </div>
</div>
</body>
</html>
