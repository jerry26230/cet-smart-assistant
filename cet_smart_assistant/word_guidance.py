"""词汇学习用途；教学建议不等于考试词频或能力评分。"""

from dataclasses import asdict, dataclass
from html import escape
import json
from pathlib import Path

from .anki_service import normalize_word
from .data_service import save_document
from .training import EXAMPLES

LABELS = {"reading": "先练阅读识别", "writing": "值得练习写作表达", "both": "阅读与写作都可练"}
SOURCE = "项目原创教学示例（AI 辅助）；非真题，未作考试词频统计。"


@dataclass(frozen=True)
class WordGuide:
    focus: str
    reason: str
    reading_example: str
    reading_meaning: str
    writing_example: str
    writing_tip: str
    alternative: str
    caution: str

    def validate(self):
        if self.focus not in LABELS:
            raise ValueError("用法建议的训练方向无效。")
        for key, value in asdict(self).items():
            if not isinstance(value, str) or not value.strip() or len(value) > 700:
                raise ValueError("用法建议必须完整，每项不超过 700 字符。")
            if any(ord(c) < 32 and c not in "\n\t" for c in value):
                raise ValueError("用法建议包含无效控制字符。")


def builtin_guides():
    guides = {}
    alternatives = {
        "contribute": "Regular exercise helps improve health. → Regular exercise contributes to better health.（表示促成因素，不保证单独导致结果）",
        "address": "Schools should deal with this problem. → Schools should address this problem.（表示着手处理，不等于已经解决）",
        "account": "Transport costs make up a quarter of the budget. → Transport costs account for a quarter of the budget.（仅在占比语境）",
        "access": "Students should be able to use the library. → Students should have access to the library.（强调可使用的机会）",
        "benefit": "Regular feedback is helpful to students. → Students can benefit from regular feedback.（改换主语和介词结构）",
        "adapt": "We need to adjust to change. → We need to adapt to change.（适应变化，不是采用某个办法）",
        "maintain": "We should keep a balance between study and rest. → We should maintain a balance between study and rest.（强调持续保持）",
        "significant": "Education plays an important role in development. → Education plays a significant role in development.（强调重要影响，不声称统计显著）",
        "promote": "Group activities can encourage cooperation. → Group activities can promote cooperation.（强调促进，不表示强迫或保证）",
        "reduce": "We should use less energy. → We should reduce energy consumption.（改为动词加名词结构，含义相近）",
        "approach": "We need a new way to solve the problem. → We need a new approach to solving the problem.（to 后接动名词）",
        "essential": "Regular practice is very important for progress. → Regular practice is essential for progress.（语气变强，仅确实必不可少时用）",
    }
    for word, sentence, meaning, prompt, answer, completed, usage in EXAMPLES:
        guides[word] = WordGuide("both", "先识别句中含义，再主动练习这个搭配；是否用于作文取决于题意。",
                                sentence, meaning, completed, usage,
                                alternatives[word],
                                "用词准确、自然比词汇难度更重要。")
    guides.update({
        "abandon": WordGuide("reading", "可先掌握阅读中的‘放弃、遗弃’义；作文谈放弃计划或做法时也可使用，并非不能写。",
            "The team abandoned the plan after reviewing its costs.", "团队评估成本后放弃了计划；不是忘记了计划。",
            "We should abandon wasteful habits.", "abandon + 计划、尝试或习惯，通常表示不再继续；不能用来表达忘记做某事。",
            "在‘放弃某计划’语境，give up the plan 可改写为 abandon the plan。",
            "forget 侧重忘记，abandon 侧重放弃或离弃，两者不能机械互换。"),
        "forget": WordGuide("both", "基础词同样有用，叙事或提醒时可准确表达忘记，不需要刻意换难词。",
            "She forgot to submit the form before the deadline.", "她忘记在截止前交表格，forget to do 指忘记去做。",
            "We should not forget the needs of older people.", "forget to do 与 forget doing 含义不同：前者忘记去做，后者不记得做过。",
            "正式讨论忽视需求时可考虑 overlook people's needs，但它强调忽视，不等于所有 forget。",
            "不要把 forget 自动换成 abandon；先判断是忘记、忽视还是主动放弃。"),
        "good": WordGuide("writing", "作文中可先说清楚好在哪里，再选更精确的形容词；good 本身没有错。",
            "The programme produced good results for local schools.", "good results 表示效果好，具体含义需看上下文。",
            "Regular feedback is beneficial to students.", "表达‘有益’可用 beneficial to；表达‘有效的方法’可用 an effective method。",
            "Exercise is good for our health. → Exercise is beneficial to our health.（强调益处）",
            "不是所有 good 都能替换为 beneficial 或 fantastic；fantastic 常带强烈赞赏色彩。"),
        "fantastic": WordGuide("reading", "先理解强烈赞赏语气；写作中适合热情评价，不是正式议论文的通用升级词。",
            "The volunteers did a fantastic job at the event.", "这里是强烈赞扬志愿者表现非常好。",
            "We had a fantastic time at the festival.", "个人体验或热情评价中较自然；论证措施效果时应具体说明 effective、beneficial 等含义。",
            "a good time → a fantastic time 可加强赞赏，但改变了语气与程度。",
            "不将 good method 一律改成 fantastic method；精确表达效果比夸赞更适合论证。"),
    })
    return guides


BUILTIN_GUIDES = builtin_guides()


def guide_text(guide, source=SOURCE):
    guide.validate()
    return "\n\n".join((f"学习建议：{LABELS[guide.focus]}\n{guide.reason}",
        f"阅读中这样理解\n{guide.reading_example}\n{guide.reading_meaning}",
        f"写作中这样使用\n{guide.writing_example}\n{guide.writing_tip}",
        f"有条件的表达替换\n{guide.alternative}", f"易错提醒\n{guide.caution}", f"来源：{source}"))


def load_guides(path: Path):
    if not path.exists():
        return {}
    if path.stat().st_size > 5_000_000:
        raise ValueError("本机用法文件过大，请先检查备份。")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["version"] != 1 or not isinstance(data["guides"], dict) or len(data["guides"]) > 500:
            raise ValueError()
        for word, fields in data["guides"].items():
            validate_word(word)
            WordGuide(**fields).validate()
        return data["guides"]
    except (ValueError, KeyError, TypeError):
        raise ValueError("本机用法文件格式无效，原文件不会被覆盖。") from None


def validate_word(word):
    import re
    word = normalize_word(word)
    if not re.fullmatch(r"[a-z]+(?:[ '\-][a-z]+)*", word) or len(word) > 80:
        raise ValueError("请输入英文词或短语（最多 80 字符）。")
    return word


def save_guide(path, word, guide):
    word = validate_word(word)
    guide.validate()
    guides = load_guides(path)
    if word not in guides and len(guides) >= 500:
        raise ValueError("已保存 500 个词的 AI 用法，请先备份整理。")
    guides[word] = asdict(guide)
    data = {"version": 1, "guides": guides}
    if len(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")) > 5_000_000:
        raise ValueError("本机用法文件达到大小上限，请先备份整理。")
    save_document(path, data)


def lookup_guide(word, path=None):
    key = normalize_word(word)
    if path is not None:
        stored = load_guides(path)
        if key in stored:
            return WordGuide(**stored[key]), "AI 生成，经用户保存；仍需核对，非真题或词频结论。"
    return BUILTIN_GUIDES.get(key), SOURCE


def render_guide(guide, source=SOURCE):
    return '<section class="cet-word-guide" style="text-align:left;border-top:1px solid #888;margin-top:20px;padding:14px;line-height:1.6"><b>这个词怎么学、怎么用</b><br>' + escape(guide_text(guide, source)).replace("\n", "<br>") + '</section>'
