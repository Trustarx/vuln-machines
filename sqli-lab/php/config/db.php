<?php
$db_host = 'db';
$db_name = 'acmecorp';
$db_user = 'acmecorp';
$db_pass = 'acmecorp123';

$conn = new mysqli($db_host, $db_user, $db_pass, $db_name);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
