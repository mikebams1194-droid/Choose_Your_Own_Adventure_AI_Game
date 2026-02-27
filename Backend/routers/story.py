import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks
from pydantic import UUID4
from requests import Session
from sqlalchemy.orm import Session

from db.database import get_db, SessionLocal
from models.story import Story, StoryNode
from models.job import StoryJob
from schemas.story import CompleteStoryResponse, CompleteStoryNodeResponse, CreateStoryRequest
from schemas.job import StoryJobResponse
from core.story_generator import StoryGenerator
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


async def generate_image(prompt_description: str):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Digital art style, cinematic adventure game scene: {prompt_description}",
            size="1024x1024",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        print(f"DALL-E Error: {e}")
        return None


router = APIRouter(prefix="/stories", tags=["stories"])


def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id


@router.post("/create", response_model=StoryJobResponse)
def create_story(
    request: CreateStoryRequest,
    background_task: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db),
    # Remove session_id: str = Depends(get_session_id)
):
    # 1. Get the UID directly from the request body sent by React
    actual_user_uid = request.session_id

    if not actual_user_uid:
        raise HTTPException(status_code=400, detail="No UID provided")

    job_id = str(uuid.uuid4())

    # 2. Save the job using the REAL UID
    job = StoryJob(job_id=job_id, session_id=actual_user_uid, theme=request.theme, status="pending")
    db.add(job)
    db.commit()

    # 3. Pass that same UID to the background task
    background_task.add_task(
        generate_story_task, job_id=job_id, theme=request.theme, session_id=actual_user_uid
    )

    return job


def generate_story_task(job_id: str, theme: str, session_id: str):
    db = SessionLocal()
    try:
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()
        if not job:
            return

        try:
            job.status = "processing"
            db.commit()

            story = StoryGenerator.generate_story(db, session_id, theme)
            job.story_id = story.id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = str(e)
            db.commit()
    finally:
        db.close()


@router.get("/{story_id}/complete", response_model=CompleteStoryResponse)
def get_complete_story(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    complete_story = build_complete_story_tree(db, story)
    return complete_story


@router.get("/user/{session_id}")
def get_user_stories(session_id: str, db: Session = Depends(get_db)):
    stories = db.query(Story).filter(Story.session_id == session_id).order_by(Story.id.desc()).all()

    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in stories
    ]


def build_complete_story_tree(db: Session, story: Story) -> CompleteStoryResponse:
    nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).all()

    node_dict = {}
    for node in nodes:
        node_response = CompleteStoryNodeResponse(
            id=node.id,
            content=node.content,
            is_ending=node.is_ending,
            is_winning_ending=node.is_winning_ending,
            options=node.options,
        )
        node_dict[node.id] = node_response

    root_node = next((node for node in nodes if node.is_root), None)
    if not root_node:
        raise HTTPException(status_code=500, detail="Story root node not found")

    return CompleteStoryResponse(
        id=story.id,
        title=story.title,
        session_id=story.session_id,
        created_at=story.created_at,
        root_node=node_dict[root_node.id],
        all_nodes=node_dict,
    )


@router.post("/generate-scene-image")
async def get_image(data: dict):
    scene_text = data.get("scene_description")
    if not scene_text:
        return {"error": "No description provided"}

    url = await generate_image(scene_text)
    return {"image_url": url}
