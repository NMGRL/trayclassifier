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
from typing import Optional, Union

from pydantic import BaseModel


class UnclassifiedImage(BaseModel):
    trayname: str
    hole_id: int
    image: str
    zoom_level: Union[float, int]

    loadname: Optional[str] = None
    project: Optional[str] = None
    sample: Optional[str] = None
    material: Optional[str] = None
    identifier: Optional[str] = None
    weight: Optional[float] = None
    note: Optional[str] = None
    nxtals: Optional[int] = None


class ORMBase(BaseModel):
    id: Optional[int] = None

    class Config:
        orm_mode = True


class User(ORMBase):
    name: str


class Image(ORMBase):
    name: str
    hashid: str
    blob: bytes


class ImageInfo(ORMBase):
    hole_id: int
    loadname: str
    trayname: str
    hashid: str


class Label(ORMBase):
    name: str


class Labels(ORMBase):
    pass
# ============= EOF =============================================
