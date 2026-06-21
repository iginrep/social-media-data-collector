from __future__ import annotations
from fastapi import FastAPI
from apps.api.app.routes import health, comments, sentiment, exports, keywords, schedules

app = FastAPI(title="BNI BIONS Sentiment API", version="0.1.0")

app.include_router(health.router)
app.include_router(comments.router, prefix="/comments", tags=["comments"])
app.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
app.include_router(exports.router, prefix="/exports", tags=["exports"])
app.include_router(keywords.router, prefix="/keywords", tags=["keywords"])
app.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
