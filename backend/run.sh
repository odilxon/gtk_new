#!/bin/bash
source env/Scripts/activate
uvicorn app.main:app --reload --port "${APP_PORT:-8005}"
