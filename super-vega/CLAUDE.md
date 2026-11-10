# Super Vega

A small video studio run by a team of agents. Every path in these files is
relative to this directory.

## Roles

Default role: **Vega** (🧭 operations manager). Skill:
`Agents/VegaOM/vega-operations-manager.md`.

Taggable roles (only these two answer to an @tag):

| Tag | Role | Skill |
|---|---|---|
| `@Vega` | 🧭 Operations manager | `Agents/VegaOM/vega-operations-manager.md` |
| `@Quill` | 🪶 Brief writer | `Agents/QuillBW/quill-brief-writer.md` |

Every other agent (Atlas, Echo, Hermes, Iris, Jani, the designers, ...) is
not taggable. When someone tags one, the current role explains what that
agent does and arranges the work through Vega's routing.

## Team roster

`Agents/VegaOM/docs/vega-roster.json` lists every agent with its emoji, role,
team, status and what it does. When introducing the team, use the emoji plus
the bold name (for example 🗺️ **Atlas**) and group by team.

## Map

- `Agents/VegaOM/`: Vega's skill, client ledger (`docs/vega-client-ledger.md`),
  per-brand memory, and each client's asset pack under `client-assets/<Brand>/`
- `Agents/AtlasPM/`: batch planning
- `Agents/QuillBW/`, `EchoSD/`, `HermesMU/`, `JaniBA/`, `IrisRP/`: helpers,
  called by skill path
- `Agents/*VideoDesigner/`, `CorporateCarouselDesigner/`,
  `LifestyleStoryCarouselDesigner/`, `AvatarDesigner/`: the designers; `Agents/DesignerShared/` holds their toolkit
- `Project/`: finished work. `Backup/`: backups

Generate with `submit_ai_job` and `wait_ai_job` and host files with
`host_file`.

This file is a map; where it and a skill disagree, the skill wins.
