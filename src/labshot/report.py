"""Optional automatic Word (.docx) lab report population engine."""

import os
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from labshot.storage import LabStorage


def find_default_template() -> Optional[Path]:
    """Look for CS345 Word template on Desktop or current directory."""
    candidates = [
        Path.home() / "Desktop/CS345_Linux_Lab_Template.docx",
        Path.home() / "Desktop/CS345_Linux_Lab_Report.docx",
        Path.cwd() / "CS345_Linux_Lab_Template.docx",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def generate_completed_docx(
    storage: LabStorage,
    template_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Optional[Path]:
    """Populate commands and screenshots into the CS345 Word template."""
    tmpl = template_path or find_default_template()
    if not tmpl or not tmpl.exists():
        return None

    dest = output_path or (Path.home() / "Desktop" / f"{storage.folder_name}_Completed.docx")

    meta = storage.load_metadata()
    questions_list = meta.get("questions", [])
    if not questions_list:
        return None

    # Map question number to record
    q_map = {q["number"]: q for q in questions_list if "number" in q}

    # Open template and create output zip
    temp_dest = dest.with_suffix(".tmp.docx")
    try:
        with zipfile.ZipFile(tmpl, "r") as zin, zipfile.ZipFile(temp_dest, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            doc_xml = zin.read("word/document.xml").decode("utf-8")
            rels_xml = zin.read("word/_rels/document.xml.rels").decode("utf-8")
            content_types_xml = zin.read("[Content_Types].xml").decode("utf-8")

            # 1. Ensure PNG content type in [Content_Types].xml
            if 'Extension="png"' not in content_types_xml:
                content_types_xml = content_types_xml.replace(
                    "</Types>",
                    '<Default Extension="png" ContentType="image/png"/></Types>'
                )

            # 2. Iterate through questions and replace $ and (Paste here)
            new_rels = []
            images_to_add = {}

            p_pattern = r'<w:p\b[^>]*>(?:(?!<w:p\b).)*?<w:t>\(Paste here\)</w:t>.*?</w:p>'

            for q_num in sorted(q_map.keys()):
                record = q_map[q_num]
                cmd_text = record.get("command", "").strip()
                shot_file = storage.get_screenshot_path(q_num)

                # Replace "$ " with "$ command"
                if "<w:t>$ </w:t>" in doc_xml:
                    escaped_cmd = cmd_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    doc_xml = doc_xml.replace(
                        "<w:t>$ </w:t>",
                        f'<w:t>$ {escaped_cmd}</w:t>',
                        1
                    )

                # Embed Screenshot if exists
                if shot_file.exists():
                    rel_id = f"rIdImg{q_num}"
                    img_target = f"media/img_q{q_num}.png"

                    new_rels.append(
                        f'<Relationship Id="{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{img_target}"/>'
                    )
                    images_to_add[img_target] = shot_file.read_bytes()

                    drawing_p = (
                        f'<w:p><w:pPr><w:spacing w:before="100" w:after="100"/><w:jc w:val="center"/></w:pPr>'
                        f'<w:r><w:drawing>'
                        f'<wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
                        f'<wp:extent cx="5212080" cy="3200400"/>'
                        f'<wp:effectExtent l="0" t="0" r="0" b="0"/>'
                        f'<wp:docPr id="{100 + q_num}" name="Picture {q_num}"/>'
                        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
                        f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                        f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                        f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                        f'<pic:nvPicPr><pic:cNvPr id="{100 + q_num}" name="Screenshot {q_num}"/><pic:cNvPicPr/></pic:nvPicPr>'
                        f'<pic:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="5212080" cy="3200400"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
                        f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
                    )

                    doc_xml = re.sub(p_pattern, drawing_p, doc_xml, count=1, flags=re.DOTALL)

            # Update document.xml.rels
            if new_rels:
                rels_insertion = "".join(new_rels)
                rels_xml = rels_xml.replace("</Relationships>", f"{rels_insertion}</Relationships>")

            # Validate XML before writing
            ET.fromstring(doc_xml)
            ET.fromstring(rels_xml)

            # Write modified XMLs and images
            zout.writestr("word/document.xml", doc_xml.encode("utf-8"))
            zout.writestr("word/_rels/document.xml.rels", rels_xml.encode("utf-8"))
            zout.writestr("[Content_Types].xml", content_types_xml.encode("utf-8"))

            for img_path, img_data in images_to_add.items():
                zout.writestr(f"word/{img_path}", img_data)

            # Copy all remaining files untouched
            for item in zin.infolist():
                if item.filename not in ("word/document.xml", "word/_rels/document.xml.rels", "[Content_Types].xml"):
                    zout.writestr(item, zin.read(item.filename))

        # Rename temp to final destination
        temp_dest.replace(dest)
        return dest
    except Exception as ex:
        if temp_dest.exists():
            temp_dest.unlink()
        return None


def convert_docx_to_pdf(docx_path: Path, output_dir: Optional[Path] = None) -> Optional[Path]:
    """Convert DOCX file to PDF using LibreOffice if available."""
    import subprocess
    if not shutil.which("soffice") and not shutil.which("libreoffice"):
        return None

    out_d = output_dir or docx_path.parent
    cmd_name = "soffice" if shutil.which("soffice") else "libreoffice"

    try:
        res = subprocess.run(
            [cmd_name, "--headless", "--convert-to", "pdf", str(docx_path), "--outdir", str(out_d)],
            capture_output=True, text=True, timeout=20
        )
        pdf_path = out_d / f"{docx_path.stem}.pdf"
        if pdf_path.exists():
            return pdf_path
    except Exception:
        pass
    return None
