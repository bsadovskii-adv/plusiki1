# -*- coding: utf-8 -*-

import os

DB_PATH = os.getenv("DB_PATH", "data.db")
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")
