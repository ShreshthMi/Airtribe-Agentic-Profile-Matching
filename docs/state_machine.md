# State machine

Generated from the compiled LangGraph graph by `python matching_agent.py --diagram`; do not edit by hand. Dashed edges are conditional: the node's result decides which one is taken.

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	parse_jd(parse_jd)
	extract_requirements(extract_requirements)
	search_resumes(search_resumes)
	rank_candidates(rank_candidates)
	generate_report(generate_report)
	human_feedback(human_feedback)
	agent_turn(agent_turn)
	__end__([<p>__end__</p>]):::last
	__start__ --> parse_jd;
	agent_turn -.-> human_feedback;
	agent_turn -.-> parse_jd;
	agent_turn -.-> search_resumes;
	extract_requirements -.-> human_feedback;
	extract_requirements -.-> search_resumes;
	generate_report --> human_feedback;
	human_feedback -.-> __end__;
	human_feedback -.-> agent_turn;
	parse_jd -.-> extract_requirements;
	parse_jd -.-> human_feedback;
	rank_candidates --> generate_report;
	search_resumes --> rank_candidates;
	human_feedback -.-> human_feedback;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```
