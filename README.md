# agent-skills

This repository, formerly known as `OpenClaw-Skills`, serves as a centralized collection of skills designed for autonomous agents. It has been restructured to enhance organization, maintainability, and clarity for developers and users.

## Repository Structure

All the original skill modules and their associated files, previously located at the root of the repository, have been moved into a dedicated subdirectory named `openclaw-skills/`. This change provides a cleaner root directory for repository-level documentation and configuration, while centralizing all skill-related content.

```
/agent-skills/
├── README.md                 (This file)
├── LICENSE
├── .gitignore
└── openclaw-skills/          (Contains all individual skill modules)
    ├── market/
    ├── media-gen/
    ├── perplexity-search/
    ├── prediction-market/
    ├── prediction-market-arbitrage/
    ├── search/
    ├── twitter/
    └── youtube/
```

## Accessing Skills

To explore the individual skill modules, navigate to the `openclaw-skills/` directory. Each subdirectory within `openclaw-skills/` represents a distinct skill and contains its own `README.md` and `SKILL.md` files, along with supporting scripts and documentation.

For detailed information on each skill, including its purpose, usage, and API references, please refer to the `README.md` and `SKILL.md` files located within each respective skill directory (e.g., `openclaw-skills/market/README.md`).

## Agent Harness Compatibility

AIsa agent skills are designed for broad compatibility and can be integrated with various agent harnesses, including:

*   **Claude Code**
*   **OpenClaw**
*   **Hermes**

This flexibility allows developers to leverage these skills across different agent platforms, ensuring wider applicability and ease of integration.

## Contribution

We welcome contributions to the `agent-skills` repository. Please refer to the individual skill documentation for guidelines on adding new skills or improving existing ones.

## License

This project is licensed under the Apache 2.0 License. See the `LICENSE` file for details.
