# Security and data boundaries

SynapseETL is an independent educational portfolio project. All included records,
organizations, identifiers, and scenarios are synthetic. No company source,
model weights, credentials, customer data, or private configuration is included.

The default demo has no network access and requires no credentials. Explicitly
configured model endpoints receive only the inputs supplied by the caller.
Never submit private data or commit `.env` files. Database files are ignored.

This is a local reference implementation, with no multi-user authentication,
tenant isolation, or hosted service hardening. Approval identity in local demos
is a caller-provided label, not authenticated identity. Do not expose it as a
public API or treat it as a production security boundary.

Please report a suspected vulnerability privately using GitHub's security
advisory feature when available. Include a minimal synthetic reproducer.
