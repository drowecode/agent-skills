#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

if [ -z "$AGENTMAIL_API_KEY" ]; then
    echo "⚠️  AGENTMAIL_API_KEY not set."
    echo "   Get your key at https://agentmail.to and set it with:"
    echo "   export AGENTMAIL_API_KEY=your_key_here"
fi

if [ -z "$AISA_API_KEY" ]; then
    echo "⚠️  AISA_API_KEY not set."
    echo "   Required for draft generation and humanizer fallback."
    echo "   export AISA_API_KEY=your_key_here"
fi

echo "✓ Dependencies installed. Add this skill to your agent and ask it to check your emails."
