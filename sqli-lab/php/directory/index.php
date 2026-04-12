<?php
// ============================================================
// Staff Directory - AcmeCorp Intranet
// VULN 1: Referrer-based access control (bypassable)
// VULN 2: Time-based blind SQL injection in search parameter
// ============================================================

// VULN 1: Referrer check — only allows access from news.php
// The error message intentionally leaks the required referrer.
$required_referrer = 'news.php';
$referrer = $_SERVER['HTTP_REFERER'] ?? '';

if (strpos($referrer, $required_referrer) === false) {
    http_response_code(403);
    ?>
    <!DOCTYPE html>
    <html>
    <head>
        <title>Access Denied — OutForm Portal</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body { background: #fff3ee; }
            .box { max-width: 560px; margin: 80px auto; }
            .brand { color: #f26522; font-weight: 800; font-size: 20px; margin-bottom: 20px; display:block; }
        </style>
    </head>
    <body>
    <div class="box">
        <span class="brand">✉️ OutForm</span>
        <div class="alert" style="border-left: 5px solid #f26522; background:#fff; border-radius:6px;">
            <h5 style="color:#c94e0e;">⛔ Access Denied</h5>
            <p>Direct access to the Author Directory is not permitted.</p>
            <p>This page may only be accessed via the letters portal.</p>
            <hr>
            <p class="mb-1"><strong>Required referrer:</strong></p>
            <code>http://<?= $_SERVER['HTTP_HOST'] ?>/news.php</code>
            <hr>
            <small class="text-muted">
                If you believe this is an error, please contact
                <a href="mailto:support@outform.co.uk" style="color:#f26522;">support@outform.co.uk</a>.
            </small>
        </div>
        <a href="../index.php" class="btn btn-sm" style="background:#f26522;color:#fff;">&larr; Back to Portal Home</a>
    </div>
    </body>
    </html>
    <?php
    exit();
}

// Passed referrer check — load the page
$page_title = "Staff Directory — AcmeCorp Intranet";
$page_title = "Author Directory — OutForm Portal";
include '../includes/header.php';
require_once '../config/db.php';

// VULN 2: Time-based blind SQL injection
// $search is passed directly into the query with no sanitisation.
// Payloads:
//   ' AND SLEEP(5)-- -
//   ' AND IF(1=1,SLEEP(5),0)-- -
//   ' AND IF((SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='C',SLEEP(5),0)-- -
$search = $_GET['q'] ?? '';
$dept_filter = $_GET['dept'] ?? '';

$sql = "SELECT * FROM staff WHERE 1=1";

if ($search !== '') {
    // VULN: raw interpolation — no prepared statement, no escaping
    $sql .= " AND (name LIKE '%$search%' OR department LIKE '%$search%' OR position LIKE '%$search%')";
}
if ($dept_filter !== '') {
    $sql .= " AND department = '" . $conn->real_escape_string($dept_filter) . "'";
}
$sql .= " ORDER BY department, name";

$result = $conn->query($sql);
$staff  = $result ? $result->fetch_all(MYSQLI_ASSOC) : [];

// Get departments for filter dropdown
$depts_res = $conn->query("SELECT DISTINCT department FROM staff ORDER BY department");
$departments = $depts_res ? array_column($depts_res->fetch_all(MYSQLI_ASSOC), 'department') : [];
?>

<h4 class="section-title">👥 Author Directory</h4>
<p class="text-muted mb-4">Search for letter authors by name, department or role.</p>

<form method="GET" action="" class="mb-4">
    <div class="form-row align-items-end">
        <div class="col-md-5">
            <label for="q" class="sr-only">Search</label>
            <input type="text"
                   id="q"
                   name="q"
                   class="form-control"
                   placeholder="Search by name, department or title..."
                   value="<?= htmlspecialchars($search) ?>">
        </div>
        <div class="col-md-3">
            <select name="dept" class="form-control">
                <option value="">All Departments</option>
                <?php foreach ($departments as $d): ?>
                    <option value="<?= htmlspecialchars($d) ?>" <?= $dept_filter === $d ? 'selected' : '' ?>>
                        <?= htmlspecialchars($d) ?>
                    </option>
                <?php endforeach; ?>
            </select>
        </div>
        <div class="col-md-2">
            <button type="submit" class="btn btn-primary btn-block">Search</button>
        </div>
        <?php if ($search || $dept_filter): ?>
        <div class="col-md-2">
            <a href="index.php" class="btn btn-outline-secondary btn-block">Clear</a>
        </div>
        <?php endif; ?>
    </div>
</form>

<?php if ($search !== ''): ?>
    <p class="text-muted small mb-3">
        <?= count($staff) ?> result(s) for <em>"<?= htmlspecialchars($search) ?>"</em>
    </p>
<?php endif; ?>

<?php if (empty($staff)): ?>
    <div class="alert alert-info">No staff members found matching your search.</div>
<?php else: ?>
<div class="table-responsive">
    <table class="table table-hover table-bordered bg-white">
        <thead class="thead-light">
            <tr>
                <th>Name</th>
                <th>Department</th>
                <th>Position</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Ext.</th>
            </tr>
        </thead>
        <tbody>
        <?php foreach ($staff as $row): ?>
            <tr>
                <td><?= htmlspecialchars($row['name']) ?></td>
                <td><span class="badge badge-secondary"><?= htmlspecialchars($row['department']) ?></span></td>
                <td><?= htmlspecialchars($row['position']) ?></td>
                <td><a href="mailto:<?= htmlspecialchars($row['email']) ?>"><?= htmlspecialchars($row['email']) ?></a></td>
                <td><?= htmlspecialchars($row['phone']) ?></td>
                <td><?= htmlspecialchars($row['ext']) ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
</div>
<?php endif; ?>

<?php include '../includes/footer.php'; ?>
