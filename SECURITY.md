# Security Policy

## Reporting a vulnerability

Please report security issues privately to **info@nirry.net** rather than in a
public issue. You'll get an acknowledgement, and a fix or a clear explanation.

## Design notes

- tokrate connects only to the endpoint you give it and sends only the prompt you
  give it. It reads the streamed response to time it; it doesn't execute anything
  from the response.
- A bearer token is read from an **environment variable** (`--api-key-env`), not
  passed on the command line, so it doesn't land in your shell history or the
  process list.

## Supported versions

Fixes land on the latest release.
