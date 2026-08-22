from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import oracledb
from datetime import datetime

app = FastAPI(title="Blood Bank API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── DB Connection ─────────────────────────────────────────────────
from db_config import get_db_connection

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# ─── Pydantic Models ───────────────────────────────────────────────

class StaffLoginRequest(BaseModel):
    staff_id: int
    password: str

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class StaffCreate(BaseModel):
    staff_id: int
    fullname: str
    password: str
    role: str
    hospital_id: Optional[int] = None
    contact: Optional[str] = None

class StaffUpdate(BaseModel):
    fullname: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    hospital_id: Optional[int] = None
    contact: Optional[str] = None

class DonorCreate(BaseModel):
    donor_id: int
    name: str
    blood_group: str
    gender: Optional[str] = None
    contact: str
    city: Optional[str] = None
    fitness_status: Optional[str] = "Fit"
    hospital_id: Optional[int] = None
    staff_id: Optional[int] = None

class DonorUpdate(BaseModel):
    name: Optional[str] = None
    blood_group: Optional[str] = None
    gender: Optional[str] = None
    contact: Optional[str] = None
    city: Optional[str] = None
    fitness_status: Optional[str] = None
    hospital_id: Optional[int] = None

class PatientCreate(BaseModel):
    patient_id: int
    name: str
    blood_group: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    contact: str
    hospital_id: Optional[int] = None
    staff_id: Optional[int] = None

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    blood_group: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    contact: Optional[str] = None
    hospital_id: Optional[int] = None

class BloodBagCreate(BaseModel):
    bag_id: int
    donor_id: int
    blood_group: str
    hospital_id: Optional[int] = None

class BloodTestCreate(BaseModel):
    test_id: int
    bag_id: int
    hb_level: Optional[float] = None
    test_result: str   # Must match Oracle CHECK constraint: 'Passed' or 'Failed'
    remarks: Optional[str] = None
    staff_id: int

class BloodIssuanceCreate(BaseModel):
    issue_id: int
    bag_id: int
    patient_id: int
    hospital_id: Optional[int] = None
    staff_id: int

class HospitalCreate(BaseModel):
    hospital_id: int
    name: str
    address: Optional[str] = None
    contact: Optional[str] = None

class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None

class SystemAdminUpdate(BaseModel):
    fullname: Optional[str] = None
    contact: Optional[str] = None
    password: Optional[str] = None


# ─── helper: build dynamic UPDATE ──────────────────────────────────
def build_update(table: str, pk_col: str, pk_val, data: dict, conn):
    fields, vals = [], []
    for k, v in data.items():
        if v is not None:
            fields.append(f"{k.upper()}=:{len(vals)+1}")
            vals.append(v)
    if not fields:
        raise HTTPException(400, "No fields to update")
    vals.append(pk_val)
    cur = conn.cursor()
    cur.execute(f"UPDATE {table} SET {','.join(fields)} WHERE {pk_col}=:{len(vals)}", vals)
    conn.commit()


# ═══════════════════════════════════════════════════════════════════
# AUTH  — staff login  +  system_admin login (separate endpoints)
# ═══════════════════════════════════════════════════════════════════

@app.post("/auth/login")
def staff_login(req: StaffLoginRequest, conn=Depends(get_db)):
    """Login for regular staff (Technician, Nurse, Receptionist, Admin role in STAFF table)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT STAFF_ID, FULLNAME, ROLE, HOSPITAL_ID, CONTACT FROM STAFF WHERE STAFF_ID=:1 AND PASSWORD=:2",
        (req.staff_id, req.password)
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(401, "Invalid Staff ID or Password")
    return {
        "staff_id": row[0], "fullname": row[1], "role": row[2],
        "hospital_id": row[3], "contact": row[4],
        "user_type": "staff"          # flag so frontend knows what type logged in
    }

@app.post("/auth/admin-login")
def admin_login(req: AdminLoginRequest, conn=Depends(get_db)):
    """Login for system administrators from SYSTEM_ADMIN table."""
    cur = conn.cursor()
    cur.execute(
        "SELECT ADMIN_ID, USERNAME, FULLNAME, CONTACT FROM SYSTEM_ADMIN WHERE USERNAME=:1 AND PASSWORD=:2",
        (req.username, req.password)
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(401, "Invalid username or password")
    # Update LAST_LOGIN
    cur.execute(
        "UPDATE SYSTEM_ADMIN SET LAST_LOGIN=SYSDATE WHERE ADMIN_ID=:1", (row[0],)
    )
    conn.commit()
    return {
        "admin_id": row[0], "username": row[1],
        "fullname": row[2], "contact": row[3],
        "role": "System Admin",
        "user_type": "system_admin"   # flag so frontend shows all menus
    }


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ═══════════════════════════════════════════════════════════════════

@app.get("/stats")
def get_stats(conn=Depends(get_db)):
    cur = conn.cursor()
    def q(sql):
        cur.execute(sql)
        return cur.fetchone()[0]

    stats = {
        "total_donors":    q("SELECT COUNT(*) FROM DONOR"),
        "total_patients":  q("SELECT COUNT(*) FROM PATIENT"),
        "available_bags":  q("SELECT COUNT(*) FROM BLOOD_BAG WHERE STATUS='Available'"),
        "issued_bags":     q("SELECT COUNT(*) FROM BLOOD_BAG WHERE STATUS='Issued'"),
        "expired_bags":    q("SELECT COUNT(*) FROM BLOOD_BAG WHERE EXPIRY_DATE < SYSDATE AND STATUS='Available'"),
        "total_issuances": q("SELECT COUNT(*) FROM BLOOD_ISSUANCE"),
        "total_staff":     q("SELECT COUNT(*) FROM STAFF"),
        "total_hospitals": q("SELECT COUNT(*) FROM HOSPITAL"),
    }
    cur.execute("SELECT BLOOD_GROUP, COUNT(*) FROM BLOOD_BAG WHERE STATUS='Available' GROUP BY BLOOD_GROUP")
    stats["blood_inventory"] = {r[0]: r[1] for r in cur.fetchall()}
    return stats


# ═══════════════════════════════════════════════════════════════════
# HOSPITAL CRUD  (full: GET / POST / PUT / DELETE)
# ═══════════════════════════════════════════════════════════════════

@app.get("/hospitals")
def get_hospitals(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT HOSPITAL_ID, NAME, ADDRESS, CONTACT FROM HOSPITAL ORDER BY HOSPITAL_ID")
    cols = ["hospital_id", "name", "address", "contact"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

@app.post("/hospitals")
def create_hospital(h: HospitalCreate, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO HOSPITAL (HOSPITAL_ID, NAME, ADDRESS, CONTACT) VALUES (:1,:2,:3,:4)",
            (h.hospital_id, h.name, h.address, h.contact)
        )
        conn.commit()
        return {"message": f"Hospital '{h.name}' added successfully"}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.put("/hospitals/{hospital_id}")
def update_hospital(hospital_id: int, h: HospitalUpdate, conn=Depends(get_db)):
    try:
        build_update("HOSPITAL", "HOSPITAL_ID", hospital_id, h.dict(exclude_none=True), conn)
        return {"message": f"Hospital {hospital_id} updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

@app.delete("/hospitals/{hospital_id}")
def delete_hospital(hospital_id: int, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM HOSPITAL WHERE HOSPITAL_ID=:1", (hospital_id,))
        conn.commit()
        return {"message": f"Hospital {hospital_id} deleted"}
    except Exception as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════
# STAFF CRUD
# ═══════════════════════════════════════════════════════════════════

@app.get("/staff")
def get_all_staff(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT STAFF_ID, FULLNAME, ROLE, HOSPITAL_ID, CONTACT FROM STAFF ORDER BY STAFF_ID")
    cols = ["staff_id", "fullname", "role", "hospital_id", "contact"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

@app.post("/staff")
def create_staff(s: StaffCreate, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO STAFF (STAFF_ID, FULLNAME, PASSWORD, ROLE, HOSPITAL_ID, CONTACT) VALUES (:1,:2,:3,:4,:5,:6)",
            (s.staff_id, s.fullname, s.password, s.role, s.hospital_id, s.contact)
        )
        conn.commit()
        return {"message": "Staff created successfully"}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.put("/staff/{staff_id}")
def update_staff(staff_id: int, s: StaffUpdate, conn=Depends(get_db)):
    try:
        build_update("STAFF", "STAFF_ID", staff_id, s.dict(exclude_none=True), conn)
        return {"message": "Staff updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

@app.delete("/staff/{staff_id}")
def delete_staff(staff_id: int, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM STAFF WHERE STAFF_ID=:1", (staff_id,))
        conn.commit()
        return {"message": "Staff deleted"}
    except Exception as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════
# SYSTEM ADMIN — view & update their own record (no hardcoding)
# ═══════════════════════════════════════════════════════════════════

@app.get("/system-admins")
def get_system_admins(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT ADMIN_ID, USERNAME, FULLNAME, CONTACT, LAST_LOGIN FROM SYSTEM_ADMIN ORDER BY ADMIN_ID")
    cols = ["admin_id", "username", "fullname", "contact", "last_login"]
    rows = []
    for row in cur.fetchall():
        r = dict(zip(cols, row))
        r["last_login"] = str(r["last_login"])[:19] if r["last_login"] else "Never"
        rows.append(r)
    return rows

@app.put("/system-admins/{admin_id}")
def update_system_admin(admin_id: int, body: SystemAdminUpdate, conn=Depends(get_db)):
    try:
        build_update("SYSTEM_ADMIN", "ADMIN_ID", admin_id, body.dict(exclude_none=True), conn)
        return {"message": "System admin updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════
# DONOR CRUD
# ═══════════════════════════════════════════════════════════════════

@app.get("/donors")
def get_donors(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("""
        SELECT DONOR_ID, NAME, BLOOD_GROUP, GENDER, CONTACT, CITY, FITNESS_STATUS, HOSPITAL_ID
        FROM DONOR ORDER BY DONOR_ID
    """)
    cols = ["donor_id", "name", "blood_group", "gender", "contact", "city", "fitness_status", "hospital_id"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

@app.post("/donors")
def create_donor(d: DonorCreate, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO DONOR (DONOR_ID,NAME,BLOOD_GROUP,GENDER,CONTACT,CITY,FITNESS_STATUS,HOSPITAL_ID,STAFF_ID) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9)",
            (d.donor_id, d.name, d.blood_group, d.gender, d.contact, d.city, d.fitness_status, d.hospital_id, d.staff_id)
        )
        conn.commit()
        return {"message": "Donor registered successfully"}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.put("/donors/{donor_id}")
def update_donor(donor_id: int, d: DonorUpdate, conn=Depends(get_db)):
    try:
        build_update("DONOR", "DONOR_ID", donor_id, d.dict(exclude_none=True), conn)
        return {"message": "Donor updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

@app.delete("/donors/{donor_id}")
def delete_donor(donor_id: int, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM DONOR WHERE DONOR_ID=:1", (donor_id,))
        conn.commit()
        return {"message": "Donor deleted"}
    except Exception as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════
# PATIENT CRUD
# ═══════════════════════════════════════════════════════════════════

@app.get("/patients")
def get_patients(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT PATIENT_ID, NAME, BLOOD_GROUP, GENDER, CONTACT, HOSPITAL_ID FROM PATIENT ORDER BY PATIENT_ID")
    cols = ["patient_id", "name", "blood_group", "gender", "contact", "hospital_id"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

@app.post("/patients")
def create_patient(p: PatientCreate, conn=Depends(get_db)):
    try:
        dob = datetime.strptime(p.date_of_birth, "%Y-%m-%d").date() if p.date_of_birth else None
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO PATIENT (PATIENT_ID,NAME,BLOOD_GROUP,DATE_OF_BIRTH,GENDER,CONTACT,HOSPITAL_ID,STAFF_ID) VALUES (:1,:2,:3,:4,:5,:6,:7,:8)",
            (p.patient_id, p.name, p.blood_group, dob, p.gender, p.contact, p.hospital_id, p.staff_id)
        )
        conn.commit()
        return {"message": "Patient registered"}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.put("/patients/{patient_id}")
def update_patient(patient_id: int, p: PatientUpdate, conn=Depends(get_db)):
    try:
        build_update("PATIENT", "PATIENT_ID", patient_id, p.dict(exclude_none=True), conn)
        return {"message": "Patient updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM PATIENT WHERE PATIENT_ID=:1", (patient_id,))
        conn.commit()
        return {"message": "Patient deleted"}
    except Exception as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════
# BLOOD BAG CRUD
# ═══════════════════════════════════════════════════════════════════

@app.get("/blood-bags")
def get_blood_bags(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("""
        SELECT b.BAG_ID, b.DONOR_ID, d.NAME, b.BLOOD_GROUP,
               b.COLLECTION_DATE, b.EXPIRY_DATE, b.STATUS, b.HOSPITAL_ID
        FROM BLOOD_BAG b LEFT JOIN DONOR d ON b.DONOR_ID = d.DONOR_ID
        ORDER BY b.BAG_ID
    """)
    cols = ["bag_id", "donor_id", "donor_name", "blood_group",
            "collection_date", "expiry_date", "status", "hospital_id"]
    rows = []
    for row in cur.fetchall():
        r = dict(zip(cols, row))
        r["collection_date"] = str(r["collection_date"])[:10] if r["collection_date"] else None
        r["expiry_date"]     = str(r["expiry_date"])[:10]     if r["expiry_date"]     else None
        rows.append(r)
    return rows

@app.get("/blood-bags/donor/{donor_id}/eligibility")
def check_donor_eligibility(donor_id: int, conn=Depends(get_db)):
    """
    Returns donation eligibility info for a donor:
    - fitness_status must be 'Fit'
    - Must not have donated within the last 56 days (standard safe interval)
    - Max 3 active (non-issued) bags allowed per donor in inventory at one time
    """
    cur = conn.cursor()

    # Get donor fitness status
    cur.execute("SELECT FITNESS_STATUS, NAME FROM DONOR WHERE DONOR_ID=:1", (donor_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, f"Donor {donor_id} not found")
    fitness, donor_name = row[0], row[1]

    # Most recent donation date
    cur.execute("""
        SELECT MAX(COLLECTION_DATE) FROM BLOOD_BAG WHERE DONOR_ID=:1
    """, (donor_id,))
    last_row = cur.fetchone()
    last_date = last_row[0] if last_row else None

    # Count active (Available) bags currently in inventory for this donor
    cur.execute("""
        SELECT COUNT(*) FROM BLOOD_BAG
        WHERE DONOR_ID=:1 AND STATUS='Available'
    """, (donor_id,))
    active_bags = cur.fetchone()[0]

    # Total bags ever donated
    cur.execute("SELECT COUNT(*) FROM BLOOD_BAG WHERE DONOR_ID=:1", (donor_id,))
    total_bags = cur.fetchone()[0]

    from datetime import date as dt_date, timedelta
    today = dt_date.today()

    days_since = None
    next_eligible = None
    can_donate_by_date = True

    if last_date:
        last_date_only = last_date.date() if hasattr(last_date, 'date') else last_date
        days_since = (today - last_date_only).days
        if days_since < 56:
            can_donate_by_date = False
            next_eligible = str(last_date_only + timedelta(days=56))

    # Business rules
    eligible = True
    reasons = []

    if fitness == "Unfit":
        eligible = False
        reasons.append("Donor is marked UNFIT for donation")
    elif fitness == "Deferred":
        eligible = False
        reasons.append("Donor is DEFERRED — temporarily unable to donate")

    if not can_donate_by_date:
        eligible = False
        reasons.append(f"Last donation was {days_since} days ago. Must wait until {next_eligible} (56-day rule)")

    if active_bags >= 3:
        eligible = False
        reasons.append(f"Donor already has {active_bags} unsettled bags in inventory (max 3 active at a time)")

    return {
        "donor_id":    donor_id,
        "donor_name":  donor_name,
        "fitness":     fitness,
        "eligible":    eligible,
        "reasons":     reasons,
        "last_donation": str(last_date)[:10] if last_date else None,
        "days_since_last": days_since,
        "next_eligible_date": next_eligible,
        "active_bags_in_inventory": active_bags,
        "total_donations": total_bags,
    }

@app.post("/blood-bags")
def create_blood_bag(b: BloodBagCreate, conn=Depends(get_db)):
    cur = conn.cursor()

    # ── 1. Check donor fitness status ──────────────────────────────
    cur.execute("SELECT FITNESS_STATUS, NAME FROM DONOR WHERE DONOR_ID=:1", (b.donor_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(400, f"Donor ID {b.donor_id} not found in database")
    fitness, donor_name = row[0], row[1]

    if fitness == "Unfit":
        raise HTTPException(400, f"Cannot add bag: Donor '{donor_name}' is marked UNFIT for donation.")
    if fitness == "Deferred":
        raise HTTPException(400, f"Cannot add bag: Donor '{donor_name}' is DEFERRED — temporarily unable to donate.")

    # ── 2. Enforce 56-day donation interval ────────────────────────
    cur.execute("SELECT MAX(COLLECTION_DATE) FROM BLOOD_BAG WHERE DONOR_ID=:1", (b.donor_id,))
    last_row = cur.fetchone()
    last_date = last_row[0] if last_row else None

    if last_date:
        from datetime import date as dt_date, timedelta
        last_date_only = last_date.date() if hasattr(last_date, 'date') else last_date
        days_since = (dt_date.today() - last_date_only).days
        if days_since < 56:
            next_ok = str(last_date_only + timedelta(days=56))
            raise HTTPException(
                400,
                f"Cannot add bag: Donor '{donor_name}' last donated {days_since} days ago. "
                f"Minimum safe interval is 56 days. Next eligible date: {next_ok}."
            )

    # ── 3. Max 3 active (Available) bags per donor in inventory ────
    cur.execute(
        "SELECT COUNT(*) FROM BLOOD_BAG WHERE DONOR_ID=:1 AND STATUS='Available'",
        (b.donor_id,)
    )
    active_bags = cur.fetchone()[0]
    if active_bags >= 3:
        raise HTTPException(
            400,
            f"Cannot add bag: Donor '{donor_name}' already has {active_bags} unsettled "
            f"bags in inventory. Max 3 active bags allowed per donor at any time."
        )

    # ── 4. All checks passed — insert ──────────────────────────────
    try:
        cur.execute(
            "INSERT INTO BLOOD_BAG (BAG_ID, DONOR_ID, BLOOD_GROUP, HOSPITAL_ID) VALUES (:1,:2,:3,:4)",
            (b.bag_id, b.donor_id, b.blood_group, b.hospital_id)
        )
        conn.commit()
        return {
            "message": f"Blood bag {b.bag_id} added for donor '{donor_name}'. "
                       f"They now have {active_bags + 1} active bag(s) in inventory."
        }
    except oracledb.Error as e:
        raise HTTPException(400, str(e))

@app.delete("/blood-bags/{bag_id}")
def delete_blood_bag(bag_id: int, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM BLOOD_BAG WHERE BAG_ID=:1", (bag_id,))
        conn.commit()
        return {"message": "Blood bag deleted"}
    except Exception as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════
# BLOOD TEST CRUD
# ═══════════════════════════════════════════════════════════════════

@app.get("/blood-tests")
def get_blood_tests(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("""
        SELECT t.TEST_ID, t.BAG_ID, b.BLOOD_GROUP, t.TEST_DATE,
               t.HB_LEVEL, t.TEST_RESULT, t.REMARKS, t.STAFF_ID
        FROM BLOOD_TEST t LEFT JOIN BLOOD_BAG b ON t.BAG_ID = b.BAG_ID
        ORDER BY t.TEST_ID
    """)
    cols = ["test_id", "bag_id", "blood_group", "test_date",
            "hb_level", "test_result", "remarks", "staff_id"]
    rows = []
    for row in cur.fetchall():
        r = dict(zip(cols, row))
        r["test_date"] = str(r["test_date"])[:10] if r["test_date"] else None
        rows.append(r)
    return rows

@app.post("/blood-tests")
def create_blood_test(t: BloodTestCreate, conn=Depends(get_db)):
    # Validate test_result matches Oracle CHECK constraint before hitting DB
    valid_results = {"Passed", "Failed", "Pass", "Fail"}
    if t.test_result not in valid_results:
        raise HTTPException(
            400,
            f"test_result must be 'Passed' or 'Failed'. Got: '{t.test_result}'. "
            f"Check your Oracle BLOOD_TEST table CHECK constraint."
        )
    # Normalise to whatever your DB constraint actually expects
    # (your existing data shows 'Passed' so we keep it as-is)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO BLOOD_TEST (TEST_ID,BAG_ID,TEST_DATE,HB_LEVEL,TEST_RESULT,REMARKS,STAFF_ID) VALUES (:1,:2,SYSDATE,:3,:4,:5,:6)",
            (t.test_id, t.bag_id, t.hb_level, t.test_result, t.remarks, t.staff_id)
        )
        conn.commit()
        return {"message": "Blood test recorded"}
    except oracledb.Error as e:
        err = str(e)
        if "ORA-02290" in err:
            raise HTTPException(
                400,
                f"Oracle CHECK constraint violation: your BLOOD_TEST table only allows specific "
                f"values for TEST_RESULT. Current value sent: '{t.test_result}'. "
                f"Run 'SELECT CONSTRAINT_NAME, SEARCH_CONDITION FROM USER_CONSTRAINTS "
                f"WHERE TABLE_NAME=''BLOOD_TEST''' in SQL Developer to see the allowed values."
            )
        raise HTTPException(400, err)

@app.delete("/blood-tests/{test_id}")
def delete_blood_test(test_id: int, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM BLOOD_TEST WHERE TEST_ID=:1", (test_id,))
        conn.commit()
        return {"message": "Test record deleted"}
    except Exception as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════
# BLOOD ISSUANCE
# ═══════════════════════════════════════════════════════════════════

@app.get("/issuances")
def get_issuances(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("""
        SELECT i.ISSUE_ID, i.BAG_ID, b.BLOOD_GROUP, i.PATIENT_ID, p.NAME,
               i.HOSPITAL_ID, i.STAFF_ID, i.ISSUE_DATE, i.STATUS
        FROM BLOOD_ISSUANCE i
        LEFT JOIN BLOOD_BAG b ON i.BAG_ID = b.BAG_ID
        LEFT JOIN PATIENT   p ON i.PATIENT_ID = p.PATIENT_ID
        ORDER BY i.ISSUE_ID
    """)
    cols = ["issue_id","bag_id","blood_group","patient_id","patient_name",
            "hospital_id","staff_id","issue_date","status"]
    rows = []
    for row in cur.fetchall():
        r = dict(zip(cols, row))
        r["issue_date"] = str(r["issue_date"])[:10] if r["issue_date"] else None
        rows.append(r)
    return rows

@app.post("/issuances")
def create_issuance(i: BloodIssuanceCreate, conn=Depends(get_db)):
    """
    Oracle trigger trg_check_blood_issuance_safety fires BEFORE INSERT.
    If it raises ORA-20xxx the error surfaces here with the custom message.
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO BLOOD_ISSUANCE (ISSUE_ID,BAG_ID,PATIENT_ID,HOSPITAL_ID,STAFF_ID,ISSUE_DATE) VALUES (:1,:2,:3,:4,:5,SYSDATE)",
            (i.issue_id, i.bag_id, i.patient_id, i.hospital_id, i.staff_id)
        )
        conn.commit()
        return {"message": "Blood issued successfully"}
    except oracledb.Error as e:
        err = str(e)
        # Pull out the human-readable part of the trigger message
        if "ORA-20" in err:
            try:
                msg = err.split("ORA-20")[1]          # e.g. "006: SAFETY ABORT..."
                msg = msg.split(":")[1].split("\n")[0].strip()
            except Exception:
                msg = err
            raise HTTPException(400, f"🚫 {msg}")
        raise HTTPException(400, err)

@app.delete("/issuances/{issue_id}")
def delete_issuance(issue_id: int, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM BLOOD_ISSUANCE WHERE ISSUE_ID=:1", (issue_id,))
        conn.commit()
        return {"message": "Issuance record deleted"}
    except Exception as e:
        raise HTTPException(400, str(e))