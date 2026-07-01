# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import base64
from unittest.mock import MagicMock, patch
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestHrJob(TransactionCase):
    """Test cases for Recruitment Twitter."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.job = cls.env["hr.job"].create({
            "name": "Python Developer",
        })

        cls.image_attachment = cls.env["ir.attachment"].create({
            "name": "poster.png",
            "datas": base64.b64encode(b"dummy image"),
            "mimetype": "image/png",
            "type": "binary",
        })

        cls.text_attachment = cls.env["ir.attachment"].create({
            "name": "test.txt",
            "datas": base64.b64encode(b"dummy text"),
            "mimetype": "text/plain",
            "type": "binary",
        })

        cls.config = cls.env["ir.config_parameter"].sudo()

    def _set_api_credentials(self):
        """Configure dummy Twitter credentials."""

        self.config.set_param(
            "recruitment_twitter.consumer_key", "consumer_key"
        )
        self.config.set_param(
            "recruitment_twitter.consumer_secret", "consumer_secret"
        )
        self.config.set_param(
            "recruitment_twitter.access_token", "access_token"
        )
        self.config.set_param(
            "recruitment_twitter.access_token_secret",
            "access_token_secret",
        )

    def test_action_job_post_without_credentials(self):
        """Test posting without API credentials."""

        self.config.set_param("recruitment_twitter.consumer_key", False)
        self.config.set_param("recruitment_twitter.consumer_secret", False)
        self.config.set_param("recruitment_twitter.access_token", False)
        self.config.set_param(
            "recruitment_twitter.access_token_secret", False
        )

        with self.assertRaises(UserError):
            self.job.action_job_post()

    def test_action_job_post_without_attachment(self):
        """Test posting without poster."""

        self._set_api_credentials()
        self.job.attachment_ids = [(5, 0, 0)]

        with self.assertRaises(UserError):
            self.job.action_job_post()

    @patch("tweepy.API")
    @patch("tweepy.OAuth1UserHandler")
    @patch("tweepy.Client")
    def test_action_job_post_success(
        self,
        mock_client,
        mock_auth,
        mock_api,
    ):
        """Test successful Twitter posting."""

        self._set_api_credentials()

        self.job.attachment_ids = [(6, 0, self.image_attachment.ids)]

        self.image_attachment.store_fname = "dummy.png"

        with patch.object(
            type(self.image_attachment),
            "_full_path",
            return_value="/tmp/dummy.png",
        ):
            media = MagicMock()
            media.media_id = 12345

            mock_api.return_value.media_upload.return_value = media

            result = self.job.action_job_post()

            self.assertEqual(result["tag"], "display_notification")
            self.assertEqual(
                result["params"]["type"],
                "success",
            )

    @patch("tweepy.Client")
    def test_action_job_post_authentication_failed(
        self,
        mock_client,
    ):
        """Test authentication failure."""

        self._set_api_credentials()

        self.job.attachment_ids = [(6, 0, self.image_attachment.ids)]

        self.image_attachment.store_fname = "dummy.png"

        with patch.object(
            type(self.image_attachment),
            "_full_path",
            return_value="/tmp/dummy.png",
        ):
            with patch(
                "tweepy.API.media_upload",
                side_effect=Exception("Authentication Failed"),
            ):
                with self.assertRaises(UserError):
                    self.job.action_job_post()

    def test_onchange_attachment_ids_image(self):
        """Test image attachment validation."""

        self.image_attachment.index_content = "image"
        self.job.attachment_ids = [(6, 0, self.image_attachment.ids)]

        self.job._onchange_attachment_ids()

    def test_onchange_attachment_ids_invalid(self):
        """Test non-image attachment validation."""

        self.text_attachment.index_content = "text"

        self.job.attachment_ids = [(6, 0, self.text_attachment.ids)]

        with self.assertRaises(UserError):
            self.job._onchange_attachment_ids()
