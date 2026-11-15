"""DB のテーブルと Python のクラスの対応。

検索で使う列だけを定義している（DB にはほかの列もある）。
★「要確認」の列名は、配布のデータ定義（データ定義.md）が手元になかったため仮置きしている。
  実際の列名と違ったら、Column の第1引数（DB 上の列名）だけ直せばよい。
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    """products（商品・約8,000件）。列名は Exhibit 4「商品の既存カラム」と同じ"""

    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))
    brand: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)  # 直近1年の販売数
    stock: Mapped[int] = mapped_column(Integer, default=0)


class Order(Base):
    """orders（注文・約28万件）"""

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    # 要確認：注文した会員の列名
    user_id: Mapped[str] = mapped_column("user_id", String(20))
    # 要確認：注文日時の列名
    ordered_at: Mapped[datetime] = mapped_column("ordered_at", DateTime)
    # 分析部門が推定したシーン（Exhibit 4）
    estimated_scene: Mapped[str | None] = mapped_column(String(50))
    # チームで追加する列（要件定義書 5.2）。sql/001 で追加する
    relationship: Mapped[str | None] = mapped_column(String(20))


class OrderItem(Base):
    """order_items（注文明細）。要確認：明細自体の主キー列は検索に使わないため、
    (order_id, product_id) を ORM 上の主キーとして扱う"""

    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), primary_key=True)


class GiftFeedback(Base):
    """gift_feedback（相手の反応・チームで新規作成。要件定義書 5.2）。sql/001 で作る"""

    __tablename__ = "gift_feedback"

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), unique=True)
    reaction: Mapped[int] = mapped_column(SmallInteger)  # 4:とても喜んだ〜1:いまひとつ
    comment: Mapped[str | None] = mapped_column(Text)
    answered_at: Mapped[datetime] = mapped_column(DateTime)
