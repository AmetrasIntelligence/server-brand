# Copyright 2020-2023 Onestein (<http://www.onestein.eu>)
# Copyright 2020 Akretion (<http://www.akretion.com>)
# Copyright 2023 Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from lxml import etree

from odoo.tests import common


class TestRemoveOdooEnterprise(common.TransactionCase):
    def test_res_config_settings(self):
        conf = self.env["res.config.settings"].create({})
        view = conf.get_views([[False, "form"]])["views"]["form"]
        doc = etree.XML(view["arch"])

        query = "//div[div[field[@widget='upgrade_boolean']]]"
        for item in doc.xpath(query):
            self.assertIn("d-none", item.attrib["class"])

    def test_is_base_config_settings_view(self):
        """Test the _is_base_config_settings_view method"""
        conf = self.env["res.config.settings"].create({})

        # Test with base settings view
        view_result = conf.get_views([[False, "form"]])
        self.assertTrue(conf._is_base_config_settings_view(view_result))

        # Test with a different view
        # Create a mock view result with a different view ID
        mock_view = self.env["ir.ui.view"].create(
            {
                "name": "test_view",
                "model": "res.config.settings",
                "arch": "<form/>",
            }
        )
        mock_view_result = {
            "views": {
                "form": {
                    "id": mock_view.id,
                    "arch": "<form/>",
                }
            }
        }
        self.assertFalse(conf._is_base_config_settings_view(mock_view_result))

    def test_hide_empty_containers(self):
        """Test the _hide_empty_containers method"""
        conf = self.env["res.config.settings"].create({})

        # Create a test XML document with empty containers
        xml_content = """
        <form>
            <h2>Heading 1</h2>
            <div class="o_settings_container">
                <div class="o_setting_box d-none">Hidden setting box</div>
            </div>
            <h2>Heading 2</h2>
            <div class="o_settings_container">
                <div class="o_setting_box">Visible setting box</div>
            </div>
            <div class="o_settings_container">
                <div class="o_setting_box d-none">Another hidden setting box</div>
            </div>
        </form>
        """
        doc = etree.XML(xml_content)

        # Apply the method to hide empty containers
        conf._hide_empty_containers(doc)

        # Check that empty containers and their headings are hidden
        empty_containers = doc.xpath(
            "//div[contains(@class, 'o_settings_container') "
            "and contains(@class, 'd-none')]"
        )
        self.assertEqual(len(empty_containers), 2)

        # Check that headings before empty containers are hidden
        hidden_headings = doc.xpath("//h2[contains(@class, 'd-none')]")
        self.assertEqual(len(hidden_headings), 1)
        self.assertEqual(hidden_headings[0].text, "Heading 1")

        # Check that containers with visible setting boxes are not hidden
        visible_containers = doc.xpath(
            "//div[contains(@class, 'o_settings_container') "
            "and not(contains(@class, 'd-none'))]"
        )
        self.assertEqual(len(visible_containers), 1)

    def test_hide_enterprise_settings(self):
        """Test the _hide_enterprise_settings method"""
        conf = self.env["res.config.settings"].create({})

        # Create a test XML document with upgrade_boolean widgets
        xml_content = """
        <form>
            <div class="o_setting_box">
                <div>
                    <field name="show_effect" widget="upgrade_boolean"/>
                </div>
            </div>
            <div class="o_setting_box">
                <div>
                    <field name="field2"/>
                </div>
            </div>
        </form>
        """
        doc = etree.XML(xml_content)

        # Apply the method to hide enterprise settings
        conf._hide_enterprise_settings(doc)

        # Check that setting boxes with upgrade_boolean widgets are hidden
        hidden_boxes = doc.xpath(
            "//div[contains(@class, 'o_setting_box') and contains(@class, 'd-none')]"
        )
        self.assertEqual(len(hidden_boxes), 1)

        # Check that other setting boxes are not hidden
        visible_boxes = doc.xpath(
            "//div[contains(@class, 'o_setting_box') and not(contains(@class, 'd-none'))]"
        )
        self.assertEqual(len(visible_boxes), 1)

    def test_get_views_non_base_view(self):
        """Test that get_views doesn't modify non-base views"""
        conf = self.env["res.config.settings"].create({})

        # Create a custom view
        custom_view = self.env["ir.ui.view"].create(
            {
                "name": "test_custom_view",
                "model": "res.config.settings",
                "arch": """
            <form>
                <div class="o_setting_box">
                    <div>
                        <field name="show_effect" widget="upgrade_boolean"/>
                    </div>
                </div>
            </form>
            """,
            }
        )

        # Get the view with get_views
        view_result = conf.get_views([[custom_view.id, "form"]])

        # Check that the view wasn't modified (upgrade_boolean widget is still visible)
        doc = etree.XML(view_result["views"]["form"]["arch"])
        upgrade_fields = doc.xpath("//field[@widget='upgrade_boolean']")
        self.assertEqual(len(upgrade_fields), 1)

        # Check that the setting box wasn't hidden
        hidden_boxes = doc.xpath(
            "//div[contains(@class, 'o_setting_box') " "and contains(@class, 'd-none')]"
        )
        self.assertEqual(len(hidden_boxes), 0)

    def test_search_base(self):
        if self.env.get("payment.provider"):
            acquirer_ids = self.env["payment.provider"].search([])
            self.assertFalse(any([a.module_to_buy for a in acquirer_ids]))

    def test_search_ir_module(self):
        module_ids = self.env["ir.module.module"].search([])
        self.assertFalse(any([m.to_buy for m in module_ids]))

    def test_appstore_invisible(self):
        """The appstore widget is invisible"""
        conf = self.env["res.config.settings"].create({})
        view = conf.get_views([[False, "form"]])["views"]["form"]
        doc = etree.XML(view["arch"])

        query = "//div[@id='appstore']"
        for item in doc.xpath(query):
            invisible_attrib = json.loads(item.attrib["modifiers"])
            self.assertTrue(invisible_attrib["invisible"])

    def test_appstore_visible(self):
        """Disabling the view makes the appstore widget visible again"""
        conf_form_view = self.env.ref(
            "remove_odoo_enterprise.res_config_settings_view_form"
        )
        conf_form_view.active = False
        conf = self.env["res.config.settings"].create({})
        view = conf.get_views([[False, "form"]])["views"]["form"]
        doc = etree.XML(view["arch"])

        query = "//div[@id='appstore']"
        for item in doc.xpath(query):
            self.assertNotIn("modifiers", item.attrib)
