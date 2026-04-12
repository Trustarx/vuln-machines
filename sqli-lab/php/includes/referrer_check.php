<?php
/**
 * OutForm referrer-based access control
 *
 * VULN: The required referrer is leaked in a console.log() in the
 * 403 response — visible in browser DevTools (Console tab) but
 * not rendered on the page itself.
 *
 * Usage:
 *   require_referrer('news.php');          // must come from news.php
 *   require_referrer(null);                // just must come from same host
 */

function require_referrer(?string $required_page = null): void
{
    $host     = $_SERVER['HTTP_HOST'] ?? '';
    $referrer = $_SERVER['HTTP_REFERER'] ?? '';

    // Build the full expected referrer URL for the leak
    $expected = $required_page
        ? "http://{$host}/{$required_page}"
        : "http://{$host}/";

    $allowed = false;

    if ($required_page !== null) {
        // Specific page required
        $allowed = (strpos($referrer, $required_page) !== false);
    } else {
        // Any same-host referrer is fine (or direct to homepage)
        $allowed = (strpos($referrer, $host) !== false) || $referrer === '';
    }

    if (!$allowed) {
        http_response_code(403);
        ?>
<!DOCTYPE html>
<html>
<head>
    <title>403 Forbidden — OutForm</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body { background: #fff3ee; }
        .box { max-width: 500px; margin: 100px auto; text-align: center; }
        .brand { color: #f26522; font-weight: 800; font-size: 22px; }
    </style>
    <script>
        /* OutForm portal access check - dev note: remove before go-live */
        console.log('[OutForm] 403 Forbidden: referrer check failed.');
        console.log('[OutForm] This resource requires navigation from: <?= addslashes($expected) ?>');
    </script>
</head>
<body>
<div class="box">
    <div class="brand">✉️ OutForm</div>
    <div class="mt-4 p-4" style="border:1px solid #f7c6a8; border-radius:8px; background:#fff;">
        <h4 style="color:#c94e0e;">403 — Forbidden</h4>
        <p class="text-muted">You do not have permission to access this page.</p>
        <a href="/index.php" class="btn btn-sm" style="background:#f26522;color:#fff;">Return to Portal</a>
    </div>
</div>
</body>
</html>
        <?php
        exit();
    }
}
