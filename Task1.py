
from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
from datetime import date,datetime, timezone
from typing import Optional
from pymongo import MongoClient
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
import os


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
 client = MongoClient("mongodb://localhost:27017/")
 print("Connected successfully")
except:
   print("Connection error")

db= client["Candidates"]
User=db["User"]
Issue= db["Issue"]
app=FastAPI()
router=APIRouter()


def mail(to:str, sub:str, message:str):
   sender_add="aadhithya120906@gmail.com"
   app_pass=os.getenv("GMAIL_APP_PASSWORD")

   msg= MIMEMultipart()
   msg["From"]=sender_add
   msg["To"]=to
   msg["Subject"]=sub

   msg.attach(MIMEText(message, "plain"))
   with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
      server.login(sender_add, app_pass)
      server.send_message(msg)


class Issue_model(BaseModel):
    uuid: str
    selected_date: date
    reason: str
    comment: Optional[str]=None



@app.get("/")
def root():
     return{"message":"API running"}


@app.get("/issues")
def get_issues():
    data = list(Issue.find({}, {"_id": 0}))
    if not data:
       return{"Message":"No issues found"}
    return data


@app.get("/candidates")
def get_candidates():
    data = list(User.find({}, {"_id": 0}))
    if not data:
       return{"Message":"No Users found"}
    return data


@app.post("/Reschedule-form")
def reschedule(issue: Issue_model):
    try:
       user=User.find_one({"uuid":issue.uuid})
       if not user:
          raise HTTPException(status_code=404, detail="Candidate data not found")
       if issue.selected_date< date.today() :
          raise HTTPException(status_code=400, detail="Invalid date")
       else:
          Issue.insert_one( {
             "uuid": issue.uuid,
             "selected_date": issue.selected_date.isoformat(),
             "reason": issue.reason,
             "comment": issue.comment,
             "status": "waiting"
          })
          logger.info(f"{user} wants to reschedule their assessment")
          return {
             "uuid": issue.uuid,
             "selected_date": issue.selected_date.isoformat(),
             "reason": issue.reason,
             "comment": issue.comment,
             "status": "waiting"
          }
       
    except Exception as e:
        logger.error(f"Error fetching candidate details ({user}): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching candidate details for reschedule form"
        )

class RescheduleValidation(BaseModel):
   uuid:str
   approval:bool
   admin_comment:Optional[str]=None

@app.post("/Reschedule-form-validation")
def reschedule_validate(data:RescheduleValidation):
    try:
        user=User.find_one({"uuid":data.uuid})
        if not user:
            logger.error(f"Candidate {data.uuid} not found")
            raise HTTPException(status_code=404, detail="Candidate not found")
        issue=Issue.find_one({"uuid":data.uuid})
        if not issue:
            logger.error(f"Request of {data.uuid} not found")
            raise HTTPException(status_code=404, detail="Reschedule request not found")
        if data.approval:
            logger.info("Data updation for approval of requested rescheduling")
            Issue.update_one({"uuid":data.uuid},
                            {"$set":{
                               "status":"Approved",
                            }})
            User.update_one({"uuid":data.uuid},
                            {"$set":{
                               "Interview_date": datetime.fromisoformat(issue["selected_date"]),
                               "status":"Rescheduled",
                               "Reschedule_approved_date": datetime.now(),
                               "admin_comment": data.admin_comment
                            }})
            return({
               "uuid":data.uuid,
               "approval":data.approval,
               "admin_comment":data.admin_comment
                    })
    except Exception as e:
        logger.error(f"Validation error ({data.uuid}): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error validating rescheduling request"
        )

    
''' 
      candidate_email=user["email"]
          mail(to=candidate_email, sub="Interview Rescheduled", message=f"""
               Hello {user['candidate']},
               Your interview has been rescheduled to {issue.selected_date}.
               Reason: {issue.reason}
               Regards,
               HR Team"""
          )
          return {"message":"Email sent successfully"}
          
    except Exception as e:
       return {"error":str(e)} '''
       
   
       
