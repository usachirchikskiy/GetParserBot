from src.database.dao.BaseDao import BaseDao
from src.database.model.User import Mailing


class MailingDao(BaseDao):
    model = Mailing
