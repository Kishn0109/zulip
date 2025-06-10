from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _

from zerver.actions.user_settings import do_change_avatar_fields
from zerver.lib.avatar import avatar_url
from zerver.lib.exceptions import JsonableError
from zerver.lib.response import json_success
from zerver.lib.upload import upload_avatar_image
from zerver.models import UserProfile
from zerver.decorator import authenticated_json_view, require_realm_admin

@authenticated_json_view
@require_realm_admin
def update_user_avatar_backend(request: HttpRequest, user_profile: UserProfile, target_user_id: int) -> HttpResponse:
    """Update avatar for a user. Only administrators can update other users' avatars."""
    # Get the target user
    target_user = UserProfile.objects.filter(id=target_user_id, realm=user_profile.realm).first()
    if target_user is None:
        raise JsonableError(_("No such user"))

    if len(request.FILES) != 1:
        raise JsonableError(_("You must upload exactly one avatar."))

    [user_file] = request.FILES.values()
    
    # Upload and process avatar image
    upload_avatar_image(user_file, target_user)
    do_change_avatar_fields(target_user, UserProfile.AVATAR_FROM_USER, acting_user=user_profile)

    # Return the new avatar URL
    user_avatar_url = avatar_url(target_user)
    
    return json_success(request, data={"avatar_url": user_avatar_url}) 