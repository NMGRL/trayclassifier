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
import hashlib
import io
import os

from api.models import Base, Label, Image, Labels, User
from api.session import get_db, engine
from sqlalchemy.exc import NoResultFound
from PIL import Image as PILImage, UnidentifiedImageError
from skimage.color.colorconv import rgb2gray
from numpy import array


def add_label(s, l):
    q = s.query(Label)
    q = q.filter(Label.name == l)
    try:
        if q.one():
            return
    except NoResultFound:
        ll = Label(name=l)
        s.add(ll)
        s.commit()


def add_default_user(s):
    try:
        record = s.query(User).filter(User.name == 'default').one()
    except NoResultFound:
        u = User(name='default')
        s.add(u)
        s.commit()


def setup_db():
    # Base.metadata.create_all(bind=engine)

    sess = next(get_db())
    add_default_user(sess)
    for l in ('good', 'bad', 'empty', 'multigrain', 'contaminant', 'blurry'):
        add_label(sess, l)

    if int(os.environ.get('LOAD_PICS', 0)):
        for tag in ('blurry', 'empty'):
            root = f'./data/421{tag}'
            for f in os.listdir(root):
                p = os.path.join(root, f)
                try:
                    img = PILImage.open(p)
                    width, height = img.size
                    left = 100
                    right = width - left
                    bottom = 100
                    top = height - bottom
                    img = img.crop((left, bottom, right, top))
                except UnidentifiedImageError as e:
                    print('UnidentifiedImageError', e)
                    continue
                #
                # ha = array(img.convert('L')).flatten().tobytes()

                # with open(p, 'rb') as rfile:
                #     buf = rfile.read()
                bb = io.BytesIO()
                img.save(bb, format='tiff')
                buf = bb.getvalue()
                ha = hashlib.sha256(buf).hexdigest()

                q = sess.query(Image)
                try:
                    q = q.filter(Image.hashid == ha)
                    q.one()
                    continue
                except NoResultFound:
                    pass
                name = os.path.basename(p)
                hole_id = name.split('.')[0]
                dbim = Image(blob=buf,
                             sample='foo',
                             material='sanidine',
                             identifier=1000,
                             trayname='421-hole',
                             loadname='test148',
                             hole_id=int(hole_id), hashid=ha)
                # print('asdfasdfasd', name, dbim)
                sess.add(dbim)
                if tag == 'blurry':
                    l = Labels(image=dbim, label_id=6, user_id=1)
                    sess.add(l)
                sess.commit()
                # d.add_labeled_sample(p, array(img), tag)

    sess.close()
# ============= EOF =============================================
