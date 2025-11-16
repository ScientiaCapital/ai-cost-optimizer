#!/bin/bash
echo "📋 Project Status for $(basename $PWD)"
echo "======================================"
echo ""
python3 ~/Desktop/tk_projects/doc_health_check.py --project $(basename $PWD) 2>/dev/null
echo ""
echo "🔄 Git Status:"
git status -s 2>/dev/null | head -10 || echo "Not a git repository"
echo ""
echo "📝 TODOs:"
grep -rn "TODO:" . --include="*.py" --include="*.js" --include="*.ts" 2>/dev/null | head -10 || echo "No TODOs found"
