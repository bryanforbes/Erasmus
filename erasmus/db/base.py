from typing import TYPE_CHECKING, Final

from botus_receptus.gino import Gino, ModelMixin

db: Final = Gino()

if TYPE_CHECKING:
    from gino.crud import CRUDModel

    class Base(CRUDModel, ModelMixin):
        pass

else:
    Base = db.Model
