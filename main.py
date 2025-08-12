from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import joinedload
from typing import Optional
from fastapi import Query
from sqlalchemy import func
from models import (
    SessionLocal, Client, Contract, Ticket, Technician,
    get_all_clients, get_all_tickets, get_all_technicians, get_technician_report, get_all_contracts
)
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/clients", response_class=HTMLResponse)
def view_clients(request: Request):
    clients = get_all_clients()
    return templates.TemplateResponse("clients.html", {"request": request, "clients": clients})

@app.post("/clients")
def add_client(
    name: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...)
):
    db = SessionLocal()
    new_client = Client(
        name=name.strip(),
        contact_name=contact_name.strip(),
        email=email.strip(),
        phone=phone.strip(),
        address=address.strip()
    )
    db.add(new_client)
    db.commit()
    db.close()
    return RedirectResponse(url="/clients", status_code=303)

@app.get("/clients/{client_id}/edit", response_class=HTMLResponse)
def edit_client_form(request: Request, client_id: int):
    db = SessionLocal()
    client = db.query(Client).get(client_id)
    db.close()

    if not client:
        return HTMLResponse("Client not found", status_code=404)

    return templates.TemplateResponse("edit_client.html", {
        "request": request,
        "client": client
    })

@app.post("/clients/{client_id}/edit")
def update_client(
    client_id: int,
    name: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...)
):
    db = SessionLocal()
    client = db.query(Client).get(client_id)

    if not client:
        db.close()
        return HTMLResponse("Client not found", status_code=404)

    client.name = name.strip()
    client.contact_name = contact_name.strip()
    client.email = email.strip()
    client.phone = phone.strip()
    client.address = address.strip()

    db.commit()
    db.close()
    return RedirectResponse(url="/clients", status_code=303)

@app.post("/clients/{client_id}/delete")
def delete_client(client_id: int):
    db = SessionLocal()
    client = db.query(Client).get(client_id)

    if client:
        db.delete(client)
        db.commit()

    db.close()
    return RedirectResponse(url="/clients", status_code=303)


@app.get("/contracts", response_class=HTMLResponse)
def view_contracts(request: Request):
    print("🔥 GET /contracts")
    return templates.TemplateResponse("contracts.html", {
        "request": request,
        "contracts": get_all_contracts(),
        "clients": get_all_clients()
    })

@app.post("/contracts")
def add_contract(
    client_id: int = Form(...),
    name: str = Form(...),
    total_hours: float = Form(...)
):
    print("🔥 POST /contracts")
    db = SessionLocal()
    new_contract = Contract(
        client_id=client_id,
        name=name.strip(),
        hours_allocated=total_hours
    )
    db.add(new_contract)
    db.commit()
    db.close()
    return RedirectResponse(url="/contracts", status_code=303)

@app.get("/contracts/{contract_id}/edit", response_class=HTMLResponse)
def edit_contract_form(request: Request, contract_id: int):
    db = SessionLocal()
    contract = db.query(Contract).get(contract_id)
    clients = get_all_clients()
    db.close()

    if not contract:
        return HTMLResponse("Contract not found", status_code=404)

    return templates.TemplateResponse("edit_contract.html", {
        "request": request,
        "contract": contract,
        "clients": clients
    })

@app.post("/contracts/{contract_id}/edit")
def update_contract(
    contract_id: int,
    client_id: int = Form(...),
    name: str = Form(...),
    total_hours: float = Form(...)
):
    db = SessionLocal()
    contract = db.query(Contract).get(contract_id)

    if not contract:
        db.close()
        return HTMLResponse("Contract not found", status_code=404)

    contract.client_id = client_id
    contract.name = name.strip()
    contract.hours_allocated = total_hours

    db.commit()
    db.close()
    return RedirectResponse(url="/contracts", status_code=303)

@app.post("/contracts/{contract_id}/delete")
def delete_contract(contract_id: int):
    db = SessionLocal()
    contract = db.query(Contract).get(contract_id)

    if contract:
        db.delete(contract)
        db.commit()

    db.close()
    return RedirectResponse(url="/contracts", status_code=303)

@app.get("/tickets", response_class=HTMLResponse)
def view_tickets(
    request: Request,
    client_id: Optional[str] = Query(None),
    technician_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    db = SessionLocal()
    query = db.query(Ticket).options(
        joinedload(Ticket.client),
        joinedload(Ticket.contract),
        joinedload(Ticket.technician)
    )

    # 🔁 Convert empty strings to None and strings to int
    if client_id and client_id.isdigit():
        query = query.filter(Ticket.client_id == int(client_id))

    if technician_id and technician_id.isdigit():
        query = query.filter(Ticket.technician_id == int(technician_id))

    if start_date:
        query = query.filter(Ticket.date >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Ticket.date <= datetime.strptime(end_date, "%Y-%m-%d"))

    tickets = query.all()
    clients = db.query(Client).options(joinedload(Client.contracts)).all()
    technicians = db.query(Technician).all()
    db.close()

    return templates.TemplateResponse("tickets.html", {
        "request": request,
        "tickets": tickets,
        "clients": clients,
        "technicians": technicians,
        "selected_client_id": int(client_id) if client_id and client_id.isdigit() else None,
        "selected_technician_id": int(technician_id) if technician_id and technician_id.isdigit() else None,
        "selected_start_date": start_date,
        "selected_end_date": end_date
    })



@app.post("/tickets")
def add_ticket(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    technician_id: int = Form(...),
    hours_used: float = Form(...),
    date: str = Form(...),
    contract_id: int = Form(...)
):
    db = SessionLocal()
    ticket_date = datetime.strptime(date, "%Y-%m-%d").date()
    contract = db.query(Contract).filter_by(id=contract_id).first()
    if not contract:
        db.close()
        raise HTTPException(status_code=404, detail="Contract not found")

    new_ticket = Ticket(
        title=title.strip(),
        description=description.strip(),
        hours_used=hours_used,
        date=ticket_date,
        client_id=contract.client_id,
        contract_id=contract_id,
        technician_id=technician_id
    )

    db.add(new_ticket)
    db.commit()
    db.close()
    return RedirectResponse(url="/tickets", status_code=303)

@app.get("/tickets/{ticket_id}/edit", response_class=HTMLResponse)
def edit_ticket_form(request: Request, ticket_id: int):
    db = SessionLocal()
    ticket = db.query(Ticket).options(
        joinedload(Ticket.contract),
        joinedload(Ticket.technician),
        joinedload(Ticket.client)
    ).get(ticket_id)
    clients = db.query(Client).options(joinedload(Client.contracts)).all()
    technicians = db.query(Technician).all()
    db.close()

    if not ticket:
        return HTMLResponse(content="Ticket not found", status_code=404)

    return templates.TemplateResponse("edit_ticket.html", {
        "request": request,
        "ticket": ticket,
        "clients": clients,
        "technicians": technicians
    })

@app.post("/tickets/{ticket_id}/edit")
def update_ticket(
    ticket_id: int,
    title: str = Form(...),
    description: str = Form(...),
    technician_id: int = Form(...),
    hours_used: float = Form(...),
    date: str = Form(...),
    contract_id: int = Form(...)
):
    db = SessionLocal()
    ticket = db.query(Ticket).get(ticket_id)

    if not ticket:
        db.close()
        return HTMLResponse(content="Ticket not found", status_code=404)

    contract = db.query(Contract).filter_by(id=contract_id).first()
    if not contract:
        db.close()
        return HTMLResponse(content="Contract not found", status_code=404)

    ticket.title = title.strip()
    ticket.description = description.strip()
    ticket.hours_used = hours_used
    ticket.date = datetime.strptime(date, "%Y-%m-%d").date()
    ticket.contract_id = contract_id
    ticket.client_id = contract.client_id
    ticket.technician_id = technician_id

    db.commit()
    db.close()
    return RedirectResponse(url="/tickets", status_code=303)

@app.post("/tickets/{ticket_id}/delete")
def delete_ticket(ticket_id: int):
    db = SessionLocal()
    ticket = db.query(Ticket).get(ticket_id)

    if ticket:
        db.delete(ticket)
        db.commit()

    db.close()
    return RedirectResponse(url="/tickets", status_code=303)


@app.get("/technicians", response_class=HTMLResponse)
def view_technicians(request: Request):
    technicians = get_all_technicians()
    return templates.TemplateResponse("technicians.html", {"request": request, "technicians": technicians})

@app.post("/technicians/add")
def add_technician(
    first_name: str = Form(...),
    last_name: str = Form(...)
):
    db = SessionLocal()
    new_tech = Technician(first_name=first_name.strip(), last_name=last_name.strip())
    db.add(new_tech)
    db.commit()
    db.close()
    return RedirectResponse(url="/technicians", status_code=303)

@app.get("/report", response_class=HTMLResponse)
def report(
    request: Request,
    technician_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    contract_id: Optional[str] = Query(None),
    export: Optional[bool] = Query(False)
):
    db = SessionLocal()

    # Technician Report
    technicians = db.query(Technician).all()
    total_hours = None

    if technician_id and technician_id.isdigit():
        query = db.query(func.sum(Ticket.hours_used)).filter(Ticket.technician_id == int(technician_id))
        if start_date:
            query = query.filter(Ticket.date >= datetime.strptime(start_date, "%Y-%m-%d"))
        if end_date:
            query = query.filter(Ticket.date <= datetime.strptime(end_date, "%Y-%m-%d"))
        result = query.scalar()
        total_hours = round(result or 0.0, 2)

    # Block Time Report
    clients = get_all_clients()
    contracts = []
    contract_tickets = []

    if client_id and client_id.isdigit():
        contracts = db.query(Contract).filter(Contract.client_id == int(client_id)).all()

    if contract_id and contract_id.isdigit():
        contract_tickets = db.query(Ticket).options(
            joinedload(Ticket.technician),
            joinedload(Ticket.contract),
            joinedload(Ticket.client)
        ).filter(
            Ticket.contract_id == int(contract_id)
        ).order_by(Ticket.date.asc()).all()

        if export:
            import csv
            from fastapi.responses import StreamingResponse
            from io import StringIO

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["Date", "Title", "Technician", "Hours", "Description"])

            for ticket in contract_tickets:
                writer.writerow([
                    ticket.date.strftime("%Y-%m-%d"),
                    ticket.title,
                    f"{ticket.technician.first_name} {ticket.technician.last_name}" if ticket.technician else "",
                    ticket.hours_used,
                    ticket.description or ""
                ])

            output.seek(0)
            return StreamingResponse(output, media_type="text/csv", headers={
                "Content-Disposition": f"attachment; filename=blocktime_report_contract_{contract_id}.csv"
            })

    db.close()

    return templates.TemplateResponse("report.html", {
        "request": request,
        "technicians": technicians,
        "selected_technician_id": int(technician_id) if technician_id and technician_id.isdigit() else None,
        "selected_start_date": start_date,
        "selected_end_date": end_date,
        "clients": clients,
        "contracts": contracts,
        "contract_tickets": contract_tickets,
        "selected_client_id": int(client_id) if client_id and client_id.isdigit() else None,
        "selected_contract_id": int(contract_id) if contract_id and contract_id.isdigit() else None,
        "total_hours": total_hours
    })
