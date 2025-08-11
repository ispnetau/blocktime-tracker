from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, declarative_base, sessionmaker, joinedload
from sqlalchemy import create_engine
import datetime

Base = declarative_base()
engine = create_engine("sqlite:///blocktime.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    contracts = relationship("Contract", back_populates="client")

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    hours_allocated = Column(Float, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates="contracts")
    tickets = relationship("Ticket", back_populates="contract")

    @property
    def remaining_hours(self):
        used = sum(ticket.hours_used for ticket in self.tickets or [])
        return round(self.hours_allocated - used, 1)

class Technician(Base):
    __tablename__ = 'technicians'

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)

    tickets = relationship("Ticket", back_populates="technician")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    hours_used = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"))
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    technician_id = Column(Integer, ForeignKey("technicians.id"))

    client = relationship("Client")
    contract = relationship("Contract", back_populates="tickets")
    technician = relationship("Technician", back_populates="tickets")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_all_clients():
    db = SessionLocal()
    clients = db.query(Client).options(
        joinedload(Client.contracts).joinedload(Contract.tickets)
    ).all()
    db.close()
    return clients

def get_all_tickets():
    db = SessionLocal()
    tickets = db.query(Ticket).options(
        joinedload(Ticket.client),
        joinedload(Ticket.contract),
        joinedload(Ticket.technician)
    ).all()
    db.close()
    return tickets

def get_all_contracts():
    db = SessionLocal()
    contracts = db.query(Contract).options(
        joinedload(Contract.client),
        joinedload(Contract.tickets)
    ).all()
    db.close()
    return contracts

def get_all_technicians():
    db = SessionLocal()
    technicians = db.query(Technician).options(joinedload(Technician.tickets)).all()
    db.close()
    return technicians

def get_technician_report():
    db = SessionLocal()
    result = db.query(
        Technician.first_name,
        Technician.last_name,
        func.sum(Ticket.hours_used).label("total_hours")
    ).join(Ticket).group_by(Technician.id).all()
    db.close()
    return result

