<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= htmlspecialchars($page_title ?? 'OutForm — Letter Services Portal') ?></title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        :root {
            --orange:      #f26522;
            --orange-dark: #c94e0e;
            --orange-light:#fff3ee;
        }
        body { background: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; color: #333; }
        .navbar { background: var(--orange) !important; }
        .navbar-brand { color: #fff !important; font-weight: 800; font-size: 22px; letter-spacing: -0.5px; }
        .navbar-brand span { color: #fff3a0; }
        .nav-link { color: rgba(255,255,255,.85) !important; }
        .nav-link:hover { color: #fff !important; }
        .hero-banner {
            background: linear-gradient(135deg, var(--orange) 0%, var(--orange-dark) 100%);
            color: #fff; padding: 36px 32px; border-radius: 8px; margin-bottom: 24px;
        }
        .hero-banner h1 { font-size: 26px; font-weight: 700; margin-bottom: 6px; }
        .portal-card { border: 1px solid #ffe5d3; border-top: 4px solid var(--orange); border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,.06); transition: box-shadow .2s; background: #fff; }
        .portal-card:hover { box-shadow: 0 4px 18px rgba(242,101,34,.18); }
        .portal-card .icon { font-size: 38px; margin-bottom: 10px; }
        .btn-primary { background: var(--orange); border-color: var(--orange); }
        .btn-primary:hover { background: var(--orange-dark); border-color: var(--orange-dark); }
        .badge-secondary { background: var(--orange); }
        .quick-links li { margin-bottom: 8px; }
        .quick-links a { color: var(--orange); }
        .news-body { white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 13.5px; background: #fafafa; padding: 16px; border-left: 4px solid var(--orange); }
        .list-group-item-action:hover { background: var(--orange-light); }
        .section-title { color: var(--orange-dark); font-weight: 700; border-bottom: 2px solid var(--orange); padding-bottom: 6px; margin-bottom: 18px; }
        .footer { margin-top: 50px; padding: 20px 0; border-top: 2px solid var(--orange); color: #888; font-size: 13px; }
        .letter-badge { background: var(--orange-light); color: var(--orange-dark); border: 1px solid #f7c6a8; font-size: 11px; padding: 3px 8px; border-radius: 12px; }
    </style>
</head>
<body>
<nav class="navbar navbar-expand-lg">
    <a class="navbar-brand" href="/index.php">Out<span>Form</span></a>
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#nav" style="border-color:rgba(255,255,255,.5)">
        <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="nav">
        <ul class="navbar-nav ml-auto">
            <li class="nav-item"><a class="nav-link" href="/index.php">Home</a></li>
            <li class="nav-item"><a class="nav-link" href="/news.php">Letters</a></li>
            <li class="nav-item"><a class="nav-link" href="/about.php">About</a></li>
            <li class="nav-item"><a class="nav-link" href="/admin/login.php">Staff Login</a></li>
        </ul>
    </div>
</nav>
<div class="container mt-4">
