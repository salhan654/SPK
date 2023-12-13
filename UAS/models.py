from sqlalchemy import Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Laptop(Base):
    __tablename__ = 'laptop'
    id_laptop: Mapped[str] = mapped_column(primary_key=True)
    harga: Mapped[int] = mapped_column()
    ram: Mapped[int] = mapped_column()
    kapasitas_baterai: Mapped[int] = mapped_column()
    processor: Mapped[int] = mapped_column()
    penyimpanan_internal: Mapped[int] = mapped_column()  
    
    def __repr__(self) -> str:
        return f"laptop(id_laptop={self.id_laptop!r}, harga={self.harga!r})"
