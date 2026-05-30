#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ -f venv/bin/python ]; then
    venv/bin/python main.py
elif [ -f venv/bin/python3 ]; then
    venv/bin/python3 main.py
else
    python3 main.py || python main.py
fi
