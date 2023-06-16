from src.database.dao.BaseDao import BaseDao
from src.database.model.User import User


class UserDao(BaseDao):
    model = User
