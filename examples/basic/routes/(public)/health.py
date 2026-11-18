# Route groups like (public) don't appear in the URL -> GET /health
async def get():
    return {"status": "ok"}
