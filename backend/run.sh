#!/bin/bash
source env/bin/activate
uvicorn app.main:app --reload --port "${APP_PORT:-8005}"
