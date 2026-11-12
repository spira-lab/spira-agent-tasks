# Super Vega v2.09: system update, 2026-11-12d (package 1.6.5)

The record of Hermes filing into another Spira environment. Vega reads it when anyone asks what changed, or when told to announce the update. Only the `## Announcement` section is ever sent to the groups, word for word.

## Announcement

✨ Super Vega v2.09 is live (2026-11-12)

Finished videos and carousels can now be filed into the main Spira library even when the team works from the test environment. When an upload fails, the reply says which Spira site it went to, so a wrong tag or an expired sign-in is easy to spot.

## What changed

### Platform (not in the package)
- `upload_social_post_asset` uploads to the employee's `config.assetUpload` target when one is set (a credential minted in that environment's admin and pasted into the employee's settings), else to the environment the run is in, as before. Every error ends with `(upload target: <host>)`; a refused credential reads `UNAUTHORIZED 401: the upload credential for <host> expired or was revoked`, an expired one `UPLOAD_CREDENTIAL_EXPIRED`.

### Hermes
- `Agents/HermesMU/hermes-media-uploader.md`: errors name the upload target; Tag IDs belong to that environment; `UNAUTHORIZED` and `UPLOAD_CREDENTIAL_*` stop the batch with `FAILED <the reason as the tool gave it>`.
- `Agents/HermesMU/docs/hermes-working-memory.md`: a Tag ID belongs to one Spira environment.

## Not carried over
- Tag IDs in the working memory are not checked against any environment; they stay as the owner gave them.

## Open
- Mint a credential in prod, paste it into the dev employee, and have Hermes re-upload task 50; check the asset appears under IASO / Vietnam in prod.
