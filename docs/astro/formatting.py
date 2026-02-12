"""Shared formatting and sanitization utilities for MDX documentation
generation from nf-neuro meta.yml descriptions.

All functions that touch markdown → MDX conversion belong here so both the
module and subworkflow conversion scripts can share the same logic.
"""

import re

# ---------------------------------------------------------------------------
# Small reusable helpers
# ---------------------------------------------------------------------------


def li(text):
    """Format *text* as a markdown list item."""
    return f"- {str(text)}"


def link(text, url=None):
    """Return a markdown link, or plain *text* when *url* is falsy."""
    if not url:
        return text
    return f"[{text}]({url})"


def escape_mdx(text):
    """Escape characters that are special in MDX but not in regular
    Markdown (``{`` and ``}``)."""
    return text.replace("{", "\\{").replace("}", "\\}")


# ---------------------------------------------------------------------------
# HTML sanitization scanner
# ---------------------------------------------------------------------------

#: Characters that must be escaped when rendering markdown inside HTML / MDX.
_ESCAPE = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
    "{": "\\{",
    "}": "\\}"
}


def sanitize_outside_codeblocks(text, table_cell=False):
    """Escape HTML-sensitive characters in markdown text, preserving code blocks.

    Scans the text character by character, tracking whether we're inside
    an inline code span (``...``) or a fenced code block (````` ... `````).
    Only escapes ``&``, ``<``, ``>``, ``"``, ``'``, ``{`` and ``}`` when outside of code
    regions.

    When *table_cell* is ``True`` (for content inside markdown table cells):

    * Fenced code blocks (````` ... `````) are converted to
      ``<code>...</code>``, with their internal newlines replaced by
      ``<br />``.
    * Newlines outside code blocks are replaced by ``<br />``.
    """
    result = []
    i = 0
    n = len(text)

    while i < n:
        # -- Fenced code block opening: ``` (with optional language tag) ----
        if text[i] == "`" and i + 2 < n and text[i + 1] == "`" and text[i + 2] == "`":
            end = text.find("```", i + 3)
            if end != -1:
                content = text[i + 3 : end]
                if table_cell:
                    # Strip optional language tag (first line)
                    first_nl = content.find("\n")
                    lang = None
                    if first_nl != -1:
                        lang = content[:first_nl]
                        content = content[first_nl + 1:]
                    content = content.rstrip("\n")
                    # Escape HTML inside <code> so it renders literally
                    for char, entity in _ESCAPE.items():
                        content = content.replace(char, entity)
                    content = content.replace("\n", "<br />")
                    tags = ""
                    if lang:
                        tags = f'lang="{lang}"'
                    result.append(f"<pre><code {tags}>{content}</code></pre>")
                else:
                    result.append(text[i : end + 3])
                i = end + 3
            else:
                # Unclosed fenced block — treat rest of text as code
                if table_cell:
                    content = text[i + 3:]
                    first_nl = content.find("\n")
                    lang = None
                    if first_nl != -1:
                        lang = content[:first_nl]
                        content = content[first_nl + 1:]
                    content = content.rstrip("\n")
                    for char, entity in _ESCAPE.items():
                        content = content.replace(char, entity)
                    content = content.replace("\n", "<br />")
                    tags = ""
                    if lang:
                        tags = f'lang="{lang}"'
                    result.append(f"<pre><code {tags}>{content}</code></pre>")
                else:
                    result.append(text[i:])
                break

        # -- Inline code span: `...` ----------------------------------------
        elif text[i] == "`":
            end = text.find("`", i + 1)
            if end != -1:
                result.append(text[i : end + 1])
                i = end + 1
            else:
                result.append("`")
                i += 1

        # -- Newline inside a table cell → <br /> ---------------------------
        elif text[i] == "\n" and table_cell:
            result.append("<br />")
            i += 1

        # -- Regular character: escape when outside code --------------------
        else:
            result.append(_ESCAPE.get(text[i], text[i]))
            i += 1

    return "".join(result)


# ---------------------------------------------------------------------------
# Line-return collapsing
# ---------------------------------------------------------------------------

#: Matches lines that start a markdown structural element — used to
#: decide that a newline *before* this line must be preserved.
_STRUCTURAL_LINE = re.compile(
    r"^("
    r"\s*[-*+] "        # unordered list item
    r"|\s*\d+[.)]\s"   # ordered list item
    r"|#{1,6}\s"        # heading
    r"|>{1}\s?"         # blockquote
    r"|```"             # fenced code block delimiter
    r"|---+"            # horizontal rule (3+ dashes)
    r"|\*\*\S"          # bold start at beginning of line
    r")"
    r"|.{0,40}:\s*$"   # short line ending with ":" (label / definition)
)

#: Matches lines that are standalone structural elements — these should
#: never absorb subsequent lines into themselves.
_STANDALONE_STRUCTURAL = re.compile(
    r"^("
    r"\s*[-*+] "        # unordered list item
    r"|\s*\d+[.)]\s"   # ordered list item
    r"|#{1,6}\s"        # heading
    r"|>{1}\s?"         # blockquote
    r"|---+"            # horizontal rule
    r"|\*\*\S"          # bold start
    r")"
)


def collapse_line_returns(text):
    """Remove soft-wrap newlines while preserving paragraph breaks and
    structurally significant line returns.

    Rules
    -----
    * Blank lines (paragraph separators) are always preserved.
    * A newline before a structural markdown line (list item, heading,
      code fence, HR, blockquote, indented text, bold label) is preserved.
    * Lines inside fenced code blocks are never touched.
    * All other newlines (soft wraps) are replaced with a single space.
    """
    lines = text.split("\n")
    result = []
    in_code_block = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Toggle fenced code block state
        if line.lstrip().startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            i += 1
            continue

        # Inside a code block: preserve everything as-is
        if in_code_block:
            result.append(line)
            i += 1
            continue

        # Blank line: preserve as paragraph separator
        if line.strip() == "":
            result.append(line)
            i += 1
            continue

        # Non-blank, non-code line outside a code block:
        # absorb following soft-wrap lines into this one.
        # But if this line is itself a standalone structural element
        # (HR, list item, heading, etc.), don't merge anything into it.
        merged = line
        if not _STANDALONE_STRUCTURAL.match(line):
            while i + 1 < len(lines):
                next_line = lines[i + 1]

                # Stop merging at blank lines (paragraph break)
                if next_line.strip() == "":
                    break

                # Stop merging at code fence boundaries
                if next_line.lstrip().startswith("```"):
                    break

                # Stop merging at structural markdown lines
                if _STRUCTURAL_LINE.match(next_line):
                    break

                # Otherwise it's a soft wrap — join with a space
                merged = merged + " " + next_line
                i += 1

        result.append(merged)
        i += 1

    return "\n".join(result)


# ---------------------------------------------------------------------------
# High-level formatting filters (registered as Jinja2 filters)
# ---------------------------------------------------------------------------


def format_description(description):
    """Collapse soft wraps then sanitize for use inside an MDX table cell.

    Handles ``None`` and non-string values gracefully.
    """
    if not description:
        return ""
    return sanitize_outside_codeblocks(
        collapse_line_returns(str(description)), table_cell=True
    )


def format_choices(choices):
    """Render a list of choices as ``<br />``-separated list items,
    sanitising any HTML-sensitive characters."""
    if isinstance(choices, str):
        choices = [c.strip() for c in choices.split(",")]

    return "<br />".join(
        [li(sanitize_outside_codeblocks(str(c))) for c in choices]
    ) if choices else ""
