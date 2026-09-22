"""Tests for the mail/calendar builders in scripts/.

Run with either:

    python -m unittest discover tests
    python -m pytest tests
"""

import base64
import email
import email.policy
import email.utils
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_mail  # noqa: E402  # pyright: ignore[reportMissingImports]
import mail_frontmatter  # noqa: E402  # pyright: ignore[reportMissingImports]
import mail_ics  # noqa: E402  # pyright: ignore[reportMissingImports]
import mail_render  # noqa: E402  # pyright: ignore[reportMissingImports]


class FrontmatterParsingTests(unittest.TestCase):
    def test_fields_and_body_are_separated(self):
        doc = mail_frontmatter.parse(
            "---\nto: a@example.com\nsubject: Hello\n---\n\nHi there,\n\nBody.\n"
        )
        self.assertEqual(doc.fields["to"], "a@example.com")
        self.assertEqual(doc.fields["subject"], "Hello")
        self.assertEqual(doc.body, "Hi there,\n\nBody.\n")

    def test_subject_keeps_its_own_colons(self):
        doc = mail_frontmatter.parse("---\nsubject: Re: Q3 invoice: revised\n---\nBody\n")
        self.assertEqual(doc.fields["subject"], "Re: Q3 invoice: revised")

    def test_utf8_bom_is_stripped(self):
        doc = mail_frontmatter.parse("﻿---\nto: a@example.com\n---\nBody\n")
        self.assertEqual(doc.fields["to"], "a@example.com")
        self.assertEqual(doc.body, "Body\n")

    def test_crlf_input_parses(self):
        doc = mail_frontmatter.parse("---\r\nto: a@example.com\r\n---\r\nBody\r\n")
        self.assertEqual(doc.fields["to"], "a@example.com")
        self.assertIn("Body", doc.body)

    def test_empty_value_is_treated_as_absent(self):
        doc = mail_frontmatter.parse("---\nto: a@example.com\ncc:\nbcc:   \n---\nBody\n")
        self.assertNotIn("cc", doc.fields)
        self.assertNotIn("bcc", doc.fields)
        self.assertEqual(doc.addresses("cc"), [])

    def test_unknown_key_warns_and_is_dropped(self):
        doc = mail_frontmatter.parse("---\nto: a@example.com\natach: f.pdf\n---\nBody\n")
        self.assertNotIn("atach", doc.fields)
        self.assertTrue(any("atach" in w for w in doc.warnings))

    def test_duplicate_key_warns_and_last_wins(self):
        doc = mail_frontmatter.parse("---\nsubject: one\nsubject: two\n---\nBody\n")
        self.assertEqual(doc.fields["subject"], "two")
        self.assertTrue(any("duplicate" in w for w in doc.warnings))

    def test_unclosed_fence_warns_and_treats_all_as_body(self):
        doc = mail_frontmatter.parse("---\nto: a@example.com\n\nBody with no fence\n")
        self.assertNotIn("to", doc.fields)
        self.assertIn("Body with no fence", doc.body)
        self.assertTrue(any("never closed" in w for w in doc.warnings))

    def test_absent_fence_means_whole_file_is_body(self):
        doc = mail_frontmatter.parse("Hi,\n\nJust a body.\n")
        self.assertEqual(doc.fields, {})
        self.assertEqual(doc.body, "Hi,\n\nJust a body.\n")

    def test_fence_inside_body_does_not_end_frontmatter_early(self):
        doc = mail_frontmatter.parse(
            "---\nto: a@example.com\n---\nFirst\n\n---\n\nSecond\n"
        )
        self.assertEqual(doc.fields["to"], "a@example.com")
        self.assertIn("---", doc.body)
        self.assertIn("Second", doc.body)

    def test_quoted_display_name_with_comma_stays_one_address(self):
        doc = mail_frontmatter.parse(
            '---\nto: "Smith, Bob" <bob@example.com>, alice@example.com\n---\nBody\n'
        )
        self.assertEqual(
            doc.addresses("to"),
            ['"Smith, Bob" <bob@example.com>', "alice@example.com"],
        )

    def test_attachment_paths_split_and_unquote(self):
        doc = mail_frontmatter.parse(
            '---\nattach: "report, final.pdf", image-1.png\n---\nBody\n'
        )
        self.assertEqual(doc.paths("attach"), ["report, final.pdf", "image-1.png"])

    def test_event_keys_are_collected_without_the_prefix(self):
        doc = mail_frontmatter.parse(
            "---\nevent.title: Kick-off\nevent.start: 2026-09-29 09:00\n---\nBody\n"
        )
        self.assertEqual(doc.event()["title"], "Kick-off")
        self.assertEqual(doc.event()["start"], "2026-09-29 09:00")

    def test_threading_keys_are_known(self):
        doc = mail_frontmatter.parse("---\nin-reply-to: <a@x>\n---\nBody\n")
        self.assertEqual(doc.warnings, [])

    def test_message_ids_accept_both_list_spellings(self):
        header_form = mail_frontmatter.parse(
            "---\nreferences: <root@x> <mid@x>\nin-reply-to: <mid@x>\n---\nBody\n"
        )
        self.assertEqual(header_form.message_ids("references"), ["<root@x>", "<mid@x>"])
        self.assertEqual(header_form.message_ids("in-reply-to"), ["<mid@x>"])

        list_form = mail_frontmatter.parse("---\nreferences: <root@x>, <mid@x>\n---\nBody\n")
        self.assertEqual(list_form.message_ids("references"), ["<root@x>", "<mid@x>"])

    def test_a_bare_message_id_is_bracketed(self):
        doc = mail_frontmatter.parse("---\nin-reply-to: mid@x\n---\nBody\n")
        self.assertEqual(doc.message_ids("in-reply-to"), ["<mid@x>"])


class EscapeTests(unittest.TestCase):
    def test_text_escaping_covers_the_dangerous_characters(self):
        self.assertEqual(
            mail_render.escape_text('<script>a & b</script>'),
            "&lt;script&gt;a &amp; b&lt;/script&gt;",
        )

    def test_attr_escaping_also_covers_quotes(self):
        self.assertEqual(mail_render.escape_attr('a"b'), "a&quot;b")


class UrlSafetyTests(unittest.TestCase):
    def test_allowed_schemes(self):
        for url in ["https://x.test/a", "http://x.test", "mailto:a@x.test", "cid:img-1"]:
            self.assertTrue(mail_render.url_is_safe(url), url)

    def test_relative_urls_are_allowed(self):
        self.assertTrue(mail_render.url_is_safe("/path/page"))
        self.assertTrue(mail_render.url_is_safe("page.html"))

    def test_javascript_scheme_is_rejected(self):
        self.assertFalse(mail_render.url_is_safe("javascript:alert(1)"))
        self.assertFalse(mail_render.url_is_safe("JaVaScRiPt:alert(1)"))
        self.assertFalse(mail_render.url_is_safe("data:text/html;base64,PHNjcmlwdD4="))

    def test_whitespace_cannot_smuggle_a_scheme(self):
        self.assertFalse(mail_render.url_is_safe("java\nscript:alert(1)"))
        self.assertFalse(mail_render.url_is_safe("java\tscript:alert(1)"))


class HtmlRenderingTests(unittest.TestCase):
    def render(self, body, cid_for=None):
        blocks = mail_render.parse_blocks(body)
        return mail_render.render_html(blocks, cid_for or {})

    def test_raw_html_in_the_body_is_escaped(self):
        html, _ = self.render("<script>alert(1)</script>")
        self.assertNotIn("<script", html)
        self.assertIn("&lt;script&gt;", html)

    def test_script_url_is_not_emitted_as_a_link(self):
        html, warnings = self.render("Click [here](javascript:alert(1)) now")
        self.assertNotIn("javascript:", html)
        self.assertNotIn("<a ", html)
        self.assertIn("here", html)
        self.assertTrue(any("disallowed scheme" in w for w in warnings))

    def test_html_entity_encoded_scheme_is_neutralised_by_escaping(self):
        html, _ = self.render("[x](&#106;avascript:alert(1))")
        # The '&' is escaped, so the attribute holds the literal text, not an entity.
        self.assertIn("&amp;#106;avascript:", html)
        self.assertNotIn('href="&#106;', html)

    def test_quote_in_url_cannot_break_out_of_the_attribute(self):
        html, _ = self.render('[x](https://x.test/a"onmouseover="alert(1))')
        self.assertIn("&quot;", html)
        self.assertNotIn('onmouseover="alert(1)"', html)

    def test_bold_italic_and_link(self):
        html, _ = self.render("**bold** and *italic* and [text](https://x.test)")
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<em>italic</em>", html)
        self.assertIn('<a href="https://x.test">text</a>', html)

    def test_image_resolves_to_cid(self):
        html, warnings = self.render(
            "Before\n\n![Search result](image-1.png)\n\nAfter", {"image-1.png": "img-1@local"}
        )
        self.assertIn('<img src="cid:img-1@local" alt="Search result">', html)
        self.assertEqual(warnings, [])

    def test_cid_given_in_header_form_is_stripped_for_the_url(self):
        # Content-ID carries angle brackets; the cid: URL must not, or the link breaks.
        html, _ = self.render("![x](i.png)", {"i.png": "<img-1@local>"})
        self.assertIn('src="cid:img-1@local"', html)
        self.assertNotIn("&lt;", html)

    def test_unresolved_image_falls_back_to_alt_text_with_a_warning(self):
        html, warnings = self.render("![Missing](nope.png)")
        self.assertNotIn("<img", html)
        self.assertIn("Missing", html)
        self.assertTrue(any("nope.png" in w for w in warnings))

    def test_paragraphs_and_bullets(self):
        html, _ = self.render("One\nstill one\n\n- a\n- b\n\nTwo")
        self.assertIn("<p>One<br>\nstill one</p>", html)
        self.assertIn("<li>a</li>", html)
        self.assertIn("<li>b</li>", html)
        self.assertIn("<p>Two</p>", html)

    def test_single_newlines_become_br(self):
        html, _ = self.render("line one\nline two")
        self.assertIn("line one<br>\nline two", html)


class PlainRenderingTests(unittest.TestCase):
    def test_markup_is_stripped_from_the_plain_part(self):
        blocks = mail_render.parse_blocks("**bold** and *italic*")
        self.assertEqual(mail_render.render_plain(blocks), "bold and italic")

    def test_links_keep_their_url(self):
        blocks = mail_render.parse_blocks("see [the site](https://x.test)")
        self.assertEqual(mail_render.render_plain(blocks), "see the site <https://x.test>")

    def test_images_become_an_explicit_marker(self):
        blocks = mail_render.parse_blocks("![Search result](image-1.png)")
        self.assertEqual(mail_render.render_plain(blocks), "[image: Search result]")

    def test_paragraphs_are_blank_line_separated(self):
        blocks = mail_render.parse_blocks("One\n\nTwo")
        self.assertEqual(mail_render.render_plain(blocks), "One\n\nTwo")

    def test_bullets_keep_their_marker(self):
        blocks = mail_render.parse_blocks("- a\n- b")
        self.assertEqual(mail_render.render_plain(blocks), "- a\n- b")


class ImageCollectionTests(unittest.TestCase):
    def test_paths_are_collected_in_order_without_duplicates(self):
        blocks = mail_render.parse_blocks("![a](one.png)\n\n![b](two.png)\n\n![c](one.png)")
        self.assertEqual(mail_render.collect_image_paths(blocks), ["one.png", "two.png"])

    def test_bullets_are_searched_too(self):
        blocks = mail_render.parse_blocks("- ![a](one.png)")
        self.assertEqual(mail_render.collect_image_paths(blocks), ["one.png"])


class IcsEventTests(unittest.TestCase):
    NOW = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)

    def build(self, **event):
        return mail_ics.build_ics(event=event, slug="my-round", now=self.NOW)

    def field(self, ics, name):
        for line in ics.split("\r\n"):
            if line.startswith(name + ":") or line.startswith(name + ";"):
                return line
        raise AssertionError(f"{name} not found in:\n{ics}")

    def test_all_day_event_is_a_single_value_date_span(self):
        ics, warnings = self.build(**{"title": "Annual conference", "start": "2026-09-29"})
        self.assertEqual(self.field(ics, "DTSTART"), "DTSTART;VALUE=DATE:20260929")
        # RFC 5545 DTEND is exclusive, so a one-day event ends the next day.
        self.assertEqual(self.field(ics, "DTEND"), "DTEND;VALUE=DATE:20260930")
        self.assertEqual(warnings, [])

    def test_all_day_end_is_treated_as_exclusive_and_warned_about(self):
        ics, warnings = self.build(
            **{"title": "Conference", "start": "2026-09-29", "end": "2026-09-30"}
        )
        self.assertEqual(self.field(ics, "DTEND"), "DTEND;VALUE=DATE:20260930")
        self.assertTrue(any("last day included is 2026-09-29" in w for w in warnings))

    def test_timed_event_converts_to_utc_with_dst(self):
        summer, _ = self.build(
            **{"title": "Kick-off", "start": "2026-09-29 09:00", "timezone": "Europe/Berlin"}
        )
        winter, _ = self.build(
            **{"title": "Kick-off", "start": "2026-01-15 09:00", "timezone": "Europe/Berlin"}
        )
        self.assertEqual(self.field(summer, "DTSTART"), "DTSTART:20260929T070000Z")
        self.assertEqual(self.field(winter, "DTSTART"), "DTSTART:20260115T080000Z")

    def test_fractional_offset_zone(self):
        ics, _ = self.build(
            **{"title": "Call", "start": "2026-09-29 09:00", "timezone": "Asia/Kolkata"}
        )
        self.assertEqual(self.field(ics, "DTSTART"), "DTSTART:20260929T033000Z")

    def test_event_spanning_a_dst_change_converts_each_end_independently(self):
        # Berlin leaves CEST on 2026-10-25: +02:00 before, +01:00 after.
        ics, _ = self.build(
            **{
                "title": "Overnight",
                "start": "2026-10-24 09:00",
                "end": "2026-10-26 09:00",
                "timezone": "Europe/Berlin",
            }
        )
        self.assertEqual(self.field(ics, "DTSTART"), "DTSTART:20261024T070000Z")
        self.assertEqual(self.field(ics, "DTEND"), "DTEND:20261026T080000Z")

    def test_missing_end_defaults_to_one_hour_with_a_warning(self):
        ics, warnings = self.build(
            **{"title": "Call", "start": "2026-09-29 09:00", "timezone": "Europe/Berlin"}
        )
        self.assertEqual(self.field(ics, "DTEND"), "DTEND:20260929T080000Z")
        self.assertTrue(any("defaulted to one hour" in w for w in warnings))

    def test_timed_event_without_a_timezone_is_refused(self):
        with self.assertRaises(mail_ics.EventError):
            self.build(**{"title": "Call", "start": "2026-09-29 09:00"})

    def test_unknown_timezone_is_refused_not_silently_interpreted_as_utc(self):
        with self.assertRaises(mail_ics.EventError):
            self.build(
                **{"title": "Call", "start": "2026-09-29 09:00", "timezone": "Europe/Brelin"}
            )

    def test_explicit_utc_escape_hatch_is_honoured(self):
        ics, _ = self.build(**{"title": "Call", "start": "2026-09-29 09:00", "utc": "2026-09-29 07:00"})
        self.assertEqual(self.field(ics, "DTSTART"), "DTSTART:20260929T070000Z")

    def test_end_before_start_is_refused(self):
        with self.assertRaises(mail_ics.EventError):
            self.build(
                **{
                    "title": "Call",
                    "start": "2026-09-29 09:00",
                    "end": "2026-09-29 08:00",
                    "timezone": "Europe/Berlin",
                }
            )

    def test_title_and_start_are_required(self):
        with self.assertRaises(mail_ics.EventError):
            self.build(**{"start": "2026-09-29"})
        with self.assertRaises(mail_ics.EventError):
            self.build(**{"title": "No start"})

    def test_default_output_is_a_personal_appointment(self):
        ics, _ = self.build(**{"title": "Dentist", "start": "2026-09-29 09:00", "timezone": "Europe/Berlin"})
        self.assertNotIn("METHOD:", ics)
        self.assertNotIn("ORGANIZER", ics)
        self.assertNotIn("ATTENDEE", ics)

    def test_meeting_request_emits_method_organizer_and_attendees(self):
        ics, _ = self.build(
            **{
                "title": "Project meeting",
                "start": "2026-09-29 09:00",
                "timezone": "Europe/Berlin",
                "method": "request",
                "organizer": "me@example.com",
                "attendees": "alice@example.com, bob@example.com",
            }
        )
        self.assertIn("METHOD:REQUEST", ics)
        self.assertIn("ORGANIZER;CN=me@example.com:mailto:me@example.com", ics)
        self.assertIn("ATTENDEE;CN=alice@example.com;RSVP=TRUE:mailto:alice@example.com", ics)
        self.assertIn("ATTENDEE;CN=bob@example.com;RSVP=TRUE:mailto:bob@example.com", ics)

    def test_meeting_request_without_an_organizer_is_refused(self):
        with self.assertRaises(mail_ics.EventError):
            self.build(
                **{
                    "title": "Meeting",
                    "start": "2026-09-29 09:00",
                    "timezone": "Europe/Berlin",
                    "method": "request",
                }
            )

    def test_uid_survives_rescheduling_and_regeneration(self):
        base = {"title": "Project meeting", "timezone": "Europe/Berlin"}
        first, _ = self.build(start="2026-09-29 09:00", **base)
        later_day = datetime(2026, 9, 25, 8, 0, tzinfo=timezone.utc)
        moved, _ = mail_ics.build_ics(
            event={**base, "start": "2026-10-01 14:00"}, slug="my-round", now=later_day
        )
        self.assertEqual(self.field(first, "UID"), self.field(moved, "UID"))

    def test_uid_changes_when_the_title_changes(self):
        first, _ = self.build(**{"title": "One", "start": "2026-09-29"})
        second, _ = self.build(**{"title": "Two", "start": "2026-09-29"})
        self.assertNotEqual(self.field(first, "UID"), self.field(second, "UID"))

    def test_dtstamp_is_the_only_thing_that_changes_between_runs(self):
        event = {"title": "Call", "start": "2026-09-29 09:00", "timezone": "Europe/Berlin"}
        first, _ = mail_ics.build_ics(event=event, slug="s", now=self.NOW)
        second, _ = mail_ics.build_ics(
            event=event, slug="s", now=datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)
        )
        strip = lambda text: [ln for ln in text.split("\r\n") if not ln.startswith("DTSTAMP")]
        self.assertEqual(strip(first), strip(second))

    def test_utc_only_and_no_vtimezone(self):
        ics, _ = self.build(**{"title": "Call", "start": "2026-09-29 09:00", "timezone": "Europe/Berlin"})
        self.assertNotIn("BEGIN:VTIMEZONE", ics)
        for name in ("DTSTART", "DTEND", "DTSTAMP"):
            self.assertRegex(self.field(ics, name), r"^\w+[:;].*\d{8}T\d{6}Z$")

    def test_crlf_line_endings(self):
        ics, _ = self.build(**{"title": "Call", "start": "2026-09-29 09:00", "timezone": "Europe/Berlin"})
        self.assertEqual(ics.replace("\r\n", "").count("\n"), 0)
        self.assertTrue(ics.endswith("\r\n"))

    def test_text_values_are_escaped(self):
        ics, _ = self.build(**{"title": "Q3, review; part 2", "start": "2026-09-29", "location": "A\\B"})
        self.assertIn("SUMMARY:Q3\\, review\\; part 2", ics)
        self.assertIn("LOCATION:A\\\\B", ics)

    def test_lines_never_exceed_75_octets(self):
        ics, _ = self.build(**{"title": "Conference " + "x" * 200, "start": "2026-09-29"})
        for line in ics.split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 75, line)

    def test_cjk_summary_folds_on_a_character_boundary(self):
        title = "会议" * 40  # 240 bytes of 3-byte characters
        ics, _ = self.build(**{"title": title, "start": "2026-09-29"})
        lines = ics.split("\r\n")
        for line in lines:
            self.assertLessEqual(len(line.encode("utf-8")), 75)
        folded = [ln for ln in lines if ln.startswith(" ")]
        self.assertTrue(folded, "expected the long summary to fold across lines")
        # No folded line may start with a stray replacement character, which is what a
        # mid-character byte split would produce.
        for line in folded:
            self.assertNotIn("�", line)

        start = lines.index(self.field(ics, "SUMMARY"))
        unfolded = lines[start]
        for line in lines[start + 1 :]:
            if not line.startswith(" "):
                break
            unfolded += line[1:]
        self.assertEqual(unfolded, "SUMMARY:" + title)


class EmlBuildTests(unittest.TestCase):
    PNG = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="mail-test-"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / "shot.png").write_bytes(self.PNG)
        (self.dir / "conf.pdf").write_bytes(b"%PDF-1.4 fake body")

    def build(self, frontmatter, body="", **kw):
        text = "---\n" + frontmatter.strip() + "\n---\n\n" + body
        doc = mail_frontmatter.parse(text)
        data, warnings = build_mail.build_eml(doc, self.dir, **kw)
        return email.message_from_bytes(data, policy=email.policy.default), data, warnings

    def shape(self, msg):
        """Nested content types, e.g. `mixed(related(alternative(plain,html),png),pdf)`."""
        if not msg.is_multipart():
            return msg.get_content_subtype()
        inner = ",".join(self.shape(part) for part in msg.iter_parts())
        return f"{msg.get_content_subtype()}({inner})"

    def text_parts(self, msg):
        return [p for p in msg.walk() if p.get_content_type().startswith("text/")]

    def test_structure_with_images_and_attachment(self):
        msg, _, _ = self.build(
            "to: a@example.com\nattach: conf.pdf",
            "Body\n\n![a shot](shot.png)\n",
        )
        self.assertEqual(self.shape(msg), "mixed(related(alternative(plain,html),png),pdf)")

    def test_structure_with_images_only(self):
        msg, _, _ = self.build("to: a@example.com", "![shot](shot.png)\n")
        self.assertEqual(self.shape(msg), "related(alternative(plain,html),png)")

    def test_structure_with_attachment_only_has_no_empty_related_wrapper(self):
        msg, _, _ = self.build("to: a@example.com\nattach: conf.pdf", "Body\n")
        self.assertEqual(self.shape(msg), "mixed(alternative(plain,html),pdf)")

    def test_structure_with_neither(self):
        msg, _, _ = self.build("to: a@example.com", "Body\n")
        self.assertEqual(self.shape(msg), "alternative(plain,html)")

    def test_text_only_skips_the_html_alternative(self):
        msg, _, _ = self.build("to: a@example.com", "Body\n", text_only=True)
        self.assertEqual(self.shape(msg), "plain")

    def test_no_x_unsent_by_default_so_outlook_opens_it_as_received(self):
        # Without the header Outlook shows Reply/Reply All; with it, it opens a compose
        # window instead, which has no Reply. Received style is the default.
        msg, _, _ = self.build("to: a@example.com", "Body\n")
        self.assertIsNone(msg["X-Unsent"])

    def test_draft_mode_opts_back_into_the_compose_window(self):
        msg, _, _ = self.build("to: a@example.com", "Body\n", draft=True)
        self.assertEqual(msg["X-Unsent"], "1")

    def test_missing_from_warns_only_in_received_style(self):
        _, _, warnings = self.build("to: a@example.com", "Body\n")
        self.assertTrue(any("no from: address" in w for w in warnings))
        # In draft mode Outlook supplies the account identity, so there is nothing to warn
        # about.
        _, _, draft_warnings = self.build("to: a@example.com", "Body\n", draft=True)
        self.assertFalse(any("no from: address" in w for w in draft_warnings))

    def test_threading_headers_are_emitted(self):
        msg, _, warnings = self.build(
            "to: a@example.com\nfrom: me@example.com\n"
            "in-reply-to: <abc@example.com>\nreferences: <root@example.com>, <abc@example.com>",
            "Body\n",
        )
        self.assertEqual(msg["In-Reply-To"], "<abc@example.com>")
        # Both spellings of a References list land on the same header value.
        self.assertEqual(msg["References"], "<root@example.com> <abc@example.com>")
        self.assertEqual(warnings, [])

    def test_from_in_the_frontmatter_is_honoured(self):
        msg, _, _ = self.build("to: a@example.com\nfrom: me@example.com", "Body\n")
        self.assertEqual(msg["From"], "me@example.com")

    def test_from_flag_overrides_the_frontmatter(self):
        msg, _, _ = self.build(
            "to: a@example.com\nfrom: me@example.com", "Body\n", from_addr="other@example.com"
        )
        self.assertEqual(msg["From"], "other@example.com")

    def test_bare_message_ids_get_their_brackets(self):
        msg, _, _ = self.build("to: a@example.com\nin-reply-to: abc@example.com", "Body\n")
        self.assertEqual(msg["In-Reply-To"], "<abc@example.com>")

    def test_references_defaults_to_in_reply_to(self):
        msg, _, _ = self.build("to: a@example.com\nin-reply-to: <abc@example.com>", "Body\n")
        self.assertEqual(msg["References"], "<abc@example.com>")

    def test_references_without_in_reply_to_warns(self):
        _, _, warnings = self.build(
            "to: a@example.com\nreferences: <root@example.com>", "Body\n"
        )
        self.assertTrue(any("Outlook threads on In-Reply-To" in w for w in warnings))

    def test_from_date_and_message_id_are_absent_by_default(self):
        msg, _, _ = self.build("to: a@example.com", "Body\n")
        for header in ("From", "Date", "Message-ID", "Sender"):
            self.assertIsNone(msg[header], header)

    def test_from_and_date_can_be_opted_into(self):
        msg, _, _ = self.build(
            "to: a@example.com",
            "Body\n",
            from_addr="me@example.com",
            date_header="Thu, 1 Jan 2026 00:00:00 +0000",
        )
        self.assertEqual(msg["From"], "me@example.com")
        # The library re-formats a Date header on serialize (zero-padded day), which is
        # harmless - assert it is the same instant rather than the same spelling.
        self.assertEqual(email.utils.parsedate_to_datetime(str(msg["Date"])),
                         email.utils.parsedate_to_datetime("Thu, 1 Jan 2026 00:00:00 +0000"))

    def test_empty_cc_is_not_emitted(self):
        msg, _, _ = self.build("to: a@example.com\ncc:\nbcc:\n", "Body\n")
        self.assertIsNone(msg["Cc"])
        self.assertIsNone(msg["Bcc"])

    def test_bcc_warns_about_leaking_the_blind_list(self):
        _, _, warnings = self.build("to: a@example.com\nbcc: hidden@example.com", "Body\n")
        self.assertTrue(any("bcc" in w for w in warnings))

    def test_body_is_crlf_only(self):
        _, data, _ = self.build("to: a@example.com", "One\n\nTwo\n")
        self.assertEqual(data.replace(b"\r\n", b"").count(b"\n"), 0)

    def test_non_ascii_subject_round_trips_through_an_encoded_word(self):
        subject = "Re: Prüfung — 会议 about pricing"
        msg, data, _ = self.build(f"to: a@example.com\nsubject: {subject}", "Body\n")
        header_block = data.split(b"\r\n\r\n")[0]
        header_block.decode("ascii")  # raises if a raw non-ASCII byte leaked in
        self.assertRegex(header_block.decode("ascii"), r"Subject: .*=\?utf-8\?b\?")
        self.assertEqual(str(msg["Subject"]), subject)

    def test_inline_image_is_inline_and_its_cid_matches_the_html(self):
        msg, _, _ = self.build("to: a@example.com", "![a shot](shot.png)\n")
        image = [p for p in msg.walk() if p.get_content_type() == "image/png"][0]
        self.assertEqual(image.get_content_disposition(), "inline")
        self.assertEqual(image.get_content(), self.PNG)
        html = [p for p in self.text_parts(msg) if p.get_content_subtype() == "html"][0]
        cid = str(image["Content-ID"]).strip("<>")
        self.assertIn(f'cid:{cid}', html.get_content())
        self.assertIn('alt="a shot"', html.get_content())

    def test_alternative_is_part_one_of_the_related_block(self):
        msg, _, _ = self.build("to: a@example.com", "![shot](shot.png)\n")
        first = next(iter(msg.iter_parts()))
        self.assertEqual(first.get_content_type(), "multipart/alternative")

    def test_attachment_bytes_and_filename_survive(self):
        msg, _, _ = self.build("to: a@example.com\nattach: conf.pdf", "Body\n")
        pdf = [p for p in msg.iter_parts() if p.get_content_type() == "application/pdf"][0]
        self.assertEqual(pdf.get_filename(), "conf.pdf")
        self.assertEqual(pdf.get_content(), b"%PDF-1.4 fake body")

    def test_html_body_escapes_and_the_plain_body_is_stripped(self):
        msg, _, _ = self.build("to: a@example.com", "**Hi** <script>x</script>\n")
        plain, html = self.text_parts(msg)  # walk order is plain first
        self.assertNotIn("<script", html.get_content())
        self.assertIn("<strong>Hi</strong>", html.get_content())
        self.assertIn("&lt;script&gt;", html.get_content())
        # The plain part legitimately keeps the raw text; it carries no markup.
        self.assertIn("Hi <script>x</script>", plain.get_content())

    def test_missing_to_is_an_error(self):
        text = "---\nsubject: No recipient\n---\n\nBody\n"
        with self.assertRaises(build_mail.BuildError):
            build_mail.build_eml(mail_frontmatter.parse(text), self.dir)

    def test_missing_image_file_is_an_error_naming_the_path(self):
        with self.assertRaises(build_mail.BuildError) as ctx:
            self.build("to: a@example.com", "![gone](missing.png)\n")
        self.assertIn("missing.png", str(ctx.exception))

    def test_missing_attachment_is_an_error(self):
        with self.assertRaises(build_mail.BuildError):
            self.build("to: a@example.com\nattach: nope.pdf", "Body\n")

    def test_file_that_is_both_inline_and_attached_warns(self):
        _, _, warnings = self.build(
            "to: a@example.com\nattach: shot.png", "![shot](shot.png)\n"
        )
        self.assertTrue(any("both inline and attached" in w for w in warnings))

    def test_message_ids_are_never_rfc2047_encoded(self):
        # An id long enough to need folding: the stdlib would otherwise encode it as
        # `=3C...=40...`, which no client can thread on.
        long_id = "<" + "A" * 70 + "@example.com>"
        _msg, data, _ = self.build(f"to: a@example.com\nin-reply-to: {long_id}", "Body\n")

        raw = data.decode("ascii", "replace")
        self.assertNotIn("=?utf-8?", raw)
        self.assertIn(long_id, raw.replace("\r\n ", ""))

    def test_a_whole_references_chain_survives(self):
        msg, data, _ = self.build(
            "to: a@example.com\n"
            "in-reply-to: <mid@example.com>\n"
            "references: <" + "B" * 70 + "@example.com>, <other@example.com>, <mid@example.com>",
            "Body\n",
        )
        # Re-parse: a single-id header would silently keep only the first entry.
        reparsed = email.message_from_bytes(data, policy=email.policy.default)
        ids = str(reparsed["References"]).split()
        self.assertEqual(len(ids), 3)
        self.assertEqual(ids[-1], "<mid@example.com>")
        self.assertEqual(str(msg["In-Reply-To"]), "<mid@example.com>")


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="mail-cli-"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.draft = self.dir / "final.md"
        self.draft.write_text(
            "---\n"
            "to: alice@example.com\n"
            "subject: Re: Project meeting\n"
            "event.title: Project meeting\n"
            "event.start: 2026-09-29 09:00\n"
            "event.timezone: Europe/Berlin\n"
            "---\n\n"
            "Hi Alice,\n\nFriday works.\n\nBest,\n\nAlex\n",
            encoding="utf-8",
        )

    def test_builds_both_files_named_after_the_round_directory(self):
        self.assertEqual(build_mail.main([str(self.draft)]), 0)
        self.assertTrue((self.dir / f"{self.dir.name}.eml").is_file())
        self.assertTrue((self.dir / f"{self.dir.name}.ics").is_file())

    def test_eml_only_flag(self):
        self.assertEqual(build_mail.main([str(self.draft), "--eml"]), 0)
        self.assertTrue((self.dir / f"{self.dir.name}.eml").is_file())
        self.assertFalse((self.dir / f"{self.dir.name}.ics").exists())

    def test_ics_only_flag(self):
        self.assertEqual(build_mail.main([str(self.draft), "--ics"]), 0)
        self.assertFalse((self.dir / f"{self.dir.name}.eml").exists())
        ics = (self.dir / f"{self.dir.name}.ics").read_text(encoding="utf-8")
        self.assertIn("BEGIN:VEVENT", ics)

    def test_out_and_name_flags(self):
        out = self.dir / "out"
        self.assertEqual(build_mail.main([str(self.draft), "--name", "custom", "--out", str(out)]), 0)
        self.assertTrue((out / "custom.eml").is_file())

    def test_as_draft_does_not_collide_with_the_positional_draft(self):
        # Both used to land on args.draft, so the positional path made the flag always-on.
        self.assertEqual(build_mail.main([str(self.draft), "--eml"]), 0)
        plain = (self.dir / f"{self.dir.name}.eml").read_bytes()
        self.assertNotIn(b"X-Unsent", plain)

        self.assertEqual(build_mail.main([str(self.draft), "--eml", "--as-draft"]), 0)
        drafted = (self.dir / f"{self.dir.name}.eml").read_bytes()
        self.assertIn(b"X-Unsent: 1", drafted)

    def test_json_output_is_parseable(self):
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = build_mail.main([str(self.draft), "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertTrue(payload["ok"])
        self.assertIn("eml", payload["written"])

    def test_missing_draft_is_a_failure(self):
        self.assertEqual(build_mail.main([str(self.dir / "nope.md")]), 1)

    def test_lf_escape_hatch_warns(self):
        self.assertEqual(build_mail.main([str(self.draft), "--eol", "lf"]), 0)
        data = (self.dir / f"{self.dir.name}.eml").read_bytes()
        self.assertNotIn(b"\r\n", data)

    def test_strict_fails_on_warnings(self):
        self.draft.write_text(
            "---\nto: a@example.com\nsubject: s\ncc: unknown-key-check\n---\n\nBody\n".replace(
                "cc: unknown-key-check", "typoed-key: x"
            ),
            encoding="utf-8",
        )
        self.assertEqual(build_mail.main([str(self.draft)]), 0)
        self.assertEqual(build_mail.main([str(self.draft), "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
