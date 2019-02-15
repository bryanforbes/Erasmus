from typing import TYPE_CHECKING
from botus_receptus.gino import Gino, ModelMixin

db = Gino()

if TYPE_CHECKING:
    from gino.declarative import declarative_base
    from gino.crud import CRUDModel

    Base = declarative_base(db, (CRUDModel, ModelMixin))
else:
    Base = db.Model
