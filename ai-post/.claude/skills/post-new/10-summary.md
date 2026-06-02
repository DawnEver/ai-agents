# Step 10 — Present Summary

Summarize: which articles were generated, review results (pass/fail per platform), and suggest next steps.

## For articles that passed review (✅ or ⚠️ after fixes)

Articles are at `ongoing/<slug>/3-final/<platform>.md` (review-passed copies).

1. **Publish**: `/post-publish <platform> <slug>` — clipboard export + platform publishing guidance
2. **After publishing all platforms**, archive the entire slug: `/post-archive <slug>`

## For articles that failed review (❌)

- **Regenerate**: `/post-regenerate <slug> <platform>` or manual edit, then re-run review
- Failed articles remain in `ongoing/<slug>/2-draft/` — NOT copied to `3-final/`
