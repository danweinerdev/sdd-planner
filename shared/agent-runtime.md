# Agent Runtime Conventions

This plugin provides skills, not slash commands or plugin-defined subagent types. A skill is selected from its description when the user asks for its workflow in natural language. The skills are runtime-neutral: they work in any agent runtime that loads `SKILL.md` skills (via a plugin installation or the `.agents/skills` discovery convention) and with any model.

## Terminology

Throughout this plugin, *collaboration subagent* means whatever delegation mechanism the current runtime provides — a task tool, a subagent, a collaboration agent, or a forked session. If the runtime provides none, the primary agent performs the work itself.

## Plugin resources

The plugin root is the directory containing `skills/` and `shared/`. When a skill needs a bundled template or reference, resolve it relative to the loaded skill's path: `<plugin-root>/skills/<skill-name>/SKILL.md`. Read the needed file under `<plugin-root>/shared/`; never look in runtime caches or tool-specific plugin directories.

If the runtime does not expose the loaded skill path, search for the unique sibling pair `skills/<skill-name>/SKILL.md` and `shared/frontmatter-schema.md` in the available skill directories. Do not select a version by cache ordering.

## Delegation

Use collaboration subagents only when they are available and a task is independent enough to benefit from parallel work. Do not depend on plugin-defined agent names, specific models, tool allowlists, or any particular delegation API. A skill must remain correct when performed by the primary agent alone.

## Project guidance

Use `AGENTS.md` for optional repository-level guidance. Do not create, update, or discover `CLAUDE.md`, `.claude/`, or `~/.claude/` paths.
