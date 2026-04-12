<?php
require_once 'includes/referrer_check.php';
require_referrer(null); // homepage: allow direct access or same-host
$page_title = "OutForm — Letter Services Portal";
include 'includes/header.php';
?>

<div class="hero-banner">
    <h1>✉️ OutForm Letter Services</h1>
    <p class="mb-0">Professional letter drafting, dispatch and tracking for businesses and individuals.</p>
</div>

<div class="row mt-2">
    <div class="col-md-4">
        <div class="card portal-card p-3 text-center">
            <div class="icon">📬</div>
            <h5>Recent Letters</h5>
            <p class="text-muted small">Browse completed and dispatched correspondence.</p>
            <a href="news.php" class="btn btn-primary btn-sm">View Letters</a>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card portal-card p-3 text-center">
            <div class="icon">👥</div>
            <h5>Author Directory</h5>
            <p class="text-muted small">Find letter authors and department contacts.</p>
            <a href="news.php" class="btn btn-primary btn-sm">Browse Authors</a>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card portal-card p-3 text-center">
            <div class="icon">🔒</div>
            <h5>Staff Portal</h5>
            <p class="text-muted small">Internal staff and administrator access.</p>
            <a href="admin/login.php" class="btn btn-secondary btn-sm">Staff Login</a>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-8">
        <h5 class="section-title">Recently Dispatched</h5>
        <div class="list-group">
            <a href="news.php?id=3" class="list-group-item list-group-item-action">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>NHS Referral Confirmation — Dr. Okonkwo</strong><br>
                        <small class="text-muted">Claire Booth &mdash; St. Catherine's Hospital NHS Trust</small>
                    </div>
                    <span class="letter-badge">2024-03-01</span>
                </div>
            </a>
            <a href="news.php?id=2" class="list-group-item list-group-item-action">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>Legal Notice RE: Property Dispute — Ms. Patel</strong><br>
                        <small class="text-muted">James Caldwell &mdash; Caldwell &amp; Partners Solicitors</small>
                    </div>
                    <span class="letter-badge">2024-02-15</span>
                </div>
            </a>
            <a href="news.php?id=1" class="list-group-item list-group-item-action">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>Account Closure Notice — Mr. Henderson</strong><br>
                        <small class="text-muted">Sarah Whitmore &mdash; Greenfield Utilities plc</small>
                    </div>
                    <span class="letter-badge">2024-01-30</span>
                </div>
            </a>
        </div>
    </div>
    <div class="col-md-4">
        <h5 class="section-title">Quick Links</h5>
        <ul class="list-unstyled quick-links">
            <li>📬 <a href="news.php">Dispatched Letters</a></li>
            <li>👥 <a href="news.php">Author Directory</a></li>
            <li>ℹ️ <a href="about.php">About OutForm</a></li>
            <li>🔒 <a href="admin/login.php">Staff Login</a></li>
        </ul>
        <div class="card mt-3" style="border-left: 4px solid #f26522; background:#fff3ee;">
            <div class="card-body py-2 px-3">
                <small class="text-muted"><strong>Need help?</strong><br>
                Contact <a href="mailto:support@outform.co.uk">support@outform.co.uk</a></small>
            </div>
        </div>
    </div>
</div>

<?php include 'includes/footer.php'; ?>
