# ===============================================================================
# Copyright 2023 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from typing import List

from fastapi import FastAPI, Depends, HTTPException, APIRouter, Response

from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from api import schemas
from api.db import setup_db
from api.models import Label, Image, Labels
from api.session import get_db

# tags_metadata = [
#     {"name": "wells", "description": "Water Wells"},
#     {"name": "repairs", "description": "Meter Repairs"},
#     {"name": "meters", "description": "Water use meters"},
# ]
description = """
"""
title = "Tray Classifier API"

app = FastAPI(
    title=title,
    # description=description,
    # openapi_tags=tags_metadata,
    version="0.0.1",
)
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8051",
    "https://localhost",
    "https://localhost:8000",
    "https://localhost:8051",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_db()


@app.post('/label/{image_id}')
async def add_label(image_id: str, label: str = 'good', db: Session = Depends(get_db)):
    q = db.query(Image)
    image = q.filter(Image.id == image_id).first()

    label = db.query(Label).filter(Label.name == label).first()
    label = Labels(label=label, image=image)
    db.add(label)
    db.commit()


@app.get('/labels', response_model=List[schemas.Label])
async def get_labels(db: Session = Depends(get_db)):
    q = db.query(Label)
    return q.all()


@app.get('/unclassified_image_info', response_model=schemas.ImageInfo)
async def get_image_info(image_id: int = None, hashid: str = None, db: Session = Depends(get_db)):
    q = db.query(Image)
    if hashid:
        q = q.filter(Image.hashid == hashid)
    elif image_id:
        q = q.filter(Image.id > image_id)
    else:
        pass

    return q.first()


@app.get('/unclassified_image',
         responses={
             200: {
                 "content": {"image/tiff": {}}
             }
         },
         response_class=Response)
async def get_image(hashid: str = None, db: Session = Depends(get_db)):
    q = db.query(Image)
    if hashid:
        q = q.filter(Image.hashid == hashid)
    else:
        pass

    dbim = q.first()
    return Response(content=dbim.blob, media_type="image/tiff")
# ============= EOF =============================================
