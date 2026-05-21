from sqlalchemy import Column, Integer, DateTime, Numeric
from app.database import Base


class MlBaserateRaw(Base):
    __tablename__ = "ml_baserate_raw"

    br_id = Column(Integer, primary_key=True)
    loaded_date = Column(DateTime, primary_key=True)
    kr_base_rate = Column(Numeric(15, 2))
    kr_cpi = Column(Numeric(15, 2))
    kr_unemployment = Column(Numeric(15, 2))
    kr_usd_exchange = Column(Numeric(15, 2))
    kr_gdp = Column(Numeric(15, 2))
    kr_m2 = Column(Numeric(15, 2))
    us_fed_rate = Column(Numeric(15, 2))
    vix = Column(Numeric(15, 2))
    wti_oil = Column(Numeric(15, 2))


class MlGoldRaw(Base):
    __tablename__ = "ml_gold_raw"

    gr_id = Column(Integer, primary_key=True)
    loaded_date = Column(DateTime, primary_key=True)
    gold = Column(Numeric(15, 2))
    kr_usd_exchange = Column(Numeric(15, 2))
    wti_oil = Column(Numeric(15, 2))
    dxy_proxy = Column(Numeric(15, 2))
    vix = Column(Numeric(15, 2))
    kospi200 = Column(Numeric(15, 2))
    sp500 = Column(Numeric(15, 2))
    kr_cpi = Column(Numeric(15, 2))


class MlRealestateRaw(Base):
    __tablename__ = "ml_realestate_raw"

    rr_id = Column(Integer, primary_key=True)
    loaded_date = Column(DateTime, primary_key=True)
    house_price_idx = Column(Numeric(15, 2))
    kr_cpi = Column(Numeric(15, 2))
    kr_unemployment = Column(Numeric(15, 2))
    kr_base_rate = Column(Numeric(15, 2))
    kr_mortgage_rate = Column(Numeric(15, 2))
    kospi200 = Column(Numeric(15, 2))
    apt_trade_count = Column(Numeric(15, 2))
    kr_m2 = Column(Numeric(15, 2))
    buyer_dominance = Column(Numeric(15, 2))
