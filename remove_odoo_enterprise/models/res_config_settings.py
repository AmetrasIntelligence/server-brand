# Copyright 2016 LasLabs Inc.
# Copyright 2018-2020 Onestein (<http://www.onestein.eu>)
# Copyright 2023 Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from lxml import etree

from odoo import api, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.model
    def get_views(self, views, options=None):
        """Override to hide settings related to enterprise features.

        This method modifies the form view for settings to hide options
        that require enterprise version of Odoo.
        """
        result = super().get_views(views, options)

        # Only process the specific configuration view we're interested in
        if not self._is_base_config_settings_view(result):
            return result

        doc = etree.XML(result["views"]["form"]["arch"])

        # Hide all setting boxes containing upgrade_boolean widgets
        self._hide_enterprise_settings(doc)

        # Hide empty setting containers and their headings
        self._hide_empty_containers(doc)

        # Update the form view architecture with the modified XML
        result["views"]["form"]["arch"] = etree.tostring(doc)
        return result

    def _is_base_config_settings_view(self, view_result):
        """Check if the current view is the base settings form."""
        form_view = self.env["ir.ui.view"].browse(view_result["views"]["form"]["id"])
        view_xml_ids = (form_view.xml_id, form_view.inherit_id.xml_id)
        return "base.res_config_settings_view_form" in view_xml_ids

    def _hide_enterprise_settings(self, doc):
        """Hide all setting boxes containing upgrade_boolean widgets."""
        # Find all setting boxes with upgrade_boolean widgets
        query = (
            "//div[contains(@class, 'o_setting_box')]"
            "[.//field[@widget='upgrade_boolean']]"
        )
        for setting_box in doc.xpath(query):
            classes = setting_box.attrib.get("class", "").split()
            if "d-none" not in classes:
                classes.append("d-none")
            setting_box.attrib["class"] = " ".join(classes)

    def _hide_empty_containers(self, doc):
        """Hide containers that no longer have any visible setting boxes."""
        # Find containers with no visible setting boxes
        empty_container_query = (
            "//div[contains(@class, 'o_settings_container')]"
            "[not(.//div[contains(@class, 'o_setting_box') "
            "and not(contains(@class, 'd-none'))])]"
        )

        for empty_container in doc.xpath(empty_container_query):
            # If there's a heading before the container, hide it too
            prev_element = empty_container.getprevious()
            if prev_element is not None and prev_element.tag == "h2":
                heading_classes = prev_element.attrib.get("class", "").split()
                if "d-none" not in heading_classes:
                    heading_classes.append("d-none")
                prev_element.attrib["class"] = " ".join(heading_classes)

            # Hide the empty container
            container_classes = empty_container.attrib.get("class", "").split()
            if "d-none" not in container_classes:
                container_classes.append("d-none")
            empty_container.attrib["class"] = " ".join(container_classes)
