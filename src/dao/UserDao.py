from src.dao.BaseDao import BaseDao
from src.model.User import User


class UserDao(BaseDao):
    model = User
