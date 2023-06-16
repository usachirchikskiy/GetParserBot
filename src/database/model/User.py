from datetime import datetime

from sqlalchemy import Column, String, BigInteger, Integer, Float, ForeignKey, Boolean, UniqueConstraint, \
    TIMESTAMP
from sqlalchemy.orm import relationship

from src.database.database import Base


class UserSubscriptionAssociation(Base):
    __tablename__ = "user_subscription_association"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    subscription_id = Column(Integer, ForeignKey('subscription.id', ondelete='CASCADE'))
    is_favourite = Column(Boolean, default=False)
    expired_at = Column(TIMESTAMP)

    user = relationship("User", back_populates="subscriptions")
    subscription = relationship("Subscription", back_populates="users")


class UserSubscriptionFilterAssociation(Base):
    __tablename__ = "user_subscription_filter_association"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    subscription_id = Column(Integer, ForeignKey('subscription.id', ondelete='CASCADE'))
    filter_id = Column(Integer, ForeignKey('filter.id', ondelete='CASCADE'))
    is_favourite = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    title = Column(String)

    user = relationship("User", back_populates="filters")
    subscription = relationship("Subscription", back_populates="filters")
    filter = relationship("Filter", back_populates="user_subscription_associations")

    __table_args__ = (
        UniqueConstraint('user_id', 'subscription_id', 'filter_id', name='user_subscription_filter_uc'),
    )


class UserPaymentSystemAssociation(Base):
    __tablename__ = "user_payment_system_association"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    payment_system_id = Column(Integer, ForeignKey('payment_system.id', ondelete='CASCADE'))
    type = Column(String)

    user = relationship("User", back_populates="payment_systems")
    payment_system = relationship("PaymentSystem", back_populates="users")


class User(Base):
    __tablename__ = "user"
    id = Column(BigInteger, primary_key=True)
    balance = Column(Float)
    bot_message = Column(String)
    subscriptions = relationship(
        "UserSubscriptionAssociation",
        back_populates="user",
        passive_deletes=True,
        cascade="all, delete-orphan",
    )
    filters = relationship(
        "UserSubscriptionFilterAssociation",
        back_populates="user",
        passive_deletes=True,
        cascade="all, delete-orphan"
    )
    payment_systems = relationship(
        "UserPaymentSystemAssociation",
        back_populates="user",
        passive_deletes=True,
        cascade="all, delete-orphan",
    )


class Subscription(Base):
    __tablename__ = 'subscription'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price_one_day = Column(Integer)
    price_three_day = Column(Integer)
    price_week = Column(Integer)
    price_month = Column(Integer)
    users = relationship(
        "UserSubscriptionAssociation",
        back_populates="subscription",
        passive_deletes=True,
        cascade="all, delete-orphan",
    )
    filters = relationship(
        "UserSubscriptionFilterAssociation",
        back_populates="subscription",
        passive_deletes=True,
        cascade="all, delete-orphan",
    )


class Filter(Base):
    __tablename__ = 'filter'

    id = Column(Integer, primary_key=True)
    value = Column(String)
    question_number = Column(Integer)
    user_subscription_associations = relationship(
        "UserSubscriptionFilterAssociation",
        back_populates='filter',
        passive_deletes=True,
        cascade="all, delete-orphan",
    )


class PaymentSystem(Base):
    __tablename__ = 'payment_system'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    users = relationship(
        "UserPaymentSystemAssociation",
        back_populates='payment_system',
        passive_deletes=True,
        cascade="all, delete-orphan"
    )


# — Кол-во объявлений продавца
# — Кол-во проданных товаров
# — Дата регистрации продавца
# — Дата создания объявления
# — Рейтинг продавца


# — Кол-во объявлений продавца
# — Кол-во проданных товаров
# — Кол-во купленных товаров
# — Дата регистрации продавца
# — Дата создания объявления
# — Рейтинг продавца
