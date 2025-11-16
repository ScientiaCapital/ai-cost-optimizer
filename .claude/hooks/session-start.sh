#!/bin/bash
python3 ~/Desktop/tk_projects/doc_health_check.py --project $(basename $PWD) 2>/dev/null | grep -E "STALE|AGING" && {
    echo ""
    echo "⚠️  Documentation needs refresh!"
    echo "   Run: ./refresh_docs.sh"
    echo ""
}
