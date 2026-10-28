# Defensive catalog data

This directory contains small, curated starter catalogs used by the Streamlit app.

## tool_catalog.csv

One row per defensive tool. Important fields:

- name, category, description: tool identity and high-level use.
- strengths, limitations: concise fit considerations; these are starter summaries, not a full product audit.
- cost_model, deployment, suitable_environments, priorities, skill_level: transparent tags used by the profile-matching logic.
- official_url, source_url: project website and official documentation/source.
- last_reviewed: date the repository's starter entry was reviewed.

Included entries cover endpoint/security monitoring, network monitoring, vulnerability management, web application testing, software supply-chain scanning, and runtime monitoring. Verify current features, supported systems, licenses, maintenance status, and total cost of ownership before selecting a tool.

## control_catalog.csv

One row per foundational defensive control. Source links point to public guidance such as CISA, NIST, CIS, or OWASP. The records are intentionally high-level and are not a claim that a named framework prescribes every exact sentence in the catalog.

## Matching limitations

The app scores tag overlap with a session security profile. Scores are **not** model accuracy, measured effectiveness, security guarantees, or an independent endorsement. A higher score means only that more manually assigned tags matched. Missing or broad tags can affect the order. Human review is required.

The catalogs do not include user ratings. Do not treat these records as user feedback or use the match score as ground-truth relevance for research evaluation without a documented review protocol.

## Sources

- Wazuh documentation: https://documentation.wazuh.com/current/getting-started/index.html
- Suricata documentation: https://docs.suricata.io/
- Zeek overview: https://docs.zeek.org/en/current/about/what.html
- Greenbone Community Edition / OpenVAS scanner: https://github.com/greenbone/openvas-scanner
- OWASP ZAP: https://www.zaproxy.org/
- Trivy documentation: https://trivy.dev/latest/
- Falco documentation: https://falco.org/docs/
- Security Onion documentation: https://docs.securityonion.net/en/2.4/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- CIS Critical Security Controls: https://www.cisecurity.org/controls
- CISA Known Exploited Vulnerabilities catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- CISA Secure Our World: https://www.cisa.gov/secure-our-world
- OWASP Top 10: https://owasp.org/www-project-top-ten/
