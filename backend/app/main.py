from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean, Float, create_engine, inspect, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from datetime import datetime, date
import hashlib
import os
import random

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./golf.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    scores = relationship("Score", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    entries = relationship("DrawEntry", back_populates="user", cascade="all, delete-orphan")
    winners = relationship("Winner", back_populates="user", cascade="all, delete-orphan")


class Charity(Base):
    __tablename__ = "charities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    image_url = Column(String, default="")
    category = Column(String, default="Community")
    featured = Column(Boolean, default=False)
    location = Column(String, default="")
    upcoming_events = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="charity")


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    score_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scores")


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan = Column(String, default="monthly")
    status = Column(String, default="active")
    amount = Column(Float, default=19.99)
    currency = Column(String, default="USD")
    renewal_date = Column(Date, default=date.today)
    charity_percentage = Column(Integer, default=10)
    charity_id = Column(Integer, ForeignKey("charities.id"), nullable=True)
    donation_amount = Column(Float, default=0.0)
    donation_note = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscription")
    charity = relationship("Charity", back_populates="subscriptions")


class Draw(Base):
    __tablename__ = "draws"
    id = Column(Integer, primary_key=True, index=True)
    month = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String, default="draft")
    draw_type = Column(String, default="random")
    winning_numbers = Column(String, default="")
    total_pool = Column(Float, default=0)
    jackpot = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship("DrawEntry", back_populates="draw", cascade="all, delete-orphan")
    winners = relationship("Winner", back_populates="draw", cascade="all, delete-orphan")


class DrawEntry(Base):
    __tablename__ = "draw_entries"
    id = Column(Integer, primary_key=True, index=True)
    draw_id = Column(Integer, ForeignKey("draws.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    selected_numbers = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    draw = relationship("Draw", back_populates="entries")
    user = relationship("User", back_populates="entries")


class Winner(Base):
    __tablename__ = "winners"
    id = Column(Integer, primary_key=True, index=True)
    draw_id = Column(Integer, ForeignKey("draws.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prize_tier = Column(String, nullable=False)
    amount = Column(Float, default=0)
    verification_status = Column(String, default="pending")
    payout_status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    draw = relationship("Draw", back_populates="winners")
    user = relationship("User", back_populates="winners")


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "user"
    charity_id: int | None = None
    charity_percentage: int = Field(default=10, ge=10, le=100)
    donation_amount: float = Field(default=0.0, ge=0)
    donation_note: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class ScorePayload(BaseModel):
    score: int = Field(..., ge=1, le=45)
    score_date: date | None = None


class ScoreUpdatePayload(BaseModel):
    score: int = Field(..., ge=1, le=45)
    score_date: date | None = None


class SubscriptionPayload(BaseModel):
    plan: str = "monthly"
    status: str = "active"
    charity_percentage: int = Field(default=10, ge=10, le=100)
    charity_id: int | None = None
    donation_amount: float = Field(default=0.0, ge=0)
    donation_note: str = ""


class CharityPayload(BaseModel):
    name: str
    description: str = ""
    image_url: str = ""
    category: str = "Community"
    featured: bool = False
    location: str = ""
    upcoming_events: str = ""


class CharitySearchPayload(BaseModel):
    q: str | None = None
    category: str | None = None
    featured: bool | None = None


class DrawEntryPayload(BaseModel):
    selected_numbers: str | None = None
    quantity: int = Field(default=1, ge=1, le=10)


class DrawConfigPayload(BaseModel):
    draw_type: str = "random"


class AdminUserUpdatePayload(BaseModel):
    full_name: str | None = None
    role: str | None = None


class DrawSimulationPayload(BaseModel):
    winning_numbers: str | None = None


class WinnerVerificationPayload(BaseModel):
    status: str


class WinnerPayoutPayload(BaseModel):
    status: str


app = FastAPI(title="Golf Impact Platform", version="1.0.0")
origins = [
    "http://localhost:5173",
    "https://golf-frontend-hxiqhmyl3-muskan090s-projects.vercel.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


def get_current_user(db: Session, token: str | None):
    if not token:
        raise HTTPException(status_code=401, detail="Missing x-token")
    if not token.startswith("user-"):
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(token.split("-", 1)[1])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def ensure_schema():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "charities" in tables:
        charity_columns = {column["name"] for column in inspector.get_columns("charities")}
        if "upcoming_events" not in charity_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE charities ADD COLUMN upcoming_events TEXT DEFAULT ''"))

    if "subscriptions" in tables:
        subscription_columns = {column["name"] for column in inspector.get_columns("subscriptions")}
        if "donation_amount" not in subscription_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN donation_amount FLOAT DEFAULT 0.0"))
        if "donation_note" not in subscription_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN donation_note VARCHAR DEFAULT ''"))


def seed_data(db: Session):
    if db.query(Charity).count() == 0:
        charities = [
            Charity(name="Swing for Hope", description="Supports youth golf access programs.", image_url="", category="Youth", featured=True, location="London", upcoming_events="Community golf day on 14 July • Youth clinic on 21 July"),
            Charity(name="Birdie & Beyond", description="Funds community health initiatives.", image_url="", category="Health", featured=False, location="Manchester", upcoming_events="Charity fundraiser at the club on 2 August"),
            Charity(name="Fairway Futures", description="Provides scholarships for underrepresented golfers.", image_url="", category="Education", featured=True, location="Bristol", upcoming_events="Scholarship tee-off event on 11 September"),
        ]
        db.add_all(charities)
    if db.query(User).count() == 0:
        admin = User(email="admin@digitalheroes.com", password_hash=hash_password("admin123"), full_name="Admin User", role="admin")
        db.add(admin)
    if db.query(Draw).count() == 0:
        current_month = datetime.utcnow().strftime("%B")
        current_year = datetime.utcnow().year
        db.add(Draw(month=current_month, year=current_year, status="draft", draw_type="random", jackpot=0, total_pool=0))
    db.commit()


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password), full_name=payload.full_name, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    subscription = Subscription(user_id=user.id, plan="monthly", status="active", amount=19.99, renewal_date=date.today().replace(day=1), charity_percentage=payload.charity_percentage, charity_id=payload.charity_id, donation_amount=payload.donation_amount, donation_note=payload.donation_note)
    db.add(subscription)
    db.commit()
    return {"user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}, "token": f"user-{user.id}"}


@app.post("/api/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}, "token": f"user-{user.id}"}


@app.get("/api/me")
def get_me(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    scores = db.query(Score).filter(Score.user_id == user.id).order_by(Score.score_date.desc(), Score.created_at.desc()).all()
    charity = None
    if subscription and subscription.charity_id:
        charity = db.query(Charity).filter(Charity.id == subscription.charity_id).first()
    return {
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
        "subscription": {
            "plan": subscription.plan if subscription else "monthly",
            "status": subscription.status if subscription else "inactive",
            "charity_percentage": subscription.charity_percentage if subscription else 10,
            "renewal_date": subscription.renewal_date if subscription else None,
            "donation_amount": subscription.donation_amount if subscription else 0,
            "donation_note": subscription.donation_note if subscription else "",
        },
        "scores": [{"id": score.id, "score": score.score, "score_date": score.score_date.isoformat()} for score in scores],
        "charity": {"id": charity.id, "name": charity.name} if charity else None,
    }


@app.get("/api/charities")
def get_charities(q: str | None = None, category: str | None = None, featured: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Charity)
    if q:
        query = query.filter(Charity.name.contains(q) | Charity.description.contains(q))
    if category:
        query = query.filter(Charity.category == category)
    if featured is not None:
        query = query.filter(Charity.featured == featured)
    charities = query.order_by(Charity.featured.desc(), Charity.name).all()
    return [{"id": c.id, "name": c.name, "description": c.description, "image_url": c.image_url, "category": c.category, "featured": c.featured, "location": c.location, "upcoming_events": c.upcoming_events} for c in charities]


@app.get("/api/charities/{charity_id}")
def get_charity(charity_id: int, db: Session = Depends(get_db)):
    charity = db.query(Charity).filter(Charity.id == charity_id).first()
    if not charity:
        raise HTTPException(status_code=404, detail="Charity not found")
    return {"id": charity.id, "name": charity.name, "description": charity.description, "image_url": charity.image_url, "category": charity.category, "featured": charity.featured, "location": charity.location, "upcoming_events": charity.upcoming_events}


@app.post("/api/charities", status_code=201)
def create_charity(payload: CharityPayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    charity = Charity(**payload.dict())
    db.add(charity)
    db.commit()
    db.refresh(charity)
    return charity


@app.put("/api/charities/{charity_id}")
def update_charity(charity_id: int, payload: CharityPayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    charity = db.query(Charity).filter(Charity.id == charity_id).first()
    if not charity:
        raise HTTPException(status_code=404, detail="Charity not found")
    for key, value in payload.dict().items():
        setattr(charity, key, value)
    db.commit()
    db.refresh(charity)
    return charity


@app.delete("/api/charities/{charity_id}")
def delete_charity(charity_id: int, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    charity = db.query(Charity).filter(Charity.id == charity_id).first()
    if not charity:
        raise HTTPException(status_code=404, detail="Charity not found")
    db.delete(charity)
    db.commit()
    return {"message": "Charity deleted"}


@app.get("/api/scores")
def get_scores(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    scores = db.query(Score).filter(Score.user_id == user.id).order_by(Score.score_date.desc(), Score.created_at.desc()).all()
    return [{"id": score.id, "score": score.score, "score_date": score.score_date.isoformat()} for score in scores]


@app.post("/api/scores", status_code=201)
def create_score(payload: ScorePayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    score_date = payload.score_date or date.today()
    if score_date is None:
        raise HTTPException(status_code=422, detail="Score date is required")

    new_score = Score(user_id=user.id, score=payload.score, score_date=score_date)
    db.add(new_score)
    db.commit()

    existing_scores = db.query(Score).filter(Score.user_id == user.id).order_by(Score.score_date.asc(), Score.created_at.asc()).all()
    if len(existing_scores) > 5:
        oldest = existing_scores[0]
        db.delete(oldest)
        db.commit()

    return {"message": "Score recorded", "retained_scores": 5}


@app.put("/api/scores/{score_id}")
def update_score(score_id: int, payload: ScoreUpdatePayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    score_record = db.query(Score).filter(Score.id == score_id, Score.user_id == user.id).first()
    if not score_record:
        raise HTTPException(status_code=404, detail="Score not found")
    score_record.score = payload.score
    score_record.score_date = payload.score_date or score_record.score_date
    db.commit()
    return {"message": "Score updated"}


@app.get("/api/subscription")
def get_subscription(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not subscription:
        subscription = Subscription(user_id=user.id, plan="monthly", status="active", amount=19.99, charity_percentage=10)
        db.add(subscription)
        db.commit()
    return {"plan": subscription.plan, "status": subscription.status, "amount": subscription.amount, "charity_percentage": subscription.charity_percentage, "renewal_date": subscription.renewal_date.isoformat(), "charity_id": subscription.charity_id, "donation_amount": subscription.donation_amount, "donation_note": subscription.donation_note}


@app.post("/api/subscription")
def update_subscription(payload: SubscriptionPayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not subscription:
        subscription = Subscription(user_id=user.id)
        db.add(subscription)
    subscription.plan = payload.plan
    subscription.status = payload.status
    subscription.charity_percentage = payload.charity_percentage
    subscription.charity_id = payload.charity_id
    subscription.donation_amount = payload.donation_amount
    subscription.donation_note = payload.donation_note
    db.commit()
    return {"message": "Subscription updated"}


@app.get("/api/draws")
def get_draws(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    today = datetime.utcnow()
    draw = db.query(Draw).filter(Draw.month == today.strftime("%B"), Draw.year == today.year).first()
    if not draw:
        draw = Draw(month=today.strftime("%B"), year=today.year, status="draft", draw_type="random", jackpot=0, total_pool=0)
        db.add(draw)
        db.commit()
    entries = db.query(DrawEntry).filter(DrawEntry.draw_id == draw.id).order_by(DrawEntry.created_at.desc()).all()
    winners = db.query(Winner).filter(Winner.draw_id == draw.id).order_by(Winner.created_at.desc()).all()
    return {
        "draw": {"id": draw.id, "month": draw.month, "year": draw.year, "status": draw.status, "winning_numbers": draw.winning_numbers, "total_pool": draw.total_pool, "jackpot": draw.jackpot},
        "entries": [{"id": entry.id, "selected_numbers": entry.selected_numbers, "full_name": entry.user.full_name} for entry in entries],
        "winners": [{"id": winner.id, "full_name": winner.user.full_name, "prize_tier": winner.prize_tier, "amount": winner.amount, "verification_status": winner.verification_status, "payout_status": winner.payout_status} for winner in winners],
    }


@app.post("/api/draws/enter", status_code=201)
def enter_draw(payload: DrawEntryPayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    today = datetime.utcnow()
    draw = db.query(Draw).filter(Draw.month == today.strftime("%B"), Draw.year == today.year).first()
    if not draw:
        draw = Draw(month=today.strftime("%B"), year=today.year, status="draft", draw_type="random", jackpot=0, total_pool=0)
        db.add(draw)
        db.commit()

    entries_created = []
    for _ in range(payload.quantity):
        numbers = payload.selected_numbers or f"{random.randint(10000, 99999)}"
        entry = DrawEntry(draw_id=draw.id, user_id=user.id, selected_numbers=numbers)
        db.add(entry)
        entries_created.append(numbers)

    db.commit()
    return {"message": "Entry recorded", "selected_numbers": entries_created, "quantity": len(entries_created)}


@app.get("/api/draws")
def get_draws(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    today = datetime.utcnow()
    draw = db.query(Draw).filter(Draw.month == today.strftime("%B"), Draw.year == today.year).first()
    if not draw:
        draw = Draw(month=today.strftime("%B"), year=today.year, status="draft", draw_type="random", jackpot=0, total_pool=0)
        db.add(draw)
        db.commit()

    entries = db.query(DrawEntry).filter(DrawEntry.draw_id == draw.id).order_by(DrawEntry.created_at.desc()).all()
    winners = db.query(Winner).filter(Winner.draw_id == draw.id).order_by(Winner.created_at.desc()).all()
    return {
        "draw": {
            "id": draw.id,
            "month": draw.month,
            "year": draw.year,
            "status": draw.status,
            "draw_type": draw.draw_type,
            "winning_numbers": draw.winning_numbers,
            "total_pool": draw.total_pool,
            "jackpot": draw.jackpot,
        },
        "entries": [{"id": entry.id, "selected_numbers": entry.selected_numbers, "full_name": entry.user.full_name} for entry in entries],
        "winners": [{"id": winner.id, "full_name": winner.user.full_name, "prize_tier": winner.prize_tier, "amount": winner.amount, "verification_status": winner.verification_status, "payout_status": winner.payout_status} for winner in winners],
    }


@app.post("/api/admin/draws/publish")
def publish_draw(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    today = datetime.utcnow()
    draw = db.query(Draw).filter(Draw.month == today.strftime("%B"), Draw.year == today.year).first()
    if not draw:
        draw = Draw(month=today.strftime("%B"), year=today.year, status="draft", draw_type="random", jackpot=0, total_pool=0)
        db.add(draw)
        db.commit()
    if draw.status == "published":
        return {"message": "Draw already published", "winning_numbers": draw.winning_numbers, "jackpot": draw.jackpot}

    active_subscribers = db.query(Subscription).filter(Subscription.status == "active").count()
    prize_pool = max(100, active_subscribers * 25)
    previous_draw = db.query(Draw).filter(Draw.id != draw.id).order_by(Draw.created_at.desc()).first()
    carry_over = previous_draw.jackpot if previous_draw and previous_draw.jackpot else 0
    jackpot_pool = carry_over + (prize_pool * 0.4)
    four_match_pool = prize_pool * 0.35
    three_match_pool = prize_pool * 0.25

    draw.total_pool = prize_pool
    draw.winning_numbers = f"{random.randint(10000, 99999)}"
    draw.status = "published"
    draw.jackpot = jackpot_pool
    db.query(Winner).filter(Winner.draw_id == draw.id).delete()
    db.commit()

    tier_pools = {"4-match": four_match_pool, "3-match": three_match_pool}
    winners_by_tier = {"5-match": [], "4-match": [], "3-match": []}
    for entry in draw.entries:
        matches = sum(1 for a, b in zip(entry.selected_numbers, draw.winning_numbers) if a == b)
        tier = None
        if matches == 5:
            tier = "5-match"
        elif matches == 4:
            tier = "4-match"
        elif matches == 3:
            tier = "3-match"
        if tier:
            winners_by_tier[tier].append(entry)

    if winners_by_tier["5-match"]:
        five_match_amount = round(jackpot_pool / len(winners_by_tier["5-match"]), 2)
        for entry in winners_by_tier["5-match"]:
            db.add(Winner(draw_id=draw.id, user_id=entry.user_id, prize_tier="5-match", amount=five_match_amount, verification_status="pending", payout_status="pending"))
        draw.jackpot = 0
    else:
        draw.jackpot = jackpot_pool

    for tier in ["4-match", "3-match"]:
        if winners_by_tier[tier]:
            tier_amount = round(tier_pools[tier] / len(winners_by_tier[tier]), 2)
            for entry in winners_by_tier[tier]:
                db.add(Winner(draw_id=draw.id, user_id=entry.user_id, prize_tier=tier, amount=tier_amount, verification_status="pending", payout_status="pending"))

    db.commit()
    return {"message": "Draw published", "winning_numbers": draw.winning_numbers, "jackpot": draw.jackpot, "total_pool": draw.total_pool}


@app.post("/api/admin/draws/simulate")
def simulate_draw(payload: DrawSimulationPayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    today = datetime.utcnow()
    draw = db.query(Draw).filter(Draw.month == today.strftime("%B"), Draw.year == today.year).first()
    if not draw:
        draw = Draw(month=today.strftime("%B"), year=today.year, status="draft", draw_type="random", jackpot=0, total_pool=0)
        db.add(draw)
        db.commit()

    winning_numbers = payload.winning_numbers or f"{random.randint(10000, 99999)}"
    results = []
    for entry in draw.entries:
        matches = sum(1 for a, b in zip(entry.selected_numbers, winning_numbers) if a == b)
        tier = None
        if matches == 5:
            tier = "5-match"
        elif matches == 4:
            tier = "4-match"
        elif matches == 3:
            tier = "3-match"
        if tier:
            results.append({"full_name": entry.user.full_name, "selected_numbers": entry.selected_numbers, "tier": tier, "matches": matches})
    return {"winning_numbers": winning_numbers, "results": results}


@app.get("/api/admin/dashboard")
def admin_dashboard(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    total_users = db.query(User).count()
    total_subscriptions = db.query(Subscription).filter(Subscription.status == "active").count()
    total_charities = db.query(Charity).count()
    total_winners = db.query(Winner).count()
    current_draw = db.query(Draw).order_by(Draw.created_at.desc()).first()
    total_pool = sum(draw.total_pool for draw in db.query(Draw).all())
    contribution_totals = sum(subscription.charity_percentage for subscription in db.query(Subscription).all())
    recent_draws = db.query(Draw).order_by(Draw.created_at.desc()).limit(3).all()
    return {
        "total_users": total_users,
        "active_subscriptions": total_subscriptions,
        "total_charities": total_charities,
        "total_winners": total_winners,
        "total_prize_pool": total_pool,
        "charity_contribution_total": contribution_totals,
        "draws": [{"month": draw.month, "year": draw.year, "status": draw.status, "total_pool": draw.total_pool, "jackpot": draw.jackpot, "winning_numbers": draw.winning_numbers} for draw in recent_draws],
        "current_draw": {"status": current_draw.status if current_draw else "draft", "month": current_draw.month if current_draw else ""},
    }


@app.get("/api/admin/users")
def list_users(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role} for u in users]


@app.put("/api/admin/users/{user_id}")
def update_user(user_id: int, payload: AdminUserUpdatePayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    admin = get_current_user(db, x_token)
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        target_user.full_name = payload.full_name
    if payload.role is not None:
        target_user.role = payload.role
    db.commit()
    return {"message": "User updated"}


@app.get("/api/admin/subscriptions")
def list_subscriptions(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    subscriptions = db.query(Subscription).order_by(Subscription.created_at.desc()).all()
    return [{"id": subscription.id, "user_id": subscription.user_id, "plan": subscription.plan, "status": subscription.status, "amount": subscription.amount, "charity_percentage": subscription.charity_percentage, "renewal_date": subscription.renewal_date.isoformat() if subscription.renewal_date else None} for subscription in subscriptions]


@app.post("/api/admin/draws/config")
def update_draw_config(payload: DrawConfigPayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    current_draw = db.query(Draw).order_by(Draw.created_at.desc()).first()
    if current_draw:
        current_draw.draw_type = payload.draw_type
        db.commit()
    return {"message": "Draw config updated", "draw_type": payload.draw_type}


@app.get("/api/admin/winners")
def list_winners(x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    winners = db.query(Winner).order_by(Winner.created_at.desc()).all()
    return [{"id": winner.id, "full_name": winner.user.full_name, "prize_tier": winner.prize_tier, "amount": winner.amount, "verification_status": winner.verification_status, "payout_status": winner.payout_status} for winner in winners]


@app.post("/api/admin/winners/{winner_id}/verify")
def verify_winner(winner_id: int, payload: WinnerVerificationPayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    winner = db.query(Winner).filter(Winner.id == winner_id).first()
    if not winner:
        raise HTTPException(status_code=404, detail="Winner not found")
    winner.verification_status = payload.status
    db.commit()
    return {"message": "Verification updated", "verification_status": winner.verification_status}


@app.post("/api/admin/winners/{winner_id}/payout")
def payout_winner(winner_id: int, payload: WinnerPayoutPayload, x_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(db, x_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    winner = db.query(Winner).filter(Winner.id == winner_id).first()
    if not winner:
        raise HTTPException(status_code=404, detail="Winner not found")
    winner.payout_status = payload.status
    db.commit()
    return {"message": "Payout updated", "payout_status": winner.payout_status}
