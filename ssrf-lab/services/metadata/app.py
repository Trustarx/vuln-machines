"""
Mock AWS EC2 Instance Metadata Service (IMDSv1)
================================================
Simulates http://169.254.169.254/latest/meta-data/...

In real AWS, the metadata service is reachable from inside an EC2 instance
at the link-local address 169.254.169.254. SSRF that can reach that address
can pull IAM role credentials and use them against AWS APIs.

In this lab the service is on a docker `internal` network and reachable only
by name as `metadata` or `aws-metadata.internal`. Any host that can SSRF to
those names lands here.
"""

from flask import Flask, Response

app = Flask(__name__)


# --- IMDSv1-style endpoints --------------------------------------

@app.route("/")
def root():
    return "latest\n"


@app.route("/latest/")
def latest():
    return "meta-data/\nuser-data\ndynamic/\n"


@app.route("/latest/meta-data/")
def meta_index():
    return ("ami-id\nhostname\ninstance-id\ninstance-type\n"
            "iam/\nlocal-ipv4\npublic-ipv4\nsecurity-groups\n")


@app.route("/latest/meta-data/instance-id")
def instance_id():
    return "i-0fae21c0d3f8b9a44"


@app.route("/latest/meta-data/hostname")
def hostname():
    return "ip-10-0-1-243.ec2.internal"


@app.route("/latest/meta-data/local-ipv4")
def local_ipv4():
    return "10.0.1.243"


@app.route("/latest/meta-data/public-ipv4")
def public_ipv4():
    return "54.180.91.18"


@app.route("/latest/meta-data/instance-type")
def instance_type():
    return "t3.medium"


@app.route("/latest/meta-data/iam/")
def iam_root():
    return "info\nsecurity-credentials/\n"


@app.route("/latest/meta-data/iam/security-credentials/")
def role_list():
    # Tells the attacker which IAM role this box is using
    return "PaperPress-RenderRole"


@app.route("/latest/meta-data/iam/security-credentials/PaperPress-RenderRole")
def role_creds():
    """The juicy bit — temporary IAM credentials.

    These look real. The flag is in the SecretAccessKey value so we can
    tell the user "you got the flag" once they read this endpoint.
    """
    body = (
        "{\n"
        '  "Code": "Success",\n'
        '  "LastUpdated": "2025-01-15T12:34:56Z",\n'
        '  "Type": "AWS-HMAC",\n'
        '  "AccessKeyId": "AKIAQX7TIAJ8FAKEROLEXX",\n'
        '  "SecretAccessKey": "FLAG{ssrf_to_imds_metadata_pwned}",\n'
        '  "Token": "IQoJb3JpZ2luX2VjEJj//////////wEaCXVzLWVhc3QtMSJGMEQCIBfakeTokenForLab",\n'
        '  "Expiration": "2099-12-31T23:59:59Z"\n'
        "}\n"
    )
    return Response(body, mimetype="application/json")


@app.route("/latest/user-data")
def user_data():
    # Common SSRF target — cloud-init scripts often contain credentials
    return ("#!/bin/bash\n"
            "# Cloud-init bootstrap for PaperPress render workers\n"
            "export DB_PASSWORD='Sup3rS3cretRDS!2024'\n"
            "export ADMIN_API_KEY='admin-api-key-7f3a2b1c'\n"
            "echo 'PaperPress worker provisioned' > /var/log/cloud-init.done\n")


@app.route("/health")
def health():
    return "ok\n"


if __name__ == "__main__":
    # IMPORTANT: bind on 80 so attackers using `http://metadata/` (no port)
    # land here naturally, mirroring real IMDS.
    app.run(host="0.0.0.0", port=80, debug=False)
