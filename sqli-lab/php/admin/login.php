<?php
session_start();
require_once '../config/db.php';

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    $stmt = $conn->prepare("SELECT * FROM users WHERE username = ? AND password = ?");
    $stmt->bind_param('ss', $username, $password);
    $stmt->execute();
    $user = $stmt->get_result()->fetch_assoc();
    if ($user) {
        $_SESSION['user_id']  = $user['id'];
        $_SESSION['username'] = $user['username'];
        $_SESSION['role']     = $user['role'];
        $conn->query("UPDATE users SET last_login = NOW() WHERE id = {$user['id']}");
        header('Location: index.php');
        exit();
    } else {
        $error = 'Invalid username or password.';
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Staff Login — OutForm Portal</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body { background: #fff3ee; }
        .login-box { max-width: 400px; margin: 90px auto; }
        .card { border: none; box-shadow: 0 4px 20px rgba(242,101,34,.15); border-radius: 8px; }
        .card-header { background: #f26522; color: #fff; text-align: center; padding: 24px; border-radius: 8px 8px 0 0; }
        .brand { font-size: 26px; font-weight: 800; letter-spacing: -0.5px; }
        .btn-login { background: #f26522; border-color: #f26522; color: #fff; }
        .btn-login:hover { background: #c94e0e; border-color: #c94e0e; color: #fff; }
        a { color: #f26522; }
    </style>
</head>
<body>
<div class="login-box">
    <div class="card">
        <div class="card-header">
            <div class="brand">✉️ OutForm</div>
            <small style="color:rgba(255,255,255,.8);">Staff Portal Login</small>
        </div>
        <div class="card-body p-4">
            <?php if ($error): ?>
                <div class="alert alert-danger py-2 small"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>
            <form method="POST">
                <div class="form-group">
                    <label class="small font-weight-bold">Username</label>
                    <input type="text" name="username" class="form-control" autofocus required>
                </div>
                <div class="form-group">
                    <label class="small font-weight-bold">Password</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-login btn-block font-weight-bold">Sign In</button>
            </form>
        </div>
        <div class="card-footer text-center bg-white" style="border-radius:0 0 8px 8px;">
            <small><a href="../index.php">&larr; Back to Portal</a></small>
        </div>
    </div>
</div>
</body>
</html>
