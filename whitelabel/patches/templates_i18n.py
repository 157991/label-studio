"""
标注模板中文化模块 - 翻译 annotation_templates 下的 YAML 模板。

翻译内容：
- group: 模板分类名
- title: 模板标题
- details: 详情说明（只翻译标题/标签，不动技术内容）
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import BrandConfig


# 分类名翻译
GROUP_TRANSLATIONS = {
    "Computer Vision": "计算机视觉",
    "Natural Language Processing": "自然语言处理",
    "Audio/Speech Processing": "音频/语音处理",
    "Conversational AI": "对话式 AI",
    "Chat": "聊天",
    "Ranking & Scoring": "排序与评分",
    "Structured Data Parsing": "结构化数据解析",
    "Time Series Analysis": "时间序列分析",
    "Videos": "视频",
    "Generative AI": "生成式 AI",
    "Community Contributions": "社区贡献",
}

# 模板标题翻译
TITLE_TRANSLATIONS = {
    "Semantic Segmentation with Polygons": "多边形语义分割",
    "Semantic Segmentation with Masks": "掩码语义分割",
    "Object Detection with Bounding Boxes": "边界框目标检测",
    "OCR Labeling for PDFs": "PDF OCR 标注",
    "Keypoint Labeling": "关键点标注",
    "Image Captioning": "图像描述",
    "Image Classification": "图像分类",
    "Inventory Tracking": "库存跟踪",
    "Medical Image Classification with Bounding Boxes": "医学图像分类（边界框）",
    "Multi-page document annotation": "多页文档标注",
    "Optical Character Recognition": "光学字符识别 (OCR)",
    "Visual Genome": "视觉基因组标注",
    "Named Entity Recognition": "命名实体识别",
    "Text Classification": "文本分类",
    "Text Summarization": "文本摘要",
    "Question Answering": "问答系统",
    "Relation Extraction": "关系抽取",
    "Machine Translation": "机器翻译",
    "Content Moderation": "内容审核",
    "Speech Transcription": "语音转写",
    "Automatic Speech Recognition": "自动语音识别",
    "Automatic Speech Recognition using Segments": "分段式自动语音识别",
    "Speaker Segmentation": "说话人分割",
    "Sound Event Detection": "声音事件检测",
    "Signal Quality Detection": "信号质量检测",
    "Intent Classification": "意图分类",
    "Conversational Analysis": "对话分析",
    "Coreference Resolution & Entity Linking": "共指消解与实体链接",
    "Intent Classification and Slot Filling": "意图分类与槽位填充",
    "Response Generation": "回复生成",
    "Response Selection": "回复选择",
    "Chatbot Evaluation": "聊天机器人评估",
    "Chatbot Model Assessment": "聊天模型评估",
    "Evaluate Production Conversations for RLHF": "RLHF 生产对话评估",
    "Red-Teaming in Chat": "聊天红队测试",
    "Pairwise classification": "成对分类",
    "Pairwise regression": "成对回归",
    "Content-based Image Retrieval": "基于内容的图像检索",
    "Document Retrieval": "文档检索",
    "Search Page Ranking": "搜索页面排序",
    "ASR Hypotheses Selection": "ASR 候选结果选择",
    "Visual Ranker": "视觉排序器",
    "LLM Ranker": "LLM 排序器",
    "Freeform Metadata": "自由格式元数据",
    "HTML Entity Recognition": "HTML 实体识别",
    "PDF Classification": "PDF 分类",
    "Tabular Data": "表格数据",
    "Activity Recognition": "行为识别",
    "Change Point Detection": "变点检测",
    "Outliers & Anomaly Detection": "异常值与异常检测",
    "Signal Quality": "信号质量",
    "Time Series Forecasting": "时间序列预测",
    "Video Classification": "视频分类",
    "Video Frame Classification": "视频帧分类",
    "Video Object Tracking": "视频目标跟踪",
    "Video Timeline Segmentation": "视频时间线分割",
    "Text-to-Image Generation": "文本生成图像",
    "Supervised Language Model Fine-tuning": "监督式语言模型微调",
    "LLM Response Grading": "LLM 回复评分",
    "Human Preference collection for RLHF": "RLHF 人类偏好收集",
    "Fine-Tune an Agent with an LLM": "基于 LLM 的智能体微调",
    "Fine-Tune an Agent without an LLM": "无 LLM 的智能体微调",
    "Breast Cancer Mammogram Classification": "乳腺癌钼靶影像分类",
    "HTML NER Tagging": "HTML 命名实体标注",
    "NER Tagging for Invoices (BIO Format)": "发票 NER 标注 (BIO 格式)",
    "OCR Invoices Pre-NER BIO Format": "发票 OCR 预标注 (BIO 格式)",
    "Two-Level Sentiment Analysis of X / Twitter posts": "X/Twitter 帖子二级情感分析",
    "Taxonomy": "分类体系",
    "Visual Question Answering": "视觉问答",
}


def translate_template_yaml(
    filepath: Path,
    dry_run: bool = False,
) -> bool:
    """翻译单个模板的 config.yml"""
    content = filepath.read_text(encoding="utf-8")
    original = content

    # 替换 group（支持带双引号、单引号和不带引号）
    for en, zh in GROUP_TRANSLATIONS.items():
        # 双引号
        content = re.sub(
            r'^group:\s*"' + re.escape(en) + r'"',
            f'group: "{zh}"',
            content,
            flags=re.MULTILINE,
        )
        # 单引号
        content = re.sub(
            r"^group:\s*'" + re.escape(en) + r"'",
            f"group: '{zh}'",
            content,
            flags=re.MULTILINE,
        )
        # 无引号
        content = re.sub(
            r'^group:\s*' + re.escape(en) + r'\s*$',
            f'group: {zh}',
            content,
            flags=re.MULTILINE,
        )

    # 替换 title（支持带双引号、单引号和不带引号）
    for en, zh in TITLE_TRANSLATIONS.items():
        # 双引号
        content = re.sub(
            r'^title:\s*"' + re.escape(en) + r'"',
            f'title: "{zh}"',
            content,
            flags=re.MULTILINE,
        )
        # 单引号
        content = re.sub(
            r"^title:\s*'" + re.escape(en) + r"'",
            f"title: '{zh}'",
            content,
            flags=re.MULTILINE,
        )
        # 无引号
        content = re.sub(
            r'^title:\s*' + re.escape(en) + r'\s*$',
            f'title: {zh}',
            content,
            flags=re.MULTILINE,
        )

    if content != original and not dry_run:
        filepath.write_text(content, encoding="utf-8")
        return True
    return content != original


def _translate_groups_file(
    groups_file: Path,
    dry_run: bool = False,
) -> bool:
    """翻译 groups.txt 分类列表文件。"""
    lines = groups_file.read_text(encoding="utf-8").splitlines()
    original = lines.copy()
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        translated = GROUP_TRANSLATIONS.get(stripped)
        if translated:
            # 保持原有的前后空白
            leading = line[:len(line) - len(line.lstrip())]
            trailing = line[len(line.rstrip()):]
            lines[i] = leading + translated + trailing
    
    if lines != original and not dry_run:
        groups_file.write_text('\n'.join(lines) + '\n', encoding="utf-8")
        return True
    return lines != original


def apply_template_localization(
    ls_root: Path,
    config: BrandConfig,
    dry_run: bool = False,
) -> list[str]:
    """翻译所有标注模板的分类名和标题。"""
    modified: list[str] = []
    ls_root = Path(ls_root)

    if not config.translations_file or not config.source_i18n:
        return modified

    templates_dir = ls_root / "label_studio" / "annotation_templates"
    if not templates_dir.exists():
        return modified

    # 1. 翻译 groups.txt（分类列表，前端直接显示）
    groups_file = templates_dir / "groups.txt"
    if groups_file.exists():
        changed = _translate_groups_file(groups_file, dry_run)
        if changed:
            modified.append(str(groups_file.relative_to(ls_root)))

    # 2. 遍历所有模板的 config.yml
    for category_dir in templates_dir.iterdir():
        if not category_dir.is_dir():
            continue
        for template_dir in category_dir.iterdir():
            if not template_dir.is_dir():
                continue
            config_file = template_dir / "config.yml"
            if config_file.exists():
                changed = translate_template_yaml(config_file, dry_run)
                if changed:
                    modified.append(str(config_file.relative_to(ls_root)))

    return modified


__all__ = ["apply_template_localization"]
