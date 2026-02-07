"""
PowerPoint (PPTX) generation service.

Converts a Presentation schema into a styled .pptx file using python-pptx.
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING, Optional

from pptx import Presentation as make_pptx
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

if TYPE_CHECKING:
    from pptx.presentation import Presentation as PptxPresentationType

from schemas.presentation import Presentation as PresentationModel, Slide as SlideModel

logger = logging.getLogger(__name__)

# ── Colour palette ──────────────────────────────────────────────────────────
_PURPLE_DARK = RGBColor(0x4A, 0x00, 0x82)
_PURPLE_MID = RGBColor(0x6B, 0x21, 0xA8)
_PURPLE_LIGHT = RGBColor(0x7C, 0x3A, 0xED)
_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_GRAY_700 = RGBColor(0x37, 0x41, 0x51)
_GRAY_500 = RGBColor(0x6B, 0x72, 0x80)
_AMBER_700 = RGBColor(0xB4, 0x53, 0x09)
_SKY_700 = RGBColor(0x03, 0x69, 0xA1)


def _add_background(slide_obj, color: RGBColor) -> None:
    """Set a solid background colour on *slide_obj*."""
    background = slide_obj.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_textbox(slide_obj, left, top, width, height):
    """Shortcut that returns (shape, text_frame)."""
    shape = slide_obj.shapes.add_textbox(left, top, width, height)
    return shape, shape.text_frame


def _set_paragraph(
    text_frame,
    text: str,
    *,
    font_size: int = 18,
    bold: bool = False,
    color: RGBColor = _GRAY_700,
    alignment=PP_ALIGN.LEFT,
    space_before: Optional[int] = None,
    space_after: Optional[int] = None,
):
    """Write *text* into the first paragraph of *text_frame*."""
    text_frame.word_wrap = True
    para = text_frame.paragraphs[0]
    para.text = text
    para.font.size = Pt(font_size)
    para.font.bold = bold
    para.font.color.rgb = color
    para.alignment = alignment
    if space_before is not None:
        para.space_before = Pt(space_before)
    if space_after is not None:
        para.space_after = Pt(space_after)


def _add_paragraph(
    text_frame,
    text: str,
    *,
    font_size: int = 18,
    bold: bool = False,
    color: RGBColor = _GRAY_700,
    alignment=PP_ALIGN.LEFT,
    space_before: Optional[int] = None,
    space_after: Optional[int] = None,
):
    """Append a new paragraph to *text_frame*."""
    para = text_frame.add_paragraph()
    para.text = text
    para.font.size = Pt(font_size)
    para.font.bold = bold
    para.font.color.rgb = color
    para.alignment = alignment
    if space_before is not None:
        para.space_before = Pt(space_before)
    if space_after is not None:
        para.space_after = Pt(space_after)
    return para


# ── Slide builders ──────────────────────────────────────────────────────────


def _build_title_slide(
    prs: PptxPresentationType, presentation: PresentationModel
) -> None:
    """Create the opening title slide with a purple gradient-like background."""
    slide_layout = prs.slide_layouts[6]  # Blank
    slide_obj = prs.slides.add_slide(slide_layout)
    _add_background(slide_obj, _PURPLE_DARK)

    # Course title (small, top)
    _, tf = _add_textbox(slide_obj, Inches(1), Inches(1.5), Inches(8), Inches(0.8))
    _set_paragraph(
        tf,
        presentation.course_title,
        font_size=16,
        color=RGBColor(0xD8, 0xB4, 0xFE),
        alignment=PP_ALIGN.CENTER,
    )

    # Lesson title (large, centre)
    _, tf = _add_textbox(slide_obj, Inches(0.8), Inches(2.4), Inches(8.4), Inches(1.6))
    _set_paragraph(
        tf,
        presentation.lesson_title,
        font_size=36,
        bold=True,
        color=_WHITE,
        alignment=PP_ALIGN.CENTER,
    )

    # Class badge
    _, tf = _add_textbox(slide_obj, Inches(3.5), Inches(4.2), Inches(3), Inches(0.6))
    _set_paragraph(
        tf,
        f"Class {presentation.class_number}  •  {len(presentation.slides)} slides",
        font_size=14,
        color=RGBColor(0xD8, 0xB4, 0xFE),
        alignment=PP_ALIGN.CENTER,
    )


def _build_content_slide(prs: PptxPresentationType, slide: SlideModel) -> None:
    """Create one content slide with bullet points, speaker notes & visual hint."""
    slide_layout = prs.slide_layouts[6]  # Blank
    slide_obj = prs.slides.add_slide(slide_layout)

    # ── Slide number badge + title bar ──
    _, tf = _add_textbox(slide_obj, Inches(0.4), Inches(0.3), Inches(0.5), Inches(0.45))
    _set_paragraph(
        tf,
        str(slide.slide_number),
        font_size=12,
        bold=True,
        color=_PURPLE_MID,
        alignment=PP_ALIGN.CENTER,
    )

    _, tf = _add_textbox(slide_obj, Inches(1.0), Inches(0.3), Inches(8.2), Inches(0.5))
    _set_paragraph(tf, slide.title, font_size=24, bold=True, color=_PURPLE_DARK)

    # Thin purple rule
    line_shape = slide_obj.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.4), Inches(0.85), Inches(9.2), Pt(2)
    )
    line_shape.fill.solid()
    line_shape.fill.fore_color.rgb = _PURPLE_LIGHT
    line_shape.line.fill.background()

    # ── Bullet points ──
    bullet_top = 1.1
    _, tf = _add_textbox(
        slide_obj, Inches(0.6), Inches(bullet_top), Inches(8.8), Inches(3.5)
    )
    tf.word_wrap = True

    for i, point in enumerate(slide.bullet_points):
        if i == 0:
            _set_paragraph(
                tf, f"•  {point}", font_size=18, color=_GRAY_700, space_after=6
            )
        else:
            _add_paragraph(
                tf,
                f"•  {point}",
                font_size=18,
                color=_GRAY_700,
                space_before=4,
                space_after=6,
            )

    # ── Visual suggestion (small italic hint at bottom) ──
    if slide.visual_suggestion:
        _, tf = _add_textbox(
            slide_obj, Inches(0.6), Inches(4.8), Inches(8.8), Inches(0.6)
        )
        para = tf.paragraphs[0]
        para.text = f"💡 Visual: {slide.visual_suggestion}"
        para.font.size = Pt(11)
        para.font.italic = True
        para.font.color.rgb = _SKY_700

    # ── Speaker notes ──
    if slide.speaker_notes:
        notes_slide = slide_obj.notes_slide
        notes_tf = notes_slide.notes_text_frame
        if notes_tf is not None:
            notes_tf.text = slide.speaker_notes


# ── Public API ──────────────────────────────────────────────────────────────


def generate_pptx(presentation: PresentationModel) -> bytes:
    """
    Build a .pptx file from a *PresentationModel* schema and return the raw bytes.

    Parameters
    ----------
    presentation : PresentationModel
        Validated Pydantic model with course_title, lesson_title,
        class_number, and a list of slides.

    Returns
    -------
    bytes
        The binary content of the generated .pptx file.
    """
    prs = make_pptx()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)  # 16:9

    _build_title_slide(prs, presentation)

    for slide in presentation.slides:
        _build_content_slide(prs, slide)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)

    logger.info(
        "Generated PPTX: %s – %s (class %d, %d slides)",
        presentation.course_title,
        presentation.lesson_title,
        presentation.class_number,
        len(presentation.slides),
    )
    return buf.getvalue()
