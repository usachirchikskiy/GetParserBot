#!/bin/bash
alembic revision --autogenerate -m "Database created"
alembic upgrade head
python3 -m src.bot.start.py