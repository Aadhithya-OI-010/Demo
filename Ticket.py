from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
from datetime import date,datetime, timezone
from typing import Optional
from pymongo import MongoClient
from enum import Enum
import uuid
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
 client = MongoClient("mongodb://localhost:27017/")
 print("Connected successfully")
except:
   print("Connection error")

db= client["Candidates"]
Tickets=db["Tickets"]
User=db["User"]
Tickets.create_index("tktID", unique=True)
app=FastAPI()


class Ticket_priority(str, Enum):
   low="Low"
   medium="Medium"
   high="High"
   critical="Critical"

class Ticket_category(str, Enum):
   CreatePosition="Create Position"
   ViewPositionDetails="View Position Details"
   EditPosition="Edit Position"
   ViewCandidateDetails="View Candidate Details"
   ApproveCandidate="Approve Candidate"
   DeleteCandidate="Delete Candidate"
   InviteCandidate="Invite Candidate"
   ImportCSVtoAddCandidate="Import CSV to Add Candidate"
   AddCandidate="Add Candidate"
   RescheduleInterview="Reschedule Interview"
   ViewReports="View Reports"
   DownloadReports="Download Reports" 
   DownloadCSVReports="Download CSV Reports"
   JDStudio="JD Studio"
   
class Ticket_status(str, Enum):
   open="Open"
   inProgress="In Progress"
   pending="Pending"
   resolved="Resolved"
   closed="Closed"


class Ticket_model(BaseModel):
  uuid: str
  title: str
  requested_date: date
  description: str
  comment: Optional[str]=None
  priority: Ticket_priority
  category: Ticket_category


@app.get("/")
def root():
     return{"message":"API running"}

@app.get("/candidates")
def get_candidates():
    data = list(User.find({}, {"_id": 0}))
    if not data:
       return{"Message":"No Users found"}
    return data

@app.get("/get_tickets")
def get_tickets():
    data = list(Tickets.find({}, {"_id": 0}))
    if not data:
       return{"Message":"No issues found"}
    return data


@app.get("/tickets/count/category")
def count_by_category():
    result = Tickets.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ])

    existing = {item["_id"]: item["count"] for item in result}

    return {
        category.value: existing.get(category.value, 0)
        for category in Ticket_category
    }


@app.get("/tickets/count/status")
def count_by_status():
    result = Tickets.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ])

    existing = {item["_id"]: item["count"] for item in result}

    return {
        status.value: existing.get(status.value, 0)
        for status in Ticket_status
    }

@app.get("/tickets/count/priority")
def count_by_priority():
    result = Tickets.aggregate([
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
    ])

    existing = {item["_id"]: item["count"] for item in result}

    return {
        priority.value: existing.get(priority.value, 0)
        for priority in Ticket_priority
    }
   

@app.post("/create_ticket")
def create_ticket(details: Ticket_model):
    try:
        user=User.find_one({"uuid":details.uuid})
        if not user:
          raise HTTPException(status_code=404, detail="Candidate data not found")
        if details.requested_date< date.today() :
          raise HTTPException(status_code=400, detail="Invalid date")
        else:
          ticket_id=f"TKT-{uuid.uuid4().hex[:8]}"
          logger.info("Inserting new ticket details")
          Tickets.insert_one({
             "tktID": ticket_id,
             "title":details.title,
             "description": details.description,
             "requested_date":details.requested_date.isoformat(),

             "priority":details.priority.value,
             "category":details.category.value,

             "status": Ticket_status.open.value,  

             "requester": {"name":user["candidate"],
                           "uuid":details.uuid},

             "assignee": {"name":"xyz"},

             "comment":details.comment,   
          
             "created_at": datetime.now(timezone.utc),
             "updated_at": None,
             "validated_at":None,
             "validated_by":None,
             "admin_comment": None,

          })
        return {
            "message": "Ticket created successfully",
            "ticket_id": ticket_id
            }
    except Exception as e:
        logger.error(f"Ticket creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating ticket")
    
class Ticket_update(BaseModel):
   status: Ticket_status
   admin_comment: Optional[str]=None

@app.patch("/tickets/{tktID}/status")
def update_ticket_status(tktID: str, data:Ticket_update):
    try:
       ticket=Tickets.find_one({"tktID":tktID})
       if not ticket:
          logger.error("Wrong tktID input")
          raise HTTPException(status_code=404, detail="Ticket not found")
       
       updated_fields={
             "status":data.status.value,
             "updated_at": datetime.now(timezone.utc),
             "validated_at":datetime.now(timezone.utc),
             "validated_by":"admin",
       }
       if data.admin_comment:
          updated_fields["admin_comment"]= data.admin_comment

       Tickets.update_one(
          {"tktID":tktID},
          {"$set": updated_fields}
       )
       logger.info("Status Updated by Admin")

       return{
          "message": f"Ticket {tktID} updated successfully",
          "status": data.status.value
       }
    
    except HTTPException:
       raise
    except Exception as e:
       logger.error(f"Status update error ({tktID}): {str(e)}")
       raise HTTPException(status_code=500, detail="Failed to update ticket status")