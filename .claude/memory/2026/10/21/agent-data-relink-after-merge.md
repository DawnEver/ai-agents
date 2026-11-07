---
name: agent-data-relink-after-merge
description: Relinking data dirs after pulling a new link-agent-data.sh layout
metadata:
  type: project
---

After merging a new link-agent-data.sh mapping, links from the old layout can dangle (e.g. cc-docx/out, cc-docx/workspace pointed at agent-data/cc-docx/{out,workspace}, which no longer exist). The script refuses to replace them only when they are real dirs; remove dangling symlinks (check they are links first), then rerun. cc-docx/workspace and cc-slides/workspace now map to the whole agent-data/<project> root. A mapping whose source is missing in agent-data is SKIPped: create the empty ongoing/archived dirs there, then rerun. Finally rerun node .claude/hooks/allow-data-links.js so settings.local.json covers the new links.
