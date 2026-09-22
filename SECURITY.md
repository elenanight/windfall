# Security Policy

## Supported Versions

Only the latest release and the two releases immediately before it receive
security fixes (a sliding window of three, refreshed on every cut). Releases
older than the window are end-of-life and will not receive patches:

<!-- security:start -->
| Version  | Supported          |
| -------- | ------------------ |

| 0.2.7    | :white_check_mark: |
| 0.2.6    | :white_check_mark: |
| 0.2.5    | :white_check_mark: |
| <= 0.2.4 | :x:               |

The window is the latest release plus the two prior releases (3 total), sliding on every cut.
<!-- security:end -->

## Reporting a Vulnerability

Please do **not** open a public issue for security problems. Instead,
use [private vulnerability reporting](https://github.com/elenanight/windfall/security/advisories/new)
so the report stays visible only to you and the maintainers until a fix
ships.

Include, where you can:

- what you found and where (file, version, command),
- steps to reproduce or proof of concept,
- what you think the impact is.

## What to Expect

- Acknowledgement of your report.
- Triage and a fix released as a patch version, with the advisory
  published once the fix is out.
- Credit in the advisory if you want it — say so in the report.

Dependency vulnerabilities are additionally tracked by Dependabot alerts
and fixed through Dependabot security updates.
