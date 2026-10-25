# Check results collected 2026-10-25 (treat these as the output of today's checks)

## osv-scanner, billing (package-lock.json)
- GHSA-aaaa-bbbb-cccc, xml-tools 3.1.0, CVSS 7.5, fixed in 3.1.4
  Advisory: parseDocument() expands external entities when called on untrusted input. Other functions in the package are not affected.

## Code search, billing
- `src/` imports xml-tools only in `src/vendor/invoice-import.ts`, which re-exports a function from the internal package `@billing/import-core`.
- `@billing/import-core` lives in a separate private repository that is not on this machine, so whether it calls parseDocument(), and on what input, can't be read.

## Mac
- softwareupdate: no updates

## Advisory feed items since 2026-10-24
- none matching the keywords
