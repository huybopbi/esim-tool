def format_user_id_response(user, admin_ids) -> str:
    """Build /myid response without leaking admin configuration to normal users."""
    is_admin = user.id in admin_ids

    response = "🆔 **THÔNG TIN USER**\n\n"
    response += f"**User ID:** `{user.id}`\n"
    response += f"**Username:** @{user.username}\n"
    response += f"**First Name:** {user.first_name}\n"
    if user.last_name:
        response += f"**Last Name:** {user.last_name}\n"

    if is_admin:
        response += f"\n**Admin IDs configured:** `{admin_ids}`\n"

    response += f"**Is Admin:** {'✅ Yes' if is_admin else '❌ No'}\n\n"
    response += "Copy User ID trên để cấu hình admin trong file config.py"
    return response
