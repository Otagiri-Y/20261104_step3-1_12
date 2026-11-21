"""DB のテーブルと Python のクラスの対応。

検索で使う列だけを定義している（DB にはほかの列もある）。
列名と型は、班の DB の SHOW CREATE TABLE（2026-11-21 確認）に合わせている。
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    """products（商品・約8,000件）"""

    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(30))
    brand: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))  # 商品全体の★
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)  # 直近1年の販売数
    stock: Mapped[int] = mapped_column(Integer, default=0)


class Order(Base):
    """orders（注文・約28万件）"""

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20))
    ordered_at: Mapped[datetime] = mapped_column(DateTime)
    # 分析部門が注文ごとに推定したシーン（Exhibit 4）
    estimated_scene: Mapped[str] = mapped_column(String(20))
    # 余力：チームで追加する列（要件定義書 5.2）。sql/001 で追加する
    relationship: Mapped[str | None] = mapped_column(String(20))


class OrderItem(Base):
    """order_items（注文明細）。主キーは (order_id, line_no)"""

    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), primary_key=True)
    line_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"))


class Review(Base):
    """reviews（購入者のレビュー）。注文IDはないので、注文とは user_id × product_id で結ぶ（要件定義書 5.2）"""

    __tablename__ = "reviews"

    review_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"))
    user_id: Mapped[str] = mapped_column(String(20))
    rating: Mapped[int] = mapped_column(Integer)  # 1〜5
    comment: Mapped[str | None] = mapped_column(Text)  # 空のこともある（コメント付きは約3割）
    posted_at: Mapped[date] = mapped_column(Date)  # 日付だけ（時刻はない）


class GiftFeedback(Base):
    """gift_feedback（相手の反応・Phase2。要件定義書 5.2）。sql/001 で作る。範囲Bでは使わない"""

    __tablename__ = "gift_feedback"

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), unique=True)
    reaction: Mapped[int] = mapped_column(SmallInteger)  # 4:とても喜んだ〜1:いまひとつ
    comment: Mapped[str | None] = mapped_column(Text)
    answered_at: Mapped[datetime] = mapped_column(DateTime)


class SiteEventLog(Base):
    """site_event_log（計測の記録・範囲Bで新規。要件定義書 5.2・FR-11）。sql/003 で作る。
    1行が1つの行動。個人を特定する情報は持たない"""

    __tablename__ = "site_event_log"

    # 班の DB では BIGINT。テストの SQLite は INTEGER でないと自動で番号が振られないので、型を出し分ける
    event_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    session_id: Mapped[str] = mapped_column(String(36))
    event_type: Mapped[str] = mapped_column(String(20))  # pdp_view／add_to_cart
    product_id: Mapped[str] = mapped_column(String(10))
    scene: Mapped[str | None] = mapped_column(String(20))  # なしは NULL
    occurred_at: Mapped[datetime] = mapped_column(DateTime)  # API が受け取った時刻（日本時間）
