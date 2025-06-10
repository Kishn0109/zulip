from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils.timezone import now

from zerver.lib.test_classes import ZulipTestCase
from zerver.lib.test_helpers import get_test_image_file
from zerver.lib.upload import upload_avatar_image
from zerver.models import UserProfile

class AdminUserAvatarTest(ZulipTestCase):
    def test_admin_upload_user_avatar(self) -> None:
        """Test that administrators can upload avatars for other users."""
        # Log in as an admin
        self.login("iago")
        
        # Get the target user (Hamlet)
        target_user = self.example_user("hamlet")
        original_avatar_version = target_user.avatar_version
        
        # Upload avatar
        with get_test_image_file("img.png") as fp:
            result = self.client_patch(
                f"/json/users/{target_user.id}/avatar",
                {"file": fp},
            )
        
        self.assert_json_success(result)
        self.assertIn("avatar_url", result.json()["data"])
        
        # Verify avatar was updated
        target_user.refresh_from_db()
        self.assertEqual(target_user.avatar_version, original_avatar_version + 1)
        self.assertEqual(target_user.avatar_source, UserProfile.AVATAR_FROM_USER)

    def test_non_admin_cannot_upload_other_avatar(self) -> None:
        """Test that non-administrators cannot upload avatars for other users."""
        # Log in as a non-admin user
        self.login("hamlet")
        
        # Try to update Cordelia's avatar
        target_user = self.example_user("cordelia")
        
        with get_test_image_file("img.png") as fp:
            result = self.client_patch(
                f"/json/users/{target_user.id}/avatar",
                {"file": fp},
            )
        
        self.assert_json_error(result, "Must be an administrator")
        
        # Verify avatar was not updated
        target_user.refresh_from_db()
        self.assertEqual(target_user.avatar_source, UserProfile.AVATAR_FROM_GRAVATAR)

    def test_admin_upload_invalid_user(self) -> None:
        """Test uploading avatar for non-existent user."""
        self.login("iago")
        
        invalid_user_id = 999999
        
        with get_test_image_file("img.png") as fp:
            result = self.client_patch(
                f"/json/users/{invalid_user_id}/avatar",
                {"file": fp},
            )
        
        self.assert_json_error(result, "No such user")

    def test_admin_upload_multiple_files(self) -> None:
        """Test that uploading multiple files is not allowed."""
        self.login("iago")
        
        target_user = self.example_user("hamlet")
        
        with get_test_image_file("img.png") as fp1, get_test_image_file("img.gif") as fp2:
            result = self.client_patch(
                f"/json/users/{target_user.id}/avatar",
                {"file1": fp1, "file2": fp2},
            )
        
        self.assert_json_error(result, "You must upload exactly one avatar.") 