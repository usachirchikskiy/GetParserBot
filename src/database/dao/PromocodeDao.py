from src.database.dao.BaseDao import BaseDao
from src.database.model.User import Promocode


class PromocodeDao(BaseDao):
    model = Promocode
