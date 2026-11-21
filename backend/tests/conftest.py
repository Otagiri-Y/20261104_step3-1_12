"""テスト用の DB（メモリ上の SQLite）。班の DB にはつながない"""
import os

# app を import する前に設定する：.env（接続情報）を読まない
os.environ["GIFTIA_SKIP_DOTENV"] = "1"

from collections.abc import Iterator  # noqa: E402
from datetime import date, datetime  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Order, OrderItem, Product, Review  # noqa: E402

IN_PERIOD = datetime(2026, 3, 1, 12, 0)  # 基準日 2026-06-30 の直近1年に入る
OUT_OF_PERIOD = datetime(2025, 5, 1, 12, 0)  # 1年より前


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    def override() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


class Seeder:
    """テストデータを短く書くための道具"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._order_no = 0
        self._user_no = 0
        self._review_no = 0

    def product(self, pid: str, price: int = 4000, rating: float | None = 4.0,
                sales: int = 10, stock: int = 10, category: str = "食品",
                name: str | None = None, description: str = "") -> str:
        self.db.add(Product(
            product_id=pid, product_name=name or f"商品{pid}", category=category, brand="B",
            description=description, price=price, rating=rating, review_count=5,
            sales_count=sales, stock=stock,
        ))
        return pid

    def buy(self, user_id: str, pid: str, scene: str, relationship: str | None = None,
            at: datetime = IN_PERIOD) -> None:
        """user_id の人が pid を1回買った注文を1件作る"""
        self._order_no += 1
        oid = f"O{self._order_no:06d}"
        self.db.add(Order(order_id=oid, user_id=user_id, ordered_at=at,
                          estimated_scene=scene, relationship=relationship))
        self.db.add(OrderItem(order_id=oid, line_no=1, product_id=pid))

    def orders(self, pid: str, scene: str, relationship: str | None = None, buyers: int = 1,
               at: datetime = IN_PERIOD) -> list[str]:
        """buyers 人（それぞれ別の人）が1回ずつ pid を買った注文を作り、買った人の user_id を返す"""
        users = []
        for _ in range(buyers):
            self._user_no += 1
            uid = f"U{self._user_no:06d}"
            self.buy(uid, pid, scene, relationship, at)
            users.append(uid)
        return users

    def review(self, pid: str, user_id: str, rating: int, comment: str | None = None,
               posted: date = date(2026, 3, 10)) -> str:
        self._review_no += 1
        rid = f"RV{self._review_no:07d}"
        self.db.add(Review(review_id=rid, product_id=pid, user_id=user_id,
                           rating=rating, comment=comment, posted_at=posted))
        return rid

    def commit(self) -> None:
        self.db.commit()


@pytest.fixture
def seed(db: Session) -> Seeder:
    return Seeder(db)
