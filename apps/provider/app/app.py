"""qtcloud-3r — FastAPI service."""

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException

from . import (
    cmd_review, cmd_reflect, cmd_rewrite, cmd_cycle,
    MAX_INPUT_LENGTH, ReviewError,
)

app = FastAPI(title="qtcloud-3r", version="0.2.0", description="3R writing service")


class TextIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_INPUT_LENGTH, description="待分析文本")


class ReviewOut(BaseModel):
    genre: str
    intent: str
    stage: str
    summary: str


@app.post("/review", response_model=ReviewOut)
def review(body: TextIn):
    try:
        return cmd_review(body.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/reflect")
def reflect(body: TextIn):
    try:
        result = cmd_reflect(body.text)
        if not result:
            return []
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


class RewriteOut(BaseModel):
    text: str
    length: int


@app.post("/rewrite", response_model=RewriteOut)
def rewrite(body: TextIn):
    try:
        result = cmd_rewrite(body.text)
        return {"text": result, "length": len(result)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


class CycleOut(BaseModel):
    review: ReviewOut
    reflect: list
    rewrite: RewriteOut


@app.post("/cycle", response_model=CycleOut)
def cycle(body: TextIn):
    try:
        review = cmd_review(body.text)
        reflect = cmd_reflect(body.text)
        rewritten = cmd_rewrite(body.text)
        return {
            "review": review,
            "reflect": reflect,
            "rewrite": {"text": rewritten, "length": len(rewritten)},
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
