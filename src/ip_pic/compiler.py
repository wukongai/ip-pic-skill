"""Exact IP-only compiler extracted from the private upstream behavior."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

from . import character_performance, director, typography
from .canvas import resolve_size
from .errors import IPPicError
from .handoff import build_render_handoff
from .profiles import load_character_profile
from .project_resolver import apply_project_customization
from .references import compile_reference_plan
from .selection import Selection, require_confirmed_selection
from .styles import resolve_project_style, resolve_style
from .templates import list_templates, resolve_template


IP_SCENES = {"ip_article_illustration", "ip_video_keyframe"}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_text(item) for item in value if _text(item)]
    if _text(value):
        return [_text(value)]
    return []


def _clip(value: Any, limit: int) -> str:
    text = _text(value)
    return text if len(text) <= limit else text[:limit]


def _render_config(value: Any, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if item in (None, "", [], {}):
                continue
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}- {key}:")
                lines.extend(_render_config(item, indent + 1))
            else:
                lines.append(f"{prefix}- {key}: {item}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_render_config(item, indent + 1))
            else:
                lines.append(f"{prefix}- {item}")
        return lines
    return [f"{prefix}- {value}"] if value not in (None, "") else []


def _append_block(lines: list[str], title: str, value: Any) -> None:
    rendered = _render_config(value)
    if rendered:
        lines.extend(["", f"【{title}】", *rendered])


def _append_list(lines: list[str], title: str, values: list[str]) -> None:
    if values:
        lines.extend(["", f"【{title}】"])
        lines.extend(f"- {item}" for item in values)


def normalize_brief(brief: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(brief)
    scene = _text(result.get("scene")) or _text(template.get("scene"))
    if scene not in IP_SCENES:
        raise IPPicError(f"ip-pic does not support scene {scene!r}")
    content = result.get("content") if isinstance(result.get("content"), dict) else {}
    visual = result.get("visual") if isinstance(result.get("visual"), dict) else {}
    composition = (
        result.get("composition")
        if isinstance(result.get("composition"), dict)
        else {}
    )
    directed = director.merge_missing(
        {
            **result,
            "scene": scene,
            "content": content,
            "visual": visual,
            "composition": composition,
        },
        template,
    )
    visual = directed["visual"]
    composition = directed["composition"]
    headline = _text(content.get("headline"))
    if not headline:
        raise IPPicError("brief.content.headline 不能为空")
    result.update(
        {
            "schema_version": _text(result.get("schema_version"))
            or "image-asset-brief/v1",
            "id": _text(result.get("id")) or "ip-pic-item",
            "scene": scene,
            "goal": _text(result.get("goal")) or "single_image_asset",
            "audience": _text(result.get("audience")) or "目标读者",
            "content": {
                "headline": _clip(headline, 32),
                "subheadline": _clip(content.get("subheadline"), 48),
                "summary": _clip(content.get("summary"), 72),
                "points": [_clip(item, 32) for item in _list(content.get("points"))[:4]],
                "cta": _clip(content.get("cta"), 24),
                "brand": _clip(content.get("brand"), 24),
            },
            "visual": {
                "subject": _clip(visual.get("subject"), 640),
                "metaphors": [_clip(item, 24) for item in _list(visual.get("metaphors"))[:5]],
                "mood": _clip(
                    visual.get("mood")
                    or template.get("default_mood")
                    or "清晰、专业、有记忆点",
                    42,
                ),
                "must_show": _list(visual.get("must_show"))[:6],
                "avoid": _list(visual.get("avoid"))[:8],
                "authorized_assets": list(visual.get("authorized_assets", [])),
                "reference_strategy": copy.deepcopy(
                    visual.get("reference_strategy")
                ),
                "style_variant_id": _text(visual.get("style_variant_id")),
                "ip_profile": visual.get("ip_profile"),
            },
            "composition": copy.deepcopy(composition),
            "director": directed["director"],
        }
    )
    performance = character_performance.normalize(
        result["composition"].get("character_performance")
    )
    if performance is not None:
        result["composition"]["character_performance"] = performance
    if result["visual"].get("ip_profile") is not None:
        result["visual"]["ip_profile"] = load_character_profile(
            result["visual"]["ip_profile"]
        )
    return result


def _prompt_brief(brief: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(brief)
    value.pop("source_content", None)
    director_value = value.get("director")
    if isinstance(director_value, dict):
        director_value.pop("provenance", None)
    visual = value.get("visual")
    if isinstance(visual, dict):
        assets = visual.get("authorized_assets")
        if isinstance(assets, list):
            visual["authorized_assets"] = [
                {
                    key: item.get(key)
                    for key in ("id", "purpose", "ownership", "required")
                    if key in item
                }
                for item in assets
                if isinstance(item, dict)
            ]
        profile = visual.get("ip_profile")
        if isinstance(profile, dict) and isinstance(profile.get("references"), list):
            profile.pop("public_profile_resolution", None)
            profile.pop("source_priority", None)
            profile.pop("scope", None)
            profile["references"] = [
                {
                    key: item.get(key)
                    for key in ("id", "purpose", "authorized")
                    if key in item
                }
                for item in profile["references"]
                if isinstance(item, dict)
            ]
    return value


def _canvas_descriptor(size: str) -> tuple[str, str]:
    width_text, height_text = size.lower().split("x", 1)
    width, height = int(width_text), int(height_text)
    divisor = math.gcd(width, height)
    ratio = f"{width // divisor}:{height // divisor}"
    if width == height:
        return ratio, "方形"
    if width > height:
        return ratio, "横版"
    return ratio, "竖版"


def _adapt_template_canvas(value: Any, size: str) -> Any:
    ratio, orientation = _canvas_descriptor(size)
    if ratio == "16:9" and orientation == "横版":
        return value
    if isinstance(value, dict):
        return {
            key: _adapt_template_canvas(item, size)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_adapt_template_canvas(item, size) for item in value]
    if not isinstance(value, str):
        return value
    result = value.replace("16:9", ratio)
    if orientation != "横版":
        result = result.replace("横版画面", f"{orientation}画面")
        result = result.replace("横版", orientation)
    return result


def compile_prompt(
    template: dict[str, Any],
    brief: dict[str, Any],
    size: str,
    style_profile: dict[str, Any] | None,
) -> str:
    prompt_template = _adapt_template_canvas(template, size)
    content = brief["content"]
    visual = brief["visual"]
    composition = brief["composition"]
    mode = _text(brief.get("delivery_mode"))
    direct = mode == "direct-integrated"
    two_step = mode == "two-step-publish"
    video_raw = brief["scene"] == "ip_video_keyframe"
    raw_ratio, _raw_orientation = _canvas_descriptor(size)
    lines = [
        _text(prompt_template.get("prompt_role"))
        or "你是资深中文视觉设计师和 AI 生图提示词编排师。",
        (
            "请生成一张用于二次扩展排版的无字原始视觉素材。只生成主体画面，不要生成任何文字、标题、字幕或标签。"
            if two_step or video_raw
            else "请一次生成一张图文融合的 IP 正文配图。文字必须是画面中的少量短标题、标签或手写说明，与人物、物件和动作共同表达一个判断；不要生成长段落、文字墙或乱码。"
            if direct
            else "请生成一张可直接用于内容发布的中文图片素材。"
        ),
        "",
        "【图片规格】",
        f"- 尺寸: {size}",
        *(
            [f"- 当前 raw 画布: {raw_ratio}"]
            if two_step or video_raw
            else []
        ),
        f"- 模板: {_text(prompt_template.get('name')) or _text(prompt_template.get('id'))}",
        f"- 场景: {brief['scene']}",
        f"- 目标: {brief['goal']}",
        f"- 受众: {brief['audience']}",
        "",
        "【用户自己的内容】",
        f"- 主标题: {content['headline']}",
    ]
    for key, label in (
        ("subheadline", "副标题"),
        ("summary", "摘要"),
        ("cta", "行动引导"),
        ("brand", "品牌/署名"),
    ):
        if _text(content.get(key)):
            lines.append(f"- {label}: {content[key]}")
    _append_list(lines, "要点", _list(content.get("points")))
    lines.extend(["", "【主视觉意图】"])
    if _text(visual.get("subject")):
        lines.append(f"- 主体: {visual['subject']}")
    if _text(visual.get("mood")):
        lines.append(f"- 情绪: {visual['mood']}")
    _append_list(lines, "视觉隐喻", _list(visual.get("metaphors")))
    _append_list(lines, "必须出现", _list(visual.get("must_show")))
    _append_list(lines, "必须避免", _list(visual.get("avoid")))
    composition_for_prompt = copy.deepcopy(composition)
    performance = composition_for_prompt.pop("character_performance", None)
    _append_block(lines, "构图意图", composition_for_prompt)
    lines.extend(
        [
            "",
            "【底部留白硬约束】",
            "- 左右两侧可以满，可以让人物、装置或动作线接近边缘；不要为了留白把画面缩成居中卡片。",
            "- 画布底部最后 12%-15% 必须保留连续、干净的低细节空间，作为后续标题带、字幕和安全边距的缓冲。",
            "- 重要物件、人物脚部、底座、卡片、箭头、绳索和动作线不得贴到或切出画布底边。",
            "- 底部留白应与背景自然融合，不要画白色矩形占位框、字幕框或装饰横条。",
        ]
    )
    if isinstance(performance, dict):
        lines.extend(["", "【角色表演】", *character_performance.prompt_lines(performance)])
    lines.extend(
        [
            "",
            "【稳定内容结构 image_brief】",
            "下面 JSON 是本图的唯一内容结构来源。请严格按照 content/visual/composition 渲染，不要新增无关模块。",
            "```json",
            json.dumps(_prompt_brief(brief), ensure_ascii=False, indent=2),
            "```",
        ]
    )
    for title, key in (
        ("模板参数", "template_parameters"),
        ("内容契约", "content_contract"),
        ("版式结构", "layout"),
    ):
        _append_block(lines, title, prompt_template.get(key))
    if style_profile:
        lines.extend(
            [
                "",
                "【用户确认的 IP 渲染风格】",
                "下方 profile 只覆盖材质、线条、色彩、形状和表面语气。它不得改变当前业务场景、文字策略、画幅、布局或角色身份。",
            ]
        )
        lines.extend(_render_config(style_profile))
    else:
        _append_block(lines, "视觉风格", prompt_template.get("style"))
    for title, key in (
        ("参考图复用政策", "reference_policy"),
        ("画布稳定性", "canvas"),
        ("信息架构", "information_architecture"),
        ("内容解析规则", "extraction_rules"),
        ("标题区规范", "header"),
        ("主体区规范", "body"),
        ("页脚区规范", "footer"),
        ("视觉元素规则", "visual_elements"),
        ("稳定生成协议", "stability_protocol"),
        ("质量门禁", "quality_gates"),
        ("结构化质量门禁", "quality_gates_v2"),
        ("文字规则", "copy_rules"),
        ("硬性约束", "constraints"),
    ):
        _append_block(lines, title, prompt_template.get(key))
    if direct:
        lines.extend(
            [
                "",
                "【直出中文字样式】",
                *typography.direct_integrated_prompt_lines(),
                "",
                "【一次生成图文融合硬约束】",
                "- 这是一次生成的正文配图，不进入二次标题带扩展；IP、物件、箭头和少量中文短标注必须组成一个整体画面。",
                "- 只允许少量、短、清晰的中文标题或标签；不要生成长段摘要、密集说明、英文乱码或装饰性伪字。",
                "- 所有文字必须服务于当前判断、流程或生意关系，并与人物动作和物件关系共同表达。",
            ]
        )
    if _text(prompt_template.get("negative_prompt")):
        lines.extend(["", "【避免】", _text(prompt_template.get("negative_prompt"))])
    if two_step:
        lines.extend(
            [
                "",
                "请直接生成无字原始主视觉图片。不要输出解释，不要加标题、字幕、标签、logo 或水印。",
            ]
        )
    elif direct:
        lines.extend(
            [
                "",
                "请直接生成一次性图文融合成品。不要输出解释，不要加无关 logo、水印或额外文案。",
            ]
        )
    elif video_raw:
        lines.extend(
            [
                "",
                "请直接生成无字视频关键帧 raw。不要输出解释，不要生成标题、字幕、标签、logo、水印或伪文字；最终中文由 video-text-overlay/v1 确定性合成。",
            ]
        )
    else:
        lines.extend(["", "请直接生成成品图片。不要输出解释，不要加无关水印。"])
    return "\n".join(lines).rstrip() + "\n"


def _default_template(root: Path, scene: str) -> dict[str, Any]:
    defaults = [
        item
        for item in list_templates(root, formal_only=True)
        if item.get("scene") == scene and item.get("default_for_scene") is True
    ]
    if len(defaults) != 1:
        raise IPPicError(f"scene {scene!r} must have exactly one formal default template")
    return defaults[0]


def _manifest(
    *,
    template: dict[str, Any],
    brief: dict[str, Any],
    prompt_path: Path,
    output_dir: Path,
    size: str,
    selection: Selection | None,
    project_customization: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item_id = brief["id"]
    raw = output_dir / "image" / f"{item_id}.png"
    final = output_dir / "final" / f"{item_id}.png"
    assets = brief["visual"].get("authorized_assets", [])
    reference_plan = compile_reference_plan(
        item_id=item_id,
        template=template,
        brief=brief,
        authorized_assets=assets,
        prompt_file=prompt_path,
        size=size,
        output_dir=output_dir,
    )
    manifest: dict[str, Any] = {
        "tool": "ip-pic",
        "compile_only": True,
        "template": {"id": template["id"], "name": template.get("name")},
        "brief": {
            "id": item_id,
            "scene": brief["scene"],
            "goal": brief["goal"],
            "headline": brief["content"]["headline"],
            "delivery_mode": brief.get("delivery_mode"),
            "style_variant_id": brief["visual"].get("style_variant_id"),
        },
        "inputs": {"authorized_visual_assets": assets},
        "reference_plan": reference_plan,
        "size": size,
        "prompt_file": str(prompt_path),
        "output_dir": str(output_dir),
        "expected_outputs": {
            "raw_image": str(raw),
            "final_image": str(final),
        },
        "director_plan": brief["director"],
        "visual_qa": {
            "required": True,
            "status": "pending",
            "attachment_evidence_is_visual_qa": False,
        },
    }
    if project_customization:
        manifest["project_customization"] = copy.deepcopy(
            project_customization
        )
    if _text(brief["visual"].get("style_variant_id")):
        manifest["style_variant_id"] = brief["visual"]["style_variant_id"]
    if reference_plan.get("selection_required"):
        manifest["render_candidates"] = reference_plan.get("candidates", [])
    else:
        manifest["render_handoff"] = build_render_handoff(
            item_id=item_id,
            prompt_file=prompt_path,
            size=size,
            output_dir=output_dir / "image",
            assets=reference_plan.get("selected_assets", []),
        )
    if selection is None and brief["scene"] == "ip_video_keyframe":
        layout_variant = _text(brief["composition"].get("text_layout_variant"))
        if layout_variant not in {"square-left", "square-right"}:
            raise IPPicError(
                "1:1 IP 视频 brief 必须声明 composition.text_layout_variant"
            )
        manifest["video_text_overlay"] = {
            "schema_version": "video-text-overlay/v1",
            "output_dir": str(output_dir / "final"),
            "items": [
                {
                    "id": item_id,
                    "input_image": str(raw),
                    "output_file": f"{item_id}.png",
                    "layout_variant": layout_variant,
                    "kicker": brief["content"]["subheadline"],
                    "headline": brief["content"]["headline"],
                    "support": brief["content"]["summary"],
                    "bottom_safe_y": 1740,
                }
            ],
        }
        manifest["delivery"] = {
            "mode": "video-two-step-overlay",
            "operation_count": 2,
            "deliverable": "final_image",
            "status": "awaiting_raw_render_then_video_text_overlay",
            "raw_publishable": False,
            "raw_retained_as": "technical_sidecar",
        }
        manifest["visual_qa"]["deliverable_under_review"] = "final_image"
        manifest["visual_qa"]["required_checks"] = [
            "ip_identity",
            "semantic_action",
            "raw_has_no_text",
            "final_title_present",
            "final_title_legible",
            "final_text_does_not_overlap_visual",
            "subtitle_safe_zone_clear",
            "raw_not_published_as_final",
        ]
        return manifest
    if selection is None:
        return manifest
    mode = selection.delivery_mode
    if mode == "direct-integrated":
        manifest["expected_outputs"]["final_image"] = str(raw)
        manifest["delivery"] = {
            "mode": mode,
            "operation_count": 1,
            "deliverable": "final_image",
            "status": "awaiting_direct_render",
            "text_integrated": True,
            "raw_is_internal_alias": True,
        }
        manifest["visual_qa"]["deliverable_under_review"] = "final_image"
        manifest["visual_qa"]["required_checks"] = [
            "ip_identity",
            "semantic_action",
            "integrated_text_present",
            "integrated_text_legible",
            "text_does_not_overlap_subject",
        ]
    else:
        final = output_dir / "publish" / "final" / f"{item_id}.png"
        manifest["expected_outputs"]["final_image"] = str(final)
        publish_layout: dict[str, Any] = {
            "schema_version": "image-publish-layout/v1",
            "id": f"{item_id}-publish-layout",
            "preset": _text(brief["composition"].get("publish_preset")) or "square_1_1",
            "layout_profile": "title-band-top",
            "source_image": str(raw),
            "output_image": str(final),
            "title": {
                "kicker": brief["content"]["subheadline"],
                "headline": brief["content"]["headline"],
                "support": brief["content"]["summary"],
                "footer": brief["content"]["brand"],
            },
        }
        extension = _text(brief["composition"].get("publish_extension"))
        if extension:
            publish_layout["extension_id"] = extension
        manifest["publish_layout"] = publish_layout
        manifest["delivery"] = {
            "mode": mode,
            "operation_count": 2,
            "deliverable": "final_image",
            "status": "awaiting_raw_render_then_publish_layout",
            "raw_publishable": False,
            "raw_retained_as": "technical_sidecar",
        }
        manifest["visual_qa"]["deliverable_under_review"] = "final_image"
        manifest["visual_qa"]["required_checks"] = [
            "raw_has_no_text",
            "final_title_band_present",
            "final_title_legible",
            "final_text_does_not_overlap_visual",
            "raw_not_published_as_final",
        ]
    return manifest


def compile_request(
    root: Path,
    input_brief: dict[str, Any],
    output_dir: Path | None = None,
    *,
    template_id: str | None = None,
    write: bool = True,
    project_root: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if input_brief.get("project_customization") not in (None, "", {}):
        if project_root is None:
            raise IPPicError(
                "brief 使用 project_customization 时必须提供 project_root / --project-root"
            )
    project_context: dict[str, Any] = {}
    working_brief = copy.deepcopy(input_brief)
    if project_root is not None:
        working_brief, project_context = apply_project_customization(
            root,
            Path(project_root),
            working_brief,
        )
    scene = _text(working_brief.get("scene"))
    template = (
        resolve_template(root, template_id)
        if template_id
        else _default_template(root, scene)
    )
    if template.get("scene") != scene:
        raise IPPicError("render style or template must not change the business scene")
    brief = normalize_brief(working_brief, template)
    project_style_id = project_context.get("project_style_id")
    selection = require_confirmed_selection(
        root,
        brief,
        project_style_id=(
            project_style_id if isinstance(project_style_id, str) else None
        ),
    )
    style_profile = None
    if selection is not None:
        brief["delivery_mode"] = selection.delivery_mode
        brief["selection_receipt"] = selection.as_receipt()
        brief["visual"]["style_variant_id"] = selection.style_variant_id
        if selection.publish_extension_id:
            brief["composition"]["publish_extension"] = (
                selection.publish_extension_id
            )
        if (
            isinstance(project_style_id, str)
            and selection.style_variant_id == project_style_id
        ):
            style_profile = resolve_project_style(
                root,
                project_context["_style_asset"],
            )
        else:
            style_profile = resolve_style(root, selection.style_variant_id)
        size = resolve_size(selection.canvas, _text(template.get("size")))
    else:
        size = _text(brief["composition"].get("size")) or _text(template.get("size"))
        style_id = _text(brief["visual"].get("style_variant_id"))
        if not style_id:
            style_file = _text(template.get("render_style_profile"))
            if style_file:
                style_id = Path(style_file).stem.removesuffix("-v1")
        if style_id:
            if (
                isinstance(project_style_id, str)
                and style_id == project_style_id
            ):
                style_profile = resolve_project_style(
                    root,
                    project_context["_style_asset"],
                )
            else:
                style_profile = resolve_style(root, style_id)
            brief["visual"]["style_variant_id"] = style_profile["id"]
    output = (output_dir or root / "outputs" / brief["id"]).resolve()
    prompt_path = output / f"{brief['id']}.prompt.md"
    prompt = compile_prompt(template, brief, size, style_profile)
    manifest = _manifest(
        template=template,
        brief=brief,
        prompt_path=prompt_path,
        output_dir=output,
        size=size,
        selection=selection,
        project_customization=project_context.get("public"),
    )
    paths = {
        "brief": str(output / "image_brief.json"),
        "director": str(output / "ip-director-plan.json"),
        "prompt": str(prompt_path),
        "manifest": str(output / "run-manifest.json"),
    }
    if "video_text_overlay" in manifest:
        paths["video_text_overlay"] = str(output / "video-text-overlay.json")
    if write:
        if output.exists():
            raise IPPicError(f"output directory already exists; refusing to overwrite: {output}")
        output.mkdir(parents=True)
        (output / "image_brief.json").write_text(
            json.dumps(brief, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "ip-director-plan.json").write_text(
            json.dumps(brief["director"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        prompt_path.write_text(prompt, encoding="utf-8")
        (output / "run-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if "video_text_overlay" in manifest:
            (output / "video-text-overlay.json").write_text(
                json.dumps(
                    manifest["video_text_overlay"],
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
    return {
        "brief": brief,
        "director_plan": brief["director"],
        "prompt": prompt,
        "manifest": manifest,
        "paths": paths,
    }
