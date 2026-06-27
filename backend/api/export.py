import io
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger("kaveri.export")

router = APIRouter()


class ConversationEntry(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    intent: Optional[str] = None
    sources: Optional[List[str]] = None
    confidence: Optional[str] = None
    timestamp: Optional[str] = None


class ExportPDFRequest(BaseModel):
    session_id: str
    conversation: List[ConversationEntry]
    title: Optional[str] = "KAVERI Intelligence Report"


def _build_pdf(request: ExportPDFRequest) -> bytes:
    """Generate a PDF intelligence report using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )

    # Color palette — KSP blue theme
    ksp_blue = HexColor("#1a3a6b")
    ksp_gold = HexColor("#c8a94a")
    ksp_light_blue = HexColor("#e8f0f7")
    critical_red = HexColor("#c0392b")
    high_orange = HexColor("#d35400")
    medium_yellow = HexColor("#f39c12")
    low_green = HexColor("#27ae60")

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "KAVERITitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=white,
        alignment=TA_CENTER,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "KAVERISubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=ksp_gold,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=ksp_blue,
        fontName="Helvetica-Bold",
        spaceBefore=12,
        spaceAfter=6,
        borderPad=4,
    )
    user_query_style = ParagraphStyle(
        "UserQuery",
        parent=styles["Normal"],
        fontSize=10,
        textColor=HexColor("#2c3e50"),
        fontName="Helvetica-Bold",
        leftIndent=10,
        spaceBefore=8,
        spaceAfter=4,
        backColor=ksp_light_blue,
        borderPad=6,
    )
    ai_response_style = ParagraphStyle(
        "AIResponse",
        parent=styles["Normal"],
        fontSize=10,
        textColor=black,
        leftIndent=10,
        spaceBefore=4,
        spaceAfter=8,
        leading=14,
    )
    meta_style = ParagraphStyle(
        "MetaInfo",
        parent=styles["Normal"],
        fontSize=8,
        textColor=HexColor("#7f8c8d"),
        leftIndent=10,
        spaceAfter=4,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=HexColor("#95a5a6"),
        alignment=TA_CENTER,
    )

    story = []

    # --- Header Banner ---
    now = datetime.utcnow().strftime("%d %B %Y, %H:%M UTC")
    header_data = [
        [Paragraph("KAVERI", title_style)],
        [Paragraph("Karnataka AI for Violence, Evidence, and Risk Intelligence", subtitle_style)],
        [Paragraph("Karnataka State Police | SCRB Intelligence Platform", subtitle_style)],
    ]
    header_table = Table(header_data, colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ksp_blue),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5 * cm))

    # --- Report Metadata ---
    meta_data = [
        ["Report Title:", request.title],
        ["Session ID:", request.session_id],
        ["Generated:", now],
        ["Classification:", "RESTRICTED — LAW ENFORCEMENT USE ONLY"],
        ["Queries:", str(len([e for e in request.conversation if e.role == "user"]))],
    ]
    meta_table = Table(meta_data, colWidths=[4 * cm, doc.width - 4 * cm])
    meta_table.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONT", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), ksp_blue),
        ("GRID", (0, 0), (-1, -1), 0.25, HexColor("#bdc3c7")),
        ("BACKGROUND", (0, 0), (-1, -1), ksp_light_blue),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=ksp_gold))
    story.append(Spacer(1, 0.3 * cm))

    # --- Conversation Section ---
    story.append(Paragraph("Intelligence Queries & Responses", section_header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#bdc3c7")))
    story.append(Spacer(1, 0.2 * cm))

    confidence_colors = {
        "HIGH": low_green,
        "MEDIUM": medium_yellow,
        "LOW": critical_red,
    }

    for idx, entry in enumerate(request.conversation):
        if entry.role == "user":
            q_num = sum(1 for e in request.conversation[:idx + 1] if e.role == "user")
            content = [
                KeepTogether([
                    Paragraph(
                        f"Q{q_num}: {_safe_text(entry.content)}",
                        user_query_style,
                    )
                ])
            ]
            story.extend(content)

        elif entry.role == "assistant":
            # Response text
            response_lines = entry.content.split("\n")
            for line in response_lines:
                line = line.strip()
                if line:
                    story.append(Paragraph(_safe_text(line), ai_response_style))

            # Metadata row: intent, sources, confidence
            meta_parts = []
            if entry.intent:
                meta_parts.append(f"Intent: {entry.intent}")
            if entry.sources:
                meta_parts.append(f"Sources: {' | '.join(entry.sources)}")
            if entry.confidence:
                conf = entry.confidence.upper()
                color = confidence_colors.get(conf, black)
                meta_parts.append(f"Confidence: {conf}")

            if meta_parts:
                meta_text = "  ·  ".join(meta_parts)
                story.append(Paragraph(meta_text, meta_style))

            if entry.timestamp:
                story.append(Paragraph(f"Time: {entry.timestamp}", meta_style))

            story.append(HRFlowable(width="80%", thickness=0.25, color=HexColor("#ecf0f1")))
            story.append(Spacer(1, 0.15 * cm))

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=ksp_blue))
    story.append(Spacer(1, 0.2 * cm))

    # --- Footer ---
    footer_text = (
        f"KAVERI — Karnataka State Police Crime Intelligence Platform | "
        f"Generated: {now} | "
        f"Session: {request.session_id[:8]}... | "
        f"RESTRICTED — LAW ENFORCEMENT USE ONLY"
    )
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _safe_text(text: str) -> str:
    """Escape special ReportLab XML characters."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


@router.post("/pdf")
async def export_pdf(request: ExportPDFRequest):
    """
    Generate a PDF intelligence report from a KAVERI conversation.

    The PDF includes:
    - KAVERI header with KSP branding
    - Session metadata
    - All queries and AI responses with FIR citations
    - Intent classification, data sources, confidence scores per response
    - Restricted classification footer
    """
    if not request.conversation:
        raise HTTPException(status_code=400, detail="Conversation is empty")

    try:
        pdf_bytes = _build_pdf(request)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="ReportLab not installed. Add reportlab to requirements.txt.",
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"KAVERI_Report_{request.session_id[:8]}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
