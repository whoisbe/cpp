# CPP Map Visualizer Prompt v1 (System Concept Map)

Task: Create ONE compact ASCII concept map that shows relationships between the numbered ideas below.

Input:
{{IDEAS_LIST}}

Output format (exactly):
Map:
<ASCII concept map <= 18 lines OR (none)>

Rules (critical):
- Output ONLY the ASCII map, no prose or explanations
- Keep it <= 18 lines total
- Use idea numbers (e.g., [1], [2]) in node labels when possible
- Prefer: hub/spoke patterns, layered dependencies, comparison columns, category groupings
- Avoid: step-by-step process flows, mechanism flowcharts
- Show relationships, dependencies, and categories between ideas
- If the ideas don't form a meaningful map, output (none)
