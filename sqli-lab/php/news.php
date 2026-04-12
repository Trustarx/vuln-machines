<?php
require_once 'includes/referrer_check.php';
require_referrer(null); // must come from same host
$page_title = "Dispatched Letters — OutForm";
include 'includes/header.php';

$news_dir = __DIR__ . '/content/news/';
$articles = [];

foreach (glob($news_dir . '*.txt') as $file) {
    $content = file_get_contents($file);
    $lines = explode("\n", trim($content));
    $meta = []; $body_lines = []; $in_body = false;
    foreach ($lines as $line) {
        if (!$in_body && preg_match('/^(DATE|TITLE|AUTHOR):\s*(.+)$/', $line, $m)) {
            $meta[strtolower($m[1])] = trim($m[2]);
        } else { $in_body = true; $body_lines[] = $line; }
    }
    $articles[] = [
        'id'     => (int) basename($file),
        'title'  => $meta['title']  ?? 'Untitled',
        'date'   => $meta['date']   ?? '',
        'author' => $meta['author'] ?? 'Unknown',
        'body'   => implode("\n", array_slice($body_lines, 1)),
    ];
}
usort($articles, fn($a, $b) => strcmp($b['date'], $a['date']));

$selected = null;
if (isset($_GET['id'])) {
    $idx = (int)$_GET['id'] - 1;
    if (isset($articles[$idx])) $selected = $articles[$idx];
}
?>

<h4 class="section-title">📬 Dispatched Letters</h4>

<?php if ($selected): ?>
<div class="card mb-4" style="border-top: 4px solid #f26522;">
    <div class="card-header bg-white d-flex justify-content-between align-items-center">
        <strong><?= htmlspecialchars($selected['title']) ?></strong>
        <span class="letter-badge"><?= htmlspecialchars($selected['date']) ?></span>
    </div>
    <div class="card-body">
        <p class="text-muted small mb-3">Authored by: <strong><?= htmlspecialchars($selected['author']) ?></strong></p>
        <pre class="news-body"><?= htmlspecialchars($selected['body']) ?></pre>
    </div>
    <div class="card-footer bg-white">
        <a href="news.php" class="btn btn-sm btn-outline-secondary">&larr; All Letters</a>
        &nbsp;
        <a href="directory/index.php" class="btn btn-sm btn-primary">Author Directory</a>
    </div>
</div>
<?php else: ?>

<p class="text-muted">Browse completed letters below, or use the <a href="directory/index.php">Author Directory</a> to search by author.</p>

<div class="list-group">
<?php foreach ($articles as $i => $a): ?>
    <a href="news.php?id=<?= $i+1 ?>" class="list-group-item list-group-item-action">
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <strong><?= htmlspecialchars($a['title']) ?></strong><br>
                <small class="text-muted"><?= htmlspecialchars($a['author']) ?></small>
            </div>
            <span class="letter-badge ml-2"><?= htmlspecialchars($a['date']) ?></span>
        </div>
    </a>
<?php endforeach; ?>
</div>
<?php endif; ?>

<?php include 'includes/footer.php'; ?>
