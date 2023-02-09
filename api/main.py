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
import base64
import hashlib
import io
import json
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, APIRouter, Response

from sqlalchemy import func, distinct, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from api import schemas
from api.db import setup_db
from api.models import Label, Image, Labels, User
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


@app.post('/add_unclassified_image')
async def add_unclassified_image(payload: schemas.UnclassifiedImage, db: Session = Depends(get_db)):

    img = base64.b64decode(payload.image.encode())

    ha = hashlib.sha256(img).hexdigest()

    q = db.query(Image)
    try:
        q = q.filter(Image.hashid == ha)
        q.one()
        return
    except NoResultFound:
        pass

    payloadargs = payload.dict(exclude={'image',})

    dbim = Image(blob=img, hashid=ha, **payloadargs)
    db.add(dbim)
    db.commit()


@app.post('/label/{image_id}')
async def add_label(image_id: str, label: str = 'good', user: str = 'default', db: Session = Depends(get_db)):
    q = db.query(Image)
    image = q.filter(Image.id == image_id).first()
    label = db.query(Label).filter(Label.name == label).first()
    try:
        user = db.query(User).filter(User.name == user).one()
    except NoResultFound:
        print('no user found', user)
        user = User(name=user)
        db.add(user)
        db.commit()

    label = Labels(label=label, image=image, user=user)
    db.add(label)
    db.commit()


@app.get('/representative_images')
def get_representative_images(db: Session = Depends(get_db)):
    # subquery = db.query(Labels.id).order_by(Labels.label_id).distinct(Labels.label_id).subquery()
    # q = db.query(Labels).filter(Labels.id.in_(select(subquery)))
    subquery = db.query(Labels.id).distinct(Labels.label_id).order_by(Labels.label_id.desc(), Labels.id.desc()).subquery()

    q = db.query(Labels).filter(Labels.id.in_(select(subquery))).order_by(Labels.id)


    records = q.all()
    for r in records:
        print(r.id)
    obj = [{'label': i.label.name,
            # 'name': i.image.name,
            'image': base64.b64encode(i.image.blob).decode()} for i in q.all()]
    return JSONResponse(content=obj)


@app.get('/users', response_model=List[schemas.User])
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@app.get('/scoreboard')
async def get_scoreboard(user: str = None, db: Session = Depends(get_db)):
    q = db.query(Labels.user_id, func.count(Labels.user_id))
    q = q.group_by(Labels.user_id)
    records = q.all()

    rows = [{'name': db.query(User).filter(User.id == u).first().name, 'total': c} for u, c in records]

    rows = sorted(rows, key=lambda x: x['total'], reverse=True)

    if user:
        idx = next((i for i, r in enumerate(rows) if r['name'] == user), None)
        if idx is not None:
            row = rows.pop(idx)
            rows.insert(0, row)

    obj = {'table': rows}
    return JSONResponse(content=obj)


def get_users_report(db, user):
    q = db.query(Labels.label_id,
                 func.count(Labels.label_id)).join(User)

    if user:
        q = q.filter(User.name == user)
    records = q.group_by(Labels.label_id).all()
    rows = [{'label': db.query(Label).filter(Label.id == l).first().name, 'count': c} for l, c in records]
    return rows


@app.get('/user_report/{user}')
async def get_user_report(user: str, db: Session = Depends(get_db)):
    rows = get_users_report(db, user)
    obj = {'table': rows}
    return JSONResponse(content=obj)


@app.get('/results_report')
async def get_result_report(db: Session = Depends(get_db)):
    rows = get_users_report(db, None)
    total = db.query(Image).count()
    classified = db.query(Labels.image_id).group_by(Labels.image_id).count()

    obj = {'table': rows,
           'total': total,
           'unclassified': total - classified}
    return JSONResponse(content=obj)


@app.get('/labels', response_model=List[schemas.Label])
async def get_labels(db: Session = Depends(get_db)):
    q = db.query(Label)
    return q.all()


@app.get('/unclassified_image_info', response_model=Optional[schemas.ImageInfo])
async def get_image_info(image_id: int = None, hashid: str = None, db: Session = Depends(get_db)):
    q = db.query(Image)
    if hashid:
        q = q.filter(Image.hashid == hashid)
    elif image_id:
        q = q.filter(Image.id > image_id)
    else:
        q = q.outerjoin(Labels)
        q = q.filter(Labels.id == None)
        q = q.order_by(Image.id.asc())

    # img = q.first()
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
