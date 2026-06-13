import unittest

from esim_tools import eSIMTools


class ESIMToolsTest(unittest.TestCase):
    def setUp(self):
        self.tools = eSIMTools()

    def test_create_iphone_install_link_with_activation_code(self):
        link = self.tools.create_iphone_install_link("rsp.truphone.com", "CODE123")

        self.assertEqual(
            link,
            "https://esimsetup.apple.com/esim_qrcode_provisioning?"
            "carddata=LPA:1$rsp.truphone.com$CODE123",
        )

    def test_create_iphone_install_link_without_activation_code(self):
        link = self.tools.create_iphone_install_link("rsp.truphone.com")

        self.assertEqual(
            link,
            "https://esimsetup.apple.com/esim_qrcode_provisioning?"
            "carddata=LPA:1$rsp.truphone.com$",
        )

    def test_create_qr_from_sm_dp_returns_png_and_lpa(self):
        qr_image, lpa_string = self.tools.create_qr_from_sm_dp(
            "rsp.truphone.com",
            "CODE123",
        )

        self.assertEqual(lpa_string, "LPA:1$rsp.truphone.com$CODE123")
        self.assertTrue(qr_image.getvalue().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_extract_sm_dp_and_activation_from_lpa(self):
        result = self.tools.extract_sm_dp_and_activation(
            "LPA:1$rsp.truphone.com$CODE123"
        )

        self.assertEqual(result["format_type"], "LPA")
        self.assertEqual(result["sm_dp_address"], "rsp.truphone.com")
        self.assertEqual(result["activation_code"], "CODE123")

    def test_extract_sm_dp_and_activation_from_iphone_url(self):
        result = self.tools.extract_sm_dp_and_activation(
            "https://esimsetup.apple.com/esim_qrcode_provisioning?"
            "carddata=LPA%3A1%24rsp.truphone.com%24CODE123"
        )

        self.assertEqual(result["format_type"], "LPA")
        self.assertEqual(result["sm_dp_address"], "rsp.truphone.com")
        self.assertEqual(result["activation_code"], "CODE123")

    def test_validate_sm_dp_address_rejects_invalid_domain(self):
        is_valid, message = self.tools.validate_sm_dp_address("not-a-domain")

        self.assertFalse(is_valid)
        self.assertIn("domain", message)

    def test_validate_lpa_string_rejects_invalid_format(self):
        is_valid, message = self.tools.validate_lpa_string("rsp.truphone.com")

        self.assertFalse(is_valid)
        self.assertIn("LPA", message)

    def test_create_qr_from_lpa_rejects_invalid_lpa(self):
        with self.assertRaises(Exception) as ctx:
            self.tools.create_qr_from_lpa("rsp.truphone.com")

        self.assertIn("LPA string", str(ctx.exception))

    def test_parse_bulk_uses_default_sm_dp_for_each_block(self):
        text = (
            "Activation Code:OZ8NB-X9008-G1LB2-AAAAA\n"
            "ICCID:89851000000010674211\n"
            "\n"
            "Activation Code:QRQNB-W2108-J1JE3-BBBBB\n"
            "ICCID:89851000000010674213\n"
        )

        entries, errors = self.tools.parse_bulk_esim_input(text, "rsp.esim.exchange")

        self.assertEqual(errors, [])
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["sm_dp_address"], "rsp.esim.exchange")
        self.assertEqual(entries[0]["activation_code"], "OZ8NB-X9008-G1LB2-AAAAA")
        self.assertEqual(entries[0]["iccid"], "89851000000010674211")
        self.assertEqual(
            entries[0]["lpa_string"],
            "LPA:1$rsp.esim.exchange$OZ8NB-X9008-G1LB2-AAAAA",
        )
        self.assertEqual(entries[1]["iccid"], "89851000000010674213")

    def test_parse_bulk_block_can_override_sm_dp(self):
        text = (
            "SM-DP+:rsp.billionconnect.com\n"
            "Activation Code:CODE-1\n"
            "ICCID:1111\n"
        )

        entries, errors = self.tools.parse_bulk_esim_input(text, "rsp.esim.exchange")

        self.assertEqual(errors, [])
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["sm_dp_address"], "rsp.billionconnect.com")

    def test_parse_bulk_accepts_raw_lpa_line(self):
        text = "LPA:1$rsp.truphone.com$CODE123\nICCID:2222\n"

        entries, errors = self.tools.parse_bulk_esim_input(text, "rsp.esim.exchange")

        self.assertEqual(errors, [])
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["sm_dp_address"], "rsp.truphone.com")
        self.assertEqual(entries[0]["activation_code"], "CODE123")
        self.assertEqual(entries[0]["iccid"], "2222")

    def test_parse_bulk_reports_missing_activation_code(self):
        text = "ICCID:89851000000010674211\n"

        entries, errors = self.tools.parse_bulk_esim_input(text, "rsp.esim.exchange")

        self.assertEqual(entries, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("Activation Code", errors[0]["reason"])

    def test_parse_bulk_reports_missing_sm_dp_without_default(self):
        text = "Activation Code:CODE-1\nICCID:1111\n"

        entries, errors = self.tools.parse_bulk_esim_input(text, "")

        self.assertEqual(entries, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("SM-DP+", errors[0]["reason"])

    def test_parse_bulk_empty_input_returns_empty(self):
        entries, errors = self.tools.parse_bulk_esim_input("   \n  ", "rsp.esim.exchange")

        self.assertEqual(entries, [])
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
