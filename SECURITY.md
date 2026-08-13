# Security Policy

## Supported scope

Only the current Stage 1A simulator-only development baseline is supported. No production deployment, real device, real institution or personal-data processing is approved.

## Reporting

Do not open a public issue containing a vulnerability, secret, private key, device identity, customer information or personal data. Report privately to the repository owner through GitHub private vulnerability reporting after the remote repository is configured.

If a credential is exposed, stop use immediately, revoke or rotate it outside Git, preserve only sanitized evidence, and notify the accountable owner. Deleting the file from the latest commit is not sufficient remediation for an exposed secret.

## Prohibited repository content

- Production or shared-environment secrets
- Device, CA, content-signing or OTA private keys
- Real student, teacher, customer or institution data
- Firmware binaries, diagnostic bundles, raw logs or database dumps
- Unredacted security captures
