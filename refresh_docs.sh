#!/bin/bash
cd ~/Desktop/tk_projects
echo "🔄 Refreshing documentation for $(basename $PWD)..."
python3 deep_analysis_generator.py --project $(basename $OLDPWD) --use-deepseek
echo "✅ Documentation refresh complete!"
