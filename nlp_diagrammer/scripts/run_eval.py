import json
import os
import sys
# Ensure we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nlp_diagrammer.diagrammer import render_diagram
from nlp_diagrammer.heuristics import select_template

def main():
    print("Running Evaluation...")
    
    # Load test cases
    test_path = os.path.join(os.path.dirname(__file__), '../tests/test_cases.json')
    with open(test_path, 'r') as f:
        cases = json.load(f)
        
    out_dir = os.path.join(os.path.dirname(__file__), '../out')
    os.makedirs(out_dir, exist_ok=True)
    
    report_lines = ["# Evaluation Report\n"]
    
    passed = 0
    total = len(cases)
    
    for case in cases:
        idea = case['input']
        
        # Get heuristic analysis for debugging
        kind, analysis = select_template(idea)
        
        diagram = render_diagram(idea)
        
        report_lines.append(f"## Case {case['id']}: {idea}")
        report_lines.append(f"- Derived Kind: {kind}")
        report_lines.append(f"- Confidence: {analysis.get('confidence', 0.0)}")
        report_lines.append(f"- Reasons: {analysis.get('reasons', [])}")
        
        if diagram is None:
            report_lines.append("- Result: NONE (Failed to parse)")
            continue
            
        report_lines.append("```")
        for line in diagram:
            report_lines.append(line)
        report_lines.append("```")
        
        # Check constraints
        if len(diagram) > 8:
             report_lines.append("- FAIL: Line count > 8")
        else:
             report_lines.append("- PASS: Line count constraint")
             passed += 1

    report_content = "\n".join(report_lines)
    print(f"Passed {passed}/{total} basic checks.")
    
    # Write report
    import time
    ts = int(time.time())
    with open(os.path.join(out_dir, f"eval_{ts}.md"), 'w') as f:
        f.write(report_content)
    print(f"Report written to out/eval_{ts}.md")

if __name__ == "__main__":
    main()
