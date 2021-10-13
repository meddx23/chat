import frappe
from frappe import _
from frappe.utils import has_common
import datetime


def time_in_range(start, end, current):
    """Check if current time is between start and end time"""
    return start <= current <= end


def validate_token(token):
    """Validate the guest token

    Args:
        token (str): Guest token

    Returns:
        list: A list specifying whether token is valid and necessary info.
    """
    if not token:
        return [False, {}]
    is_exist = frappe.db.exists({
        'doctype': 'Chat Profile',
        'token': token,
    })

    if not is_exist:
        return [False, {}]

    guest_user = frappe.get_doc('Chat Profile', str(is_exist[0][0]))

    if guest_user.ip_address != frappe.local.request_ip:
        return [False, {}]

    room = frappe.db.get_value(
        'Chat Room', {'guest': guest_user.email}, ['name'])

    guest_details = {
        'email': guest_user.email,
        'room': room,
    }
    return [True, guest_details]


def get_admin_name(user_key):
    """Get the admin name for specified user key"""
    full_name = frappe.db.get_value('User', user_key, 'full_name')
    return full_name


def update_room(room, last_message=None, is_read=0, update_modified=True):
    """Update the value of chat room doctype with latest real time values

    Args:
        room (str): [description]
        last_message (str, optional): Last message of a room. Defaults to None.
        is_read (int, optional): Whether last message is read or not. Defaults to 0.
        update_modified (bool, optional): Whether to update or not. Defaults to True.
    """
    new_values = {
        'is_read': is_read,
    }
    if last_message:
        new_values['last_message'] = last_message

    frappe.db.set_value('Chat Room', room, new_values,
                        update_modified=update_modified)


def get_chat_settings():
    """Get the chat settings
    Returns:
        dict: Dictionary containing chat settings.
    """
    chat_settings = frappe.get_single('Chat Settings')
    user_roles = frappe.get_roles()

    allowed_roles = [u.role for u in chat_settings.allowed_roles]
    allowed_roles.extend(['System Manager', 'Administrator', 'Guest'])
    result = {
        'enable_chat': False
    }

    if not chat_settings.enable_chat or not has_common(allowed_roles, user_roles):
        return result

    if chat_settings.start_time and chat_settings.end_time:
        start_time = datetime.time.fromisoformat(chat_settings.start_time)
        end_time = datetime.time.fromisoformat(chat_settings.end_time)
        current_time = datetime.datetime.now().time()

        chat_status = 'Online' if time_in_range(
            start_time, end_time, current_time) else 'Offline'
    else:
        chat_status = 'Online'

    result['enable_chat'] = True
    result['chat_status'] = chat_status
    return result


def display_warning():
    """Display deprecated warning message_item
    """
    message = 'The chat application in frappe is deprecated and will be removed in the future release. So please use this one only.'

    frappe.publish_realtime(
        event='msgprint', message=message)


def allow_guest_to_upload():
    """Allow guest to upload files
    """
    system_settings = frappe.get_doc('System Settings')
    system_settings.allow_guests_to_upload_files = 1
    system_settings.save()


def get_full_name(email, only_first=False):
    """Get full name from email

    Args:
        email (str): Email of user
        only_first (bool, optional): Whether to fetch only first name. Defaults to False.

    Returns:
        str: Full Name
    """
    field = 'first_name' if only_first else 'full_name'
    return frappe.db.get_value(
        'User', email, field)
