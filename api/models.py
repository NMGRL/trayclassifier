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
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import relationship

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKeyConstraint,
    ForeignKey,
    Float,
    BLOB,
    DateTime,
    LargeBinary,
    func,
    Boolean,
)


@as_declarative()
class Base:
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    __name__: str

    # to generate tablename from classname
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__


class User(Base):
    name = Column(String)


class Label(Base):
    name = Column(String)


class Labels(Base):
    image_id = Column(Integer, ForeignKey('Image.id'))
    label_id = Column(Integer, ForeignKey('Label.id'))
    user_id = Column(Integer, ForeignKey('User.id'))

    image = relationship('Image', uselist=False)
    user = relationship('User', uselist=False)
    label = relationship('Label', uselist=False)


class Image(Base):
    blob = Column(LargeBinary)
    name = Column(String)
    hashid = Column(String)
# ============= EOF =============================================
