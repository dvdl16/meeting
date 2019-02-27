import frappe
from frappe import _
from frappe.utils import nowdate, add_days


@frappe.whitelist()
def get_meetings(start, end):
    if not frappe.has_permission("Meeting", "read"):
        raise frappe.PermissionError

    return frappe.db.sql("""select
            timestamp(`date`, from_time) as start,
            timestamp(`date`, to_time) as end,
            name,
            title,
            status,
            0 as all_day
        from `tabMeeting`
        where `date` between %(start)s and %(end)s""", {
            "start": start,
            "end": end
        }, as_dict=True)


@frappe.whitelist()
def send_invitation_emails(meeting):
    meeting = frappe.get_doc("Meeting", meeting)
    meeting.check_permission("email")

    if meeting.status == "Planned":
        frappe.sendmail(
            recipients=[d.attendee for d in meeting.attendees],
            sender=frappe.session.user,
            subject=meeting.title,
            message=meeting.invitation_message,
            reference_doctype=meeting.doctype,
            reference_name=meeting.name,
            as_bulk=True
        )
        meeting.status = "Invitation Sent"
        meeting.save()
        frappe.msgprint(_("Invitation Sent"))

    else:
        frappe.msgprint(_("Meeting Status must be 'Planned'"))


def make_orientation_meeting(doc, method):
    """Create an orientation meeting when a new User is added"""
    #you can also create a new doc with the get_doc function
    meeting = frappe.get_doc({
        "doctype": "Meeting",
        "title": "Orientation for {0}".format(doc.first_name),
        "date": add_days(nowdate(), 1),
        "from_time": "09:00",
        "to_time": "09:30",
        "attendees": [{
            "attendee": doc.name
        }]
    })
    #the System Manager might not have permissions to create meetings
    meeting.flags.ignore_permissions = True
    meeting.insert()

    frappe.msgprint(_("Orientation meeting created"))
