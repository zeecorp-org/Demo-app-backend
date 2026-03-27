from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SOSMap(Base):
    __tablename__ = "sos_maps"
    __table_args__ = (
        UniqueConstraint("user_id", "friendship_id", name="uq_sos_map_user_friendship"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    friendship_id: Mapped[int] = mapped_column(
        ForeignKey("friendships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[user_id], lazy="joined"
    )
    friendship: Mapped["Friendship"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Friendship", foreign_keys=[friendship_id], lazy="joined"
    )
