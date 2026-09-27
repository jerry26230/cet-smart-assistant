"""原创示例训练包：由用户确认困难，不从分数推断原因。"""

from .anki_service import import_vocabulary, validate_card

# 例句与解释为本项目编写的教学示例（AI 辅助），不声称是真题或高频统计。
# 每项：词汇、阅读句、语境义、写作提示、填空答案、完整例句、用法解释。
EXAMPLES = [
    ("contribute", "Several factors contribute to this problem.", "contribute to 在这里表示‘促成、导致’，不是捐赠。",
     "规律运动有助于改善健康。填空：Regular exercise ___ better health.", "contributes to",
     "Regular exercise contributes to better health.", "contribute to + 名词 / 动名词；主语 exercise 为不可数名词，动词用第三人称单数。"),
    ("address", "The report addresses the shortage of affordable housing.", "address 在这里是动词‘处理、探讨’，不是名词‘地址’。",
     "学校应处理这一问题。填空：Schools should ___ this problem.", "address",
     "Schools should address this problem.", "address a problem / an issue；直接接宾语，不加 to。"),
    ("account", "Transport accounts for a large share of household spending.", "account for 在这里表示‘占……比例’。",
     "交通费用占预算的四分之一。填空：Transport costs ___ a quarter of the budget.", "account for",
     "Transport costs account for a quarter of the budget.", "account for 可表示‘占比’，也可表示‘解释原因’，需结合语境。"),
    ("access", "Students in remote areas may lack access to reliable internet services.", "access to 表示‘使用、获得……的机会或途径’。",
     "每位学生都应能使用图书馆。填空：Every student should have ___ the library.", "access to",
     "Every student should have access to the library.", "have access to + 名词；此处 access 为不可数名词。"),
    ("benefit", "Small businesses can benefit from better public transport.", "benefit from 表示‘从……中受益’。",
     "学生能从定期反馈中受益。填空：Students can ___ regular feedback.", "benefit from",
     "Students can benefit from regular feedback.", "benefit from + 名词；也可用及物动词结构：Regular feedback benefits students。"),
    ("adapt", "New employees need time to adapt to unfamiliar working practices.", "adapt to 表示‘适应’，不是 adopt（采用）。",
     "我们需要适应变化的环境。填空：We need to ___ a changing environment.", "adapt to",
     "We need to adapt to a changing environment.", "adapt to + 名词 / 动名词；adapt 与 adopt 的拼写和含义不同。"),
    ("maintain", "The study found that participants struggled to maintain a regular sleep schedule.", "maintain 表示‘保持’，宾语是作息规律。",
     "保持学习与休息的平衡很重要。填空：It is important to ___ a balance between study and rest.", "maintain",
     "It is important to maintain a balance between study and rest.", "maintain a balance between A and B；A 与 B 使用平行结构。"),
    ("significant", "The new policy led to a significant reduction in waste.", "significant 在这里表示‘明显的、重要的’，不一定表示统计学显著。",
     "教育对个人发展起重要作用。填空：Education plays a ___ role in personal development.", "significant",
     "Education plays a significant role in personal development.", "play a significant role in + 名词 / 动名词；important 也可表达相近含义。"),
    ("promote", "The campaign aims to promote healthier eating habits.", "promote 在这里表示‘促进、提倡’，不是给人升职。",
     "小组活动能促进合作。填空：Group activities can ___ cooperation.", "promote",
     "Group activities can promote cooperation.", "promote + 名词，直接接宾语，例如 promote cooperation / awareness。"),
    ("reduce", "Improved insulation can reduce the amount of energy a building uses.", "reduce 表示‘减少’；the amount of energy 是减少的对象。",
     "公共交通有助于减少空气污染。填空：Public transport can help ___ air pollution.", "reduce",
     "Public transport can help reduce air pollution.", "help (to) do；reduce pollution / costs / waste 都是动宾结构。"),
    ("approach", "The researchers tested a new approach to teaching vocabulary.", "approach 在这里是名词‘方法’，不是动词‘接近’。",
     "我们需要一种新的解决问题的方法。填空：We need a new ___ solving the problem.", "approach to",
     "We need a new approach to solving the problem.", "an approach to + 名词 / 动名词；这里 to 是介词，所以用 solving。"),
    ("essential", "Clean water is essential for public health.", "essential 表示‘必不可少的’，程度强于一般的 useful。",
     "定期练习对进步至关重要。填空：Regular practice is ___ progress.", "essential for",
     "Regular practice is essential for progress.", "be essential for + 名词；避免把 every useful thing 都夸大为 essential。"),
]

MODES = {"reading": "阅读语境", "writing": "写作表达"}
DIFFICULTIES = {
    "unknown": ("还不确定，先选择一种训练体验", None, "先判断困难来自理解还是表达。可自行选择训练方向；分数不会替你作出诊断。"),
    "reading_words": ("阅读：生词或熟词僻义", "reading", "推荐阅读语境：先在句中判断词义，再看释义和搭配。"),
    "reading_structure": ("阅读：长难句、定位或时间不足", None, "词汇卡只能辅助。建议另做句子结构拆解、证据定位或限时阅读，不以多背词替代这些练习。"),
    "writing_expression": ("写作：想不到表达或搭配不熟", "writing", "推荐写作表达：根据中文和句子提示主动补全搭配，再核对完整句。"),
    "writing_structure": ("写作：语法、篇章结构或切题", None, "建议另做语法订正、段落提纲或审题练习。以下词汇卡仅辅助表达，不能替代作文反馈。"),
}


def recommend(difficulty):
    if difficulty not in DIFFICULTIES:
        raise ValueError("请选择有效的困难类型。")
    return DIFFICULTIES[difficulty][1:]


def build_cards(mode):
    if mode not in MODES:
        raise ValueError("请选择阅读或写作训练。")
    cards = []
    for word, sentence, meaning, prompt, answer, completed, usage in EXAMPLES:
        if mode == "reading":
            front = f"阅读语境 | {sentence} 问：{word} 在句中是什么意思？"
            back = f"语境义：{meaning}\n搭配提示：{usage}"
        else:
            front = f"写作表达 | {prompt}"
            back = f"参考答案：{answer}\n完整例句：{completed}\n用法：{usage}\n这是参考表达，其他语法正确且符合语境的表达也可能成立。"
        back += "\n来源：项目原创教学示例（AI 辅助）；非真题，未作考试词频统计。"
        cards.append(validate_card(front, back))
    return cards


def import_training(col, mode):
    cards = build_cards(mode)
    return import_vocabulary(col, cards, deck_name=f"CET 备考::专项训练::{MODES[mode]}",
                             model_name=f"CET Smart Assistant Training {mode}",
                             tags=["cet_smart_assistant", f"cet_training_{mode}"])
