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

    ("encourage", "The mentoring programme encourages students to ask questions when they feel unsure.", "encourage 在这里表示鼓励学生提问，不表示强迫。",
     "学校应鼓励更多学生参加志愿活动。Schools should ___ more students to take part in volunteer work.", "encourage",
     "Schools should encourage more students to take part in volunteer work.", "encourage somebody to do something；它表达鼓励或支持，不表示强迫。"),
    ("improve", "Access to quiet study spaces can improve students' concentration.", "improve 表示使学习专注程度变好；句中直接接名词作宾语。",
     "规律运动能改善睡眠质量。Regular exercise can ___ sleep quality.", "improve",
     "Regular exercise can improve sleep quality.", "improve + 名词；表示使某方面变好，不需要再加 more better 一类比较结构。"),
    ("require", "Some degree courses require students to complete a placement.", "require students to do 表示课程要求学生完成某项实践。",
     "这项任务需要仔细规划。This task ___ careful planning.", "requires",
     "This task requires careful planning.", "require + 名词；require somebody to do something；单数主语 task 后用 requires。"),
    ("involve", "Organising the event involved working with several local groups.", "involve 在这里表示活动包括与多个当地团体合作。",
     "解决这个问题需要居民共同参与。Solving this problem will ___ residents working together.", "involve",
     "Solving this problem will involve residents working together.", "involve + 名词或动名词；描述活动内容时不接 to do。"),
    ("provide", "The website provides clear guidance on applying for the scholarship.", "provide guidance 表示提供指导；也可用 provide somebody with something。",
     "学校为新生提供实用建议。The school ___ new students with practical advice.", "provides",
     "The school provides new students with practical advice.", "provide somebody with something；单数主语 school 后用 provides。"),
    ("prevent", "A lack of sleep can prevent students from concentrating in class.", "prevent somebody from doing 表示阻止某人做某事。",
     "清晰的路标有助于防止游客迷路。Clear signs can help ___ visitors from getting lost.", "prevent",
     "Clear signs can help prevent visitors from getting lost.", "prevent somebody from doing something；prevent 后不接 to do。"),
    ("achieve", "Consistent practice can help students achieve better results.", "achieve 表示通过行动取得结果；句中搭配 better results。",
     "设定可行的目标能帮助小组达到目标。Setting realistic goals can help the group ___ its target.", "achieve",
     "Setting realistic goals can help the group achieve its target.", "achieve a goal / target / result；help 后可接动词原形或 to do。"),
    ("evidence", "There is no evidence that the measure has improved attendance.", "evidence that 表示支持某种判断的信息；这里没有声称措施必然有效。",
     "目前没有证据表明该措施有效。There is no ___ that the measure is effective.", "evidence",
     "There is no evidence that the measure is effective.", "evidence 通常作不可数名词；常见结构有 evidence that、evidence of，不说 an evidence。"),
    ("affect", "Rising transport costs can affect how often students visit campus.", "affect 在这里是动词，表示影响学生到校的频率。",
     "缺乏睡眠会影响注意力。A lack of sleep can ___ concentration.", "affect",
     "A lack of sleep can affect concentration.", "affect 通常作动词，后面直接接受影响的人或事；注意与名词 effect 区分。"),
    ("effect", "The new timetable had little effect on class attendance.", "effect 在这里是名词，表示新课表对出勤产生的影响。",
     "减少塑料使用可以对环境产生积极影响。Reducing plastic use can have a positive ___ on the environment.", "effect",
     "Reducing plastic use can have a positive effect on the environment.", "have an effect on 表示产生影响；effect 在此为名词，注意与动词 affect 区分。"),
    ("challenge", "The findings challenge the idea that longer study hours always produce better results.", "challenge 表示对‘学习时间越长结果越好’这一看法提出质疑。",
     "这些发现对一个常见假设提出了质疑。These findings ___ a common assumption.", "challenge",
     "These findings challenge a common assumption.", "challenge an idea / assumption 表示质疑并要求重新审视，不一定表示已经彻底推翻。"),
    ("consider", "Before choosing a course, students should consider the cost of commuting.", "consider 表示认真思考一个因素；后面直接接名词。",
     "我们应该考虑其他解决方案。We should ___ other solutions.", "consider",
     "We should consider other solutions.", "consider + 名词、动名词或从句；后面不加 about，也不说 consider to do。"),
    ("result", "The delay resulted from a shortage of staff.", "result from 表示‘由……造成’；原因是员工短缺。",
     "过度使用手机可能导致睡眠不足。Excessive phone use may ___ a lack of sleep.", "result in",
     "Excessive phone use may result in a lack of sleep.", "result in + 结果；result from + 原因。两种结构方向相反，需看句意。"),
    ("develop", "The course helps students develop practical communication skills.", "develop skills 表示逐步培养技能，不只是短时间变好。",
     "学校应帮助学生培养独立思考能力。Schools should help students ___ independent thinking skills.", "develop",
     "Schools should help students develop independent thinking skills.", "develop a skill / ability 表示培养；help 后接动词原形或 to do。"),
    ("available", "Study rooms are available to students after 5 p.m.", "available to students 表示学生在该时段可以使用自习室。",
     "在线咨询服务周一至周五均可使用。Online support is ___ from Monday to Friday.", "available",
     "Online support is available from Monday to Friday.", "be available to somebody / for something；表示可获得或可使用，不代表质量更好。"),
    ("opportunity", "The exchange programme gives students an opportunity to study abroad.", "opportunity to do 表示参加交流项目带来的学习机会。",
     "实习为学生提供了实践技能的机会。Internships give students an ___ to apply their skills.", "opportunity",
     "Internships give students an opportunity to apply their skills.", "an opportunity to do；也可用 opportunity for + 名词或动名词。"),
    ("reliable", "The analysis depends on reliable data from several sources.", "reliable 描述数据值得信赖，但不表示结论无需进一步核查。",
     "请在作决定前检查来源是否可靠。Please check that your source is ___ before making a decision.", "reliable",
     "Please check that your source is reliable before making a decision.", "reliable source / information；表示可信赖，不等于内容一定正确或完整。"),
    ("respond", "The council responded to residents' concerns by holding an open meeting.", "respond to 表示对居民的关切作出回应；后面需要介词 to。",
     "学校迅速回应了学生的反馈。The school ___ quickly to students' feedback.", "responded",
     "The school responded quickly to students' feedback.", "respond to somebody / something；不要把 respond 直接当作及物动词接对象。"),
    ("establish", "The research established a link between screen time and sleep quality.", "establish a link 表示研究建立了二者之间的联系；不自动说明因果关系。",
     "新项目旨在建立学校与社区之间的联系。The new project aims to ___ a link between the school and the community.", "establish",
     "The new project aims to establish a link between the school and the community.", "establish a link / relationship；研究发现关联不一定证明因果。"),
    ("support", "The survey results support the view that flexible hours help caregivers.", "support the view 表示调查结果为某个观点提供支持，不等于证明其绝对正确。",
     "数据支持了研究人员的结论。The survey results ___ the researchers' conclusion.", "support",
     "The survey results support the researchers' conclusion.", "support an argument / conclusion；表示提供依据或支持，不一定等同于 prove。"),
    ("increase", "The number of bicycle users increased after the new route opened.", "increase 表示数量上升；句中是不及物用法。",
     "学校应该增加为新生提供的信息量。Schools should ___ the amount of information available to new students.", "increase",
     "Schools should increase the amount of information available to new students.", "increase 可作及物或不及物动词；amount 常修饰不可数名词，number 常修饰可数名词。"),
    ("appropriate", "Protective clothing is appropriate for laboratory work.", "appropriate 表示在实验室工作这一情境下合适。",
     "请选择适合儿童的材料。Please choose materials that are ___ for children.", "appropriate",
     "Please choose materials that are appropriate for children.", "appropriate for + 人或用途；表达是否合适取决于具体场景。"),
    ("particular", "One particular detail caught the reviewers' attention.", "particular 在这里表示某一个具体细节，不直接等同于‘重要’。",
     "请特别注意截止日期。Please pay ___ attention to the deadline.", "particular",
     "Please pay particular attention to the deadline.", "pay particular attention to 是常见搭配；particular 表示特定或特别关注，不只是强调程度。"),
    ("effective", "The campaign was effective in reducing food waste.", "effective 表示措施达到了减少食物浪费的效果。",
     "清晰的反馈是一种有效的学习工具。Clear feedback is an ___ tool for learning.", "effective",
     "Clear feedback is an effective tool for learning.", "effective 表示能产生预期效果；efficient 更强调节省时间、资源或精力，两者不完全相同。"),
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
