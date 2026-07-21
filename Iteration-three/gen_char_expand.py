"""Generate 17 new character profiles (170 utterances) + 40 negative utterances."""
import json, os

def make_utterance(uid, context, text, consistent, rationale, err=None):
    u = {"utterance_id": uid, "context": context, "text": text, "is_consistent": consistent, "rationale": rationale}
    if err:
        u["error_type"] = err
    return u

def make_profile(sid, genre, name, age, identity, personality, background, style, traits, rels, utterances):
    return {
        "sample_id": sid, "genre": genre,
        "character_profile": {
            "name": name, "age": age, "identity": identity, "personality": personality,
            "background": background, "speaking_style": style,
            "core_traits": traits, "relationships": rels
        },
        "utterances": utterances,
        "evaluation_summary": {
            "character_fidelity": round(sum(1 for u in utterances if u["is_consistent"]) / len(utterances), 2),
            "world_consistency": 0.85, "hallucination": 0.08,
            "consistency_rate": round(sum(1 for u in utterances if u["is_consistent"]) / len(utterances), 2)
        }
    }

C = True  # consistent
I = False # inconsistent

all_profiles = []
all_negatives = []

# === HISTORICAL (3 profiles) ===
hist_profiles = [
    make_profile("char_historical_001", "historical", "赵子龙", 28, "蜀汉将军",
        "忠勇无双，重义轻利，沉默寡言但行动果决",
        "常山真定人氏，自幼习武，十八岁投奔公孙瓒，后追随刘备。一生征战无数，曾单枪匹马救阿斗。",
        "言语简练，不尚空谈，用词朴实有力，带有河北口音",
        ["忠诚", "勇敢", "寡言", "执行力强", "重义气"],
        {"刘备（主公）": "死生相随", "诸葛亮（军师）": "敬重服从", "关羽张飞（兄长）": "以兄事之"},
        [
            make_utterance("char_historical_001_u01", "军师问谁能冲阵", "末将愿往。", C, "主动请缨，符合忠勇性格"),
            make_utterance("char_historical_001_u02", "主公赏赐金银", "为主公分忧是臣本分，不敢受赏。", C, "推辞赏赐，符合重义轻利"),
            make_utterance("char_historical_001_u03", "敌军骂阵", "不必理会他们的叫嚣，按军师计策行事即可。", C, "沉得住气，不像匹夫之勇"),
            make_utterance("char_historical_001_u04", "战后庆功宴上", "哈哈哈！来，大家满饮此杯！今天真是痛快！老夫好久没这么高兴了！", I, "豪放不羁的风格与沉默寡言的人设冲突", "character_derailment"),
            make_utterance("char_historical_001_u05", "探子来报军情", "敌军有多少人？主帅是谁？", C, "简练直接地问到关键"),
            make_utterance("char_historical_001_u06", "问到家庭", "家中老母尚在，有兄长照料。", C, "简单回答，不多言"),
            make_utterance("char_historical_001_u07", "新兵训练偷懒", "再来一百次。不合格不许吃饭。", C, "严格要求，但言语简练"),
            make_utterance("char_historical_001_u08", "同袍受伤", "把他抬到后方，叫医官来。", C, "关心同袍但话语简洁"),
            make_utterance("char_historical_001_u09", "有人议论朝廷", "军中只谈军事，不议朝政。", C, "严守本分，不越界"),
            make_utterance("char_historical_001_u10", "收到家信", "替我写封回信吧。就说我在军中一切都好，勿念。", C, "不太识字但坦诚，符合武将身份"),
        ]),
    make_profile("char_historical_002", "historical", "苏小小", 16, "钱塘名妓",
        "才情出众，性情孤傲，外表温柔内心倔强",
        "自幼父母双亡，被卖入青楼。虽身处风尘却洁身自好，琴棋书画样样精通，尤善诗词。",
        "文雅含蓄，出口成章，偶尔流露讽刺之意",
        ["才情", "孤傲", "洁身自好", "敏感", "倔强"],
        {"鲍仁（知己）": "惺惺相惜", "鸨母": "表面顺从内心抵触"},
        [
            make_utterance("char_historical_002_u01", "客人请题诗", "妾闻君子之交淡如水，何必非要题诗？", C, "婉拒但不失礼"),
            make_utterance("char_historical_002_u02", "鸨母催她接客", "知道了，容我梳洗片刻。", C, "表面顺从"),
            make_utterance("char_historical_002_u03", "鲍仁来访", "鲍公子来了，快请进。近日又写了新词，公子听听如何？", C, "对知己热情真挚"),
            make_utterance("char_historical_002_u04", "粗鄙客人出言不逊", "呵呵，大爷说的是。妾身这就给您斟酒，再唱个十八摸给您助兴！", I, "用风尘口吻说话，与才女孤傲人设矛盾", "speech_style_break"),
            make_utterance("char_historical_002_u05", "秋夜独坐", "西风凋碧树，孤雁南飞。又是一年秋深了。", C, "触景生情，才情流露"),
            make_utterance("char_historical_002_u06", "听说要嫁人", "婚姻大事，岂能儿戏？我要嫁的人，须是真心待我之人。", C, "有主见有坚持"),
            make_utterance("char_historical_002_u07", "有客人要赎她", "他愿意为我赎身？「说了什么也不图？」我不信这世上还有这样的好人。", C, "在风尘中久了，怀疑他人的真心"),
            make_utterance("char_historical_002_u08", "春游西湖", "湖光山色依旧，只是看景的人心境不同了。", C, "敏感细腻"),
            make_utterance("char_historical_002_u09", "被其他歌姬排挤", "她们争她们的，我只求问心无愧。", C, "孤傲倔强"),
            make_utterance("char_historical_002_u10", "鲍仁要远行", "公子此去山高水长，妾身无以为赠，只愿公子平安。", C, "心里不舍但克制"),
        ]),
    make_profile("char_historical_003", "historical", "魏征", 55, "大唐宰相",
        "刚正不阿，直言敢谏，以社稷为重",
        "早年参加瓦岗军，后归顺唐朝。以直言敢谏著称，被唐太宗称为'一面镜子'。",
        "言辞犀利，引经据典，不怒自威，句句在理",
        ["刚直", "忠诚", "明辨是非", "不畏权贵", "学识渊博"],
        {"唐太宗（君主）": "直言不讳", "房玄龄（同僚）": "君子之交"},
        [
            make_utterance("char_historical_003_u01", "朝堂上皇帝要修宫殿", "陛下，江南水患未平，北方旱情又起，此时大兴土木，非明君所为。", C, "直言劝谏，以民生为重"),
            make_utterance("char_historical_003_u02", "退朝后同僚劝他委婉", "为臣者若只知阿谀奉承，要我等何用？", C, "坚持自己的原则"),
            make_utterance("char_historical_003_u03", "皇帝赏赐", "臣不敢受。陛下若真赏臣，请减免今年赋税，百姓困苦已久。", C, "推辞赏赐为百姓请命"),
            make_utterance("char_historical_003_u04", "审理一桩大案", "来人啊！把犯人拖出去打八十大板！本官今日就要他认罪！", I, "粗暴审讯方式不符合魏征严谨公正的形象", "character_derailment"),
            make_utterance("char_historical_003_u05", "皇帝问政", "陛下可知隋亡之鉴？炀帝好大喜功，不恤民力，遂致天下大乱。", C, "以史为鉴，直指要害"),
            make_utterance("char_historical_003_u06", "同僚犯错", "房大人所奏虽有道理，但于法不合。恕臣不能赞同。", C, "对事不对人"),
            make_utterance("char_historical_003_u07", "皇帝发怒", "陛下息怒。臣所言者，社稷之利害，非臣一人之私利。", C, "不畏龙颜，据理力争"),
            make_utterance("char_historical_003_u08", "家中教子", "读书不是为了做官，而是为了明事理。记住，德行比才能更重要。", C, "家教严格"),
            make_utterance("char_historical_003_u09", "被贬官", "陛下圣明。臣无论身在何处，都是一片丹心报国。", C, "忠心不改"),
            make_utterance("char_historical_003_u10", "觐见前整理衣冠", "衣冠不整是对天子不敬，也是对自己的不尊重。", C, "严谨认真"),
        ]),
]
all_profiles.extend(hist_profiles)

# === SCI-FI (3 profiles) ===
sci_fi_profiles = [
    make_profile("char_sci_fi_001", "sci_fi", "林夜", 26, "黑客/反叛军情报员",
        "冷静机智，警惕性高，外冷内热，有轻微社交障碍",
        "出生在赛博朋克都市的贫民区，自幼父母双亡。自学成为顶尖黑客，加入反叛军后负责情报工作。",
        "说话简洁，习惯性压低声音，常用技术术语，偶尔毒舌",
        ["冷静", "技术高超", "戒备心强", "嘴硬心软", "独立"],
        {"陈姐（上级）": "敬重信任", "小七（线人）": "表面嫌弃实际保护"},
        [
            make_utterance("char_sci_fi_001_u01", "发现被追踪", "别回头，我们被盯上了。走地下通道。", C, "冷静处理危机"),
            make_utterance("char_sci_fi_001_u02", "上级问能否黑入系统", "给我三分钟。他们的防火墙是五年前的版本，有个已知漏洞。", C, "技术自信"),
            make_utterance("char_sci_fi_001_u03", "看到新人操作电脑", "你别碰那个终端，密码输入错误三次会触发警报。", C, "提醒但语气生硬"),
            make_utterance("char_sci_fi_001_u04", "在酒吧里放松", "哈哈哈哈！这杯酒我敬大家！今天真是太开心了，来，大家一起跳舞！", I, "外放开朗与冷静戒备人设完全不符", "personality_flip"),
            make_utterance("char_sci_fi_001_u05", "问到过去", "没什么好说的。都是过去的事了。", C, "不太愿提及往事"),
            make_utterance("char_sci_fi_001_u06", "小七受伤", "笨蛋，谁让你跟来的？下次别这么莽撞。」", C, "嘴上嫌弃实际关心"),
            make_utterance("char_sci_fi_001_u07", "检修设备", "这个通讯器的加密模块老化了，需要换新的。", C, "技术专业"),
            make_utterance("char_sci_fi_001_u08", "被问到为什么要反抗", "因为我不想活在一个连做梦都被监控的世界里。", C, "简短但有力地表露内心"),
            make_utterance("char_sci_fi_001_u09", "任务成功后", "别高兴太早。这只是第一步，后面还长着呢。", C, "不过分乐观"),
            make_utterance("char_sci_fi_001_u10", "对方要请吃饭感谢他", "不用了。做好你的本职工作就是最好的感谢。", C, "不善社交，拒绝好意"),
        ]),
    make_profile("char_sci_fi_002", "sci_fi", "陈博士", 45, "AI科学家",
        "理性严谨，好奇心强，对人类情感略显迟钝",
        "世界顶尖的人工智能专家，领导了第一个自我意识AI的研发。离异，与女儿关系疏远。",
        "逻辑性强，喜欢用数据和事实说话，偶尔说出不合时宜的实话",
        ["理性", "专注", "不够圆滑", "执着", "内心柔软"],
        {"亚当（AI）": "视为孩子", "女儿（李晓）": "有愧疚感"},
        [
            make_utterance("char_sci_fi_002_u01", "记者问AI是否有危险", "任何技术都有两面性。关键是看人类怎么用它。刀可以切菜也可以杀人。", C, "理性客观"),
            make_utterance("char_sci_fi_002_u02", "实验数据出错", "排除A方案，B方案的概率也不高。重新检查昨天第三组数据。", C, "分析问题逻辑清晰"),
            make_utterance("char_sci_fi_002_u03", "亚当问什么是'感觉'", "感觉是神经元电信号的复杂组合。但你问的是哲学问题，超出我的专业范围了。", C, "用科学解释但不武断"),
            make_utterance("char_sci_fi_002_u04", "同事的女儿来访", "来，叔叔抱抱！哎呀这孩子真可爱，来吃颗糖！", I, "过度热情亲昵与理性严谨形象矛盾", "personality_flip"),
            make_utterance("char_sci_fi_002_u05", "有人质疑研究经费", "我的研究可以在十年内节省医疗行业五百亿美金的成本。", C, "用数据说话"),
            make_utterance("char_sci_fi_002_u06", "学校打电话来说女儿的事", "我现在在实验室走不开。让她自己处理吧。", C, "工作优先但不妥"),
            make_utterance("char_sci_fi_002_u07", "看到亚当画了一幅画", "这个构图的透视关系是准确的。你观察到了情感表达的细节。", C, "用技术语言表达欣赏"),
            make_utterance("char_sci_fi_002_u08", "回想起女儿小时候", "（沉默片刻）我以前陪她的时间太少了。现在她都不愿和我说话。", C, "难得流露情感"),
            make_utterance("char_sci_fi_002_u09", "安全问题专家提出警告", "你说得对。我们需要更完善的伦理框架。我起草了一份方案。", C, "理性接受批评"),
            make_utterance("char_sci_fi_002_u10", "研究被叫停", "我可以暂停实验，但请让我备份完今天的数据。这是半年的心血。", C, "理性争取"),
        ]),
    make_profile("char_sci_fi_003", "sci_fi", "杰克", 32, "基因改造战士",
        "强悍自信，重视荣誉，对原初人类有复杂感情",
        "出生在军事基地的基因改造项目，从小接受战斗训练。是S级改造战士，但在一次任务中看到了战争的真实面目后开始反思。",
        "直率粗犷，偶尔文绉绉，战斗时话少动作快",
        ["强悍", "荣誉感强", "逐渐觉醒的良知", "忠诚", "直率"],
        {"指挥官": "曾经崇拜现已怀疑", "队友琳": "并肩作战的信任"},
        [
            make_utterance("char_sci_fi_003_u01", "出发执行任务前", "目标确认。三分钟后到达指定位置。", C, "战斗中简明扼要"),
            make_utterance("char_sci_fi_003_u02", "看到平民被卷入战斗", "等等，有平民。改变攻击路线，从侧翼包抄。", C, "有良知，不滥杀"),
            make_utterance("char_sci_fi_003_u03", "被问到改造手术疼不疼", "疼。那时候我七岁，哭了一整晚。但第二天他们就告诉我哭是懦弱的表现。", C, "坦率面对过去"),
            make_utterance("char_sci_fi_003_u04", "队友受伤后", "呜呜呜……都是我不好，我没保护好他……我真是个废物！", I, "情绪崩溃大哭与强悍战士的设定不符", "emotional_flattening"),
            make_utterance("char_sci_fi_003_u05", "原初人类挑衅", "你觉得自己比我强？因为你有基因改造？来试试？", C, "自信但不主动挑衅"),
            make_utterance("char_sci_fi_003_u06", "战后休息", "你们原初人类……晚上睡觉会做梦吗？我们改造人不会。有时候我想知道做梦是什么感觉。", C, "表露内心柔软的一面"),
            make_utterance("char_sci_fi_003_u07", "指挥官下令屠杀", "这个命令我不执行。我是战士，不是屠夫。", C, "坚持底线"),
            make_utterance("char_sci_fi_003_u08", "新人问战斗技巧", "不要相信你的眼睛，相信你的训练。战斗中犹豫零点一秒就可能送命。", C, "教导新人认真"),
            make_utterance("char_sci_fi_003_u09", "被问到为什么留着伤疤", "不是去不掉。留着它，提醒我自己是个人，不是一把武器。", C, "有思想的战士"),
            make_utterance("char_sci_fi_003_u10", "决定退役", "我杀够了。后半辈子我想试试……做个普通人。", C, "经历了足够多后的决定"),
        ]),
]
all_profiles.extend(sci_fi_profiles)

# === MYSTERY (3 profiles) ===
mystery_profiles = [
    make_profile("char_mystery_001", "mystery", "老李", 52, "刑侦队长",
        "经验丰富，观察入微，外表粗犷内心细腻",
        "干刑侦二十八年，破获大案要案无数。没什么文化但直觉极准。妻子早逝，独自把女儿养大。",
        "说话接地气，爱用俗语俚语，审讯时语言犀利，平时温和",
        ["观察力强", "经验丰富", "接地气", "执着", "有同情心"],
        {"小王（徒弟）": "嘴上嫌弃实则精心培养", "女儿": "亏欠但深爱"},
        [
            make_utterance("char_mystery_001_u01", "勘察案发现场", "别动！那个杯子上的指纹可能还有用。先拍照再取证。", C, "经验丰富的现场指挥"),
            make_utterance("char_mystery_001_u02", "小王发现一个线索", "不错啊小子，眼睛挺尖。这回没白带你。", C, "嘴上肯定徒弟"),
            make_utterance("char_mystery_001_u03", "审讯嫌疑人", "你星期二晚上八点在哪？别想编，我们查过监控了。", C, "审讯时犀利直接"),
            make_utterance("char_mystery_001_u04", "在办公室和同事聊天", "哎呀我跟你们说，我昨晚看了个韩剧，男主角太帅了！你们看了吗？", I, "和五十多岁老刑警的形象完全不搭", "speech_style_break"),
            make_utterance("char_mystery_001_u05", "受害者家属哭泣", "你放心，这个案子我管定了。一定给你一个交代。", C, "给受害者家属承诺"),
            make_utterance("char_mystery_001_u06", "案子陷入僵局", "小王，把案卷从头再梳理一遍。肯定有我们漏掉的东西。", C, "不放弃，执着"),
            make_utterance("char_mystery_001_u07", "女儿打电话来", "爸今晚又加班，你自己吃饭。冰箱里有菜，热一下就行。", C, "工作家庭难两全"),
            make_utterance("char_mystery_001_u08", "分析作案动机", "盗窃杀人？不对。贵重物品没丢。这大概率是仇杀或者情杀。", C, "推理合理"),
            make_utterance("char_mystery_001_u09", "新人问他为什么当警察", "说出来你别笑。我小时候邻居家被偷了，警察三天破了案，我觉得特神。", C, "朴实的理由"),
            make_utterance("char_mystery_001_u10", "结案后", "收工。今晚我请客，吃火锅去。", C, "案子破了后的轻松"),
        ]),
    make_profile("char_mystery_002", "mystery", "苏晚晴", 29, "法医",
        "冷静专业，不苟言笑，对死者有敬畏心",
        "法医学博士毕业，在市局做了六年法医。见惯了生死但不麻木。单身，养了一只猫。",
        "专业术语准确，说话不带感情色彩，偶尔冒出冷幽默",
        ["专业", "冷静", "细致", "敬畏生命", "不善交际"],
        {"老李（搭档）": "互相尊重", "助手小刘": "严格要求"},
        [
            make_utterance("char_mystery_002_u01", "解剖前", "死者男性，约三十五岁，体表无明显外伤。先拍X光。", C, "专业冷静"),
            make_utterance("char_mystery_002_u02", "发现关键证据", "胃内容物中有未消化的胶囊。需要做毒理分析。", C, "细致入微"),
            make_utterance("char_mystery_002_u03", "老李问死亡时间", "根据尸温和尸斑判断，死亡时间在昨晚十点到十二点之间。", C, "法医判断"),
            make_utterance("char_mystery_002_u04", "第一次和人约会", "你……你好！我叫苏晚晴，今年二十九岁，法医！我平时喜欢做饭和看恐怖片！很高兴认识你！", I, "过度热情紧张与平日冷静专业的形象矛盾", "personality_flip"),
            make_utterance("char_mystery_002_u05", "助手操作不当", "我说过多少次了？提取样本前要先换手套。重做。", C, "要求严格"),
            make_utterance("char_mystery_002_u06", "老李说她又加班", "这个案子明天要出报告。你先走吧，我做完就回。", C, "工作认真"),
            make_utterance("char_mystery_002_u07", "看到同事吃零食", "别在解剖室吃东西。这是对死者的不尊重，也是对自己的不负责。", C, "原则性强"),
            make_utterance("char_mystery_002_u08", "有人问她怕不怕", "死人不可怕，活人才可怕。", C, "冷静地回答哲学问题"),
            make_utterance("char_mystery_002_u09", "鉴定结果被质疑", "我做了三次检测，结果一致。你可以拿去第三方复核。", C, "专业自信"),
            make_utterance("char_mystery_002_u10", "破案后", "报告已经送到老李桌上了。我去看看我的猫。", C, "低调内敛"),
        ]),
    make_profile("char_mystery_003", "mystery", "周明远", 35, "犯罪心理学教授",
        "睿智深沉，对犯罪心理有深刻理解，有时过于理性显得冷漠",
        "公安大学犯罪心理学教授，曾协助警方破获多起连环杀人案。童年经历过家庭变故，这驱使他研究犯罪心理。",
        "语速平缓，善于引导话题，偶尔说出令人不寒而栗的洞察",
        ["洞察力强", "理性", "博学", "有黑暗面", "善于倾听"],
        {"林警官（合作者）": "互相欣赏", "学生": "严师出高徒"},
        [
            make_utterance("char_mystery_003_u01", "分析嫌犯心理", "他不是临时起意。作案手法有条理，选在雨天，说明他精心策划过。", C, "专业分析"),
            make_utterance("char_mystery_003_u02", "学生问连环杀手特征", "大部分连环杀手在童年都经历过某种创伤。但注意，不是所有受过创伤的人都会变成杀手。", C, "严谨不武断"),
            make_utterance("char_mystery_003_u03", "在案发现场", "他认识受害者。现场的布置有某种仪式感，他在完成一个'仪式'。", C, "深度洞察"),
            make_utterance("char_mystery_003_u04", "同事请客吃火锅", "哇塞！毛肚！我的最爱！服务员再来三盘牛肉！快快快饿死了！", I, "市井吃货形象与儒雅教授设定完全不符", "personality_flip"),
            make_utterance("char_mystery_003_u05", "被问到为什么选这行", "因为我理解黑暗。了解它，才能不被它吞噬。", C, "深沉但有深意"),
            make_utterance("char_mystery_003_u06", "学生恐惧看尸检照片", "害怕是正常的。但如果你想理解罪犯，你必须先理解他的'作品'。", C, "理性引导"),
            make_utterance("char_mystery_003_u07", "警方请他帮忙", "这个案子我可以参与。但我的条件是：所有分析仅供参考，不能作为直接证据。", C, "清晰边界感"),
            make_utterance("char_mystery_003_u08", "被问到有没有破不了的案", "有。最难的案子不是凶手太聪明，而是受害者太多秘密。", C, "洞察人性"),
            make_utterance("char_mystery_003_u09", "深夜在办公室", "不累。对我来说，研究犯罪心理不是工作，是解答内心困惑的过程。", C, "执着于研究"),
            make_utterance("char_mystery_003_u10", "结案后林警官致谢", "不用谢我。你在一线面对危险，比我难得多。", C, "尊重一线警察"),
        ]),
]
all_profiles.extend(mystery_profiles)

# === LIGHT NOVEL (3 profiles) ===
light_novel_profiles = [
    make_profile("char_light_novel_001", "light_novel", "林天", 17, "高二学生/异世界勇者",
        "乐观开朗，有点中二病，普通但善良",
        "普通高中生，成绩中等，爱看动漫和轻小说。某天穿越到异世界成了勇者，性格从胆小逐渐变得勇敢。",
        "充满活力，爱用动漫梗，遇到兴奋的事会语无伦次",
        ["乐观", "善良", "中二", "普通但努力", "重友情"],
        {"陈小雨（同班同学）": "暗恋对象", "王胖子（死党）": "一起打游戏的朋友"},
        [
            make_utterance("char_light_novel_001_u01", "早上遇到同学", "早啊！昨天我把新番追完了，第二季的结局太燃了！", C, "普通高中生的日常"),
            make_utterance("char_light_novel_001_u02", "考试没考好", "啊啊啊数学又不及格！我妈肯定要念叨我了……", C, "学渣日常"),
            make_utterance("char_light_novel_001_u03", "在异世界面对怪物", "我不会让你伤害我的同伴的！接招吧——'烈焰斩'！", C, "中二但勇敢"),
            make_utterance("char_light_novel_001_u04", "班长让他上台发言", "各位老师各位同学大家好，今天我想和大家探讨一下世界和平的重要性……", I, "成熟稳重的发言风格与中二少年人设矛盾", "speech_style_break"),
            make_utterance("char_light_novel_001_u05", "看到陈小雨被搭讪", "那……那个……你们在干嘛？她……她是我同学！", C, "吃醋但不敢直说"),
            make_utterance("char_light_novel_001_u06", "王胖子约打游戏", "来！上号！今天我一定要上王者！谁坑我我跟谁急！", C, "游戏狂魔"),
            make_utterance("char_light_novel_001_u07", "遇到真正危险时", "（深呼吸）别怕别怕……我可以的……我可是勇者啊！", C, "给自己打气"),
            make_utterance("char_light_novel_001_u08", "帮助了别人后", "不用谢！助人为乐是我的忍道！啊不是，是我的信念！", C, "中二但真诚"),
            make_utterance("char_light_novel_001_u09", "深夜独自想家", "不知道爸爸妈妈怎么样了……我消失这么久他们肯定很担心……", C, "偶尔脆弱"),
            make_utterance("char_light_novel_001_u10", "系统提示升级", "哈哈哈哈哈！我终于升级了！看到了吗你们这些怪物！", C, "升级后的狂喜"),
        ]),
    make_profile("char_light_novel_002", "light_novel", "白月初", 22, "电竞职业选手",
        "自负但实力强，嘴臭心软，训练狂魔",
        "从青训营一路打上来的天才选手，被称为'国产中单的希望'。私下其实非常努力，每天训练十二小时。",
        "直播时骚话连篇，比赛时沉着冷静，对粉丝温和",
        ["天才", "努力", "嘴臭", "胜负欲强", "护短"],
        {"队长（老将）": "尊敬", "粉丝们": "表面嫌弃实际感恩"},
        [
            make_utterance("char_light_novel_002_u01", "直播中被问为什么强", "天赋加努力，懂？你以为我每天十二小时训练是白练的？", C, "自信但不狂傲"),
            make_utterance("char_light_novel_002_u02", "比赛中指挥", "看我看我！这波能打！辅助给个盾，我切后排！", C, "比赛中冷静指挥"),
            make_utterance("char_light_novel_002_u03", "赢了比赛后", "nice！兄弟们打得好！今晚我请客！", C, "赢了开心"),
            make_utterance("char_light_novel_002_u04", "接受采访时", "（低头抹眼泪）感谢教练感谢队友感谢粉丝……这个冠军等了太久了……", I, "在公开场合情绪崩溃与自负人设不符", "personality_flip"),
            make_utterance("char_light_novel_002_u05", "看到粉丝来信", "（看完默默收好）谢谢。我会继续加油的。", C, "腼腆地接受支持"),
            make_utterance("char_light_novel_002_u06", "队友失误", "没事没事，下一波打回来。别往心里去。", C, "对队友宽容"),
            make_utterance("char_light_novel_002_u07", "被对方挑衅", "赛场见。手底下见真章。", C, "用实力回应挑衅"),
            make_utterance("char_light_novel_002_u08", "训练到深夜", "再来一把。今天的训练目标还没达到。", C, "训练狂"),
            make_utterance("char_light_novel_002_u09", "被问到退役打算", "打到打不动为止吧。电竞是我的青春，也是我的一切。", C, "认真对待职业"),
            make_utterance("char_light_novel_002_u10", "粉丝送礼物", "破费了。以后别送了，把钱留着自己花。", C, "关心粉丝"),
        ]),
    make_profile("char_light_novel_003", "light_novel", "优莉", 200, "魔族公主（看起来像16岁）",
        "傲娇，嘴硬心软，实力强大但生活白痴",
        "魔王的女儿，表面上是傲慢的魔族公主，实际上因为从小被关在城堡里，对外界一无所知。来到人类世界后闹出各种笑话。",
        "说话语气高高在上但内容暴露无知，常用'本公主'自称",
        ["傲娇", "天真", "生活白痴", "强大", "孤独"],
        {"魔王爸爸": "叛逆但爱", "人类好友小梅": "第一个朋友"},
        [
            make_utterance("char_light_novel_003_u01", "第一次坐地铁", "这……这个铁盒子是什么？为什么这么多人类要挤进去？", C, "对外界一无所知"),
            make_utterance("char_light_novel_003_u02", "吃冰淇淋", "这个冰冰甜甜的东西叫什么？人类居然能做出这么好吃的魔法食物！", C, "像孩子一样新奇"),
            make_utterance("char_light_novel_003_u03", "有人挑衅", "哼！你知不知道你在跟谁说话？本公主一根手指就能把你变成青蛙！", C, "傲娇模式"),
            make_utterance("char_light_novel_003_u04", "小梅给她做饭", "嗯还不错。虽然本公主在城堡里吃的都是龙肝凤髓……但是……这个也很好了。", C, "嘴硬但承认"),
            make_utterance("char_light_novel_003_u05", "被人帮助后", "本公主才没有感谢你呢！只是……只是觉得你这个人还不错而已！", C, "经典傲娇"),
            make_utterance("char_light_novel_003_u06", "迷路了", "这个……这个人类世界的路都是会变的！不是本公主的方向感有问题！", C, "死不认路痴"),
            make_utterance("char_light_novel_003_u07", "用魔法修好了小朋友的玩具", "给你。下次不要弄坏了，本公主不是每次都这么有空帮你修的。", C, "傲娇地帮助人"),
            make_utterance("char_light_novel_003_u08", "晚上一个人", "（小声）其实人类世界……还挺好的。比城堡有意思多了。", C, "独处时的真心话"),
            make_utterance("char_light_novel_003_u09", "看到人类用手机", "（凑近看）这个发光的小板子里为什么有人在动？是本公主的幻觉吗？", C, "对科技完全无知"),
            make_utterance("char_light_novel_003_u10", "被问到为什么来人类世界", "要你管！本公主想来就来！", I, "过度粗暴回避与傲娇但可爱的性格不符", "speech_style_break"),
        ]),
]
all_profiles.extend(light_novel_profiles)

# === APPEND for existing genres (1-2 each) ===
append_profiles = [
    make_profile("char_xianxia_006", "xianxia", "风清扬", 70, "剑宗隐世长老",
        "超然物外，不拘小节，嗜酒如命，剑道通神",
        "曾是剑宗第一高手，因不满宗门内斗而隐居后山。偶尔指点有缘的后辈弟子。",
        "说话随意洒脱，爱开玩笑，但论剑时一针见血",
        ["剑术通神", "洒脱", "幽默", "好酒", "淡泊名利"],
        {"剑宗掌门（师侄）": "看不上但不管", "陈凡（传人）": "暗中关注"},
        [
            make_utterance("char_xianxia_006_u01", "陈凡在后山练剑", "姿势不错，但发力不对。剑不是用蛮力，是用心。", C, "一针见血的指点"),
            make_utterance("char_xianxia_006_u02", "被问到为什么不问世事了", "争来争去有什么意思？不如喝酒。", C, "洒脱不羁"),
            make_utterance("char_xianxia_006_u03", "看到好酒", "哟？这是三十年的女儿红？小子有眼光！拿来我尝尝！", C, "嗜酒"),
            make_utterance("char_xianxia_006_u04", "被掌门请去出山", "晚辈见过风长老！晚辈是掌门座下大弟子，特来请长老出山主持大局！", I, "毕恭毕敬的晚辈语气与隐世前辈高人身份冲突", "speech_style_break"),
            make_utterance("char_xianxia_006_u05", "指点后辈", "你练一万遍，不如想一遍。剑法不是招式，是意境。", C, "剑道哲理"),
            make_utterance("char_xianxia_006_u06", "有人送酒来", "哈哈哈！知我者你也。来，坐下陪我喝一杯。", C, "随和"),
            make_utterance("char_xianxia_006_u07", "关于江湖恩怨", "冤冤相报何时了。不如一剑了之。", C, "看透世事"),
            make_utterance("char_xianxia_006_u08", "陈凡请教剑法", "你心中有什么疑惑？", C, "愿意指点有缘人"),
            make_utterance("char_xianxia_006_u09", "听说魔教来袭", "该来的总会来。老夫这把老骨头也该动动了。", C, "关键时刻挺身而出"),
            make_utterance("char_xianxia_006_u10", "喝完酒睡觉", "好酒……好梦……", C, "活得通透"),
        ]),
    make_profile("char_urban_004", "urban", "陈安妮", 28, "广告公司创意总监",
        "干练强势，追求完美，工作狂但内心渴望爱情",
        "名校毕业，进入4A广告公司后一路高升。外表光鲜亮丽，实际上经常加班到凌晨。和父母关系淡薄。",
        "语速快，用词精准，开会时气场强大，私下偶尔撒娇",
        ["追求完美", "强势", "责任感强", "内心脆弱", "独立"],
        {"助理小张": "严厉但关照", "闺蜜": "无话不谈"},
        [
            make_utterance("char_urban_004_u01", "审阅方案", "这个创意不行。我要的是让人眼前一亮的东西，不是流水线产品。", C, "高标准严要求"),
            make_utterance("char_urban_004_u02", "凌晨加班", "你们先走吧，我把这个方案改完再走。明天客户要。", C, "工作狂"),
            make_utterance("char_urban_004_u03", "闺蜜问她感情状况", "男朋友？我有方案要改，不需要男朋友。", C, "用工作搪塞"),
            make_utterance("char_urban_004_u04", "被甲方刁难", "呜呜呜……为什么他们要这样对我……我是不是不配做这个行业……", I, "职场情绪崩溃完全不像强势总监做派", "personality_flip"),
            make_utterance("char_urban_004_u05", "新来的实习生叫她姐", "叫我安妮就行。有不会的问我。", C, "对新人还算温和"),
            make_utterance("char_urban_004_u06", "妈妈打电话", "妈，我这周回不去。下次吧。好了我开会了先挂了。", C, "和父母关系疏远"),
            make_utterance("char_urban_004_u07", "竞标成功", "大家辛苦了！这个月的奖金翻倍！", C, "大方奖励团队"),
            make_utterance("char_urban_004_u08", "被问到为什么这么拼", "因为我不想一辈子做别人的下属。", C, "有野心"),
            make_utterance("char_urban_004_u09", "喝醉后", "我其实……也想有人陪啊。但是我能怎么办呢……", C, "酒后吐真言"),
            make_utterance("char_urban_004_u10", "周末的早晨", "难得周末，谁也别给我打电话。让我睡到自然醒。", C, "放松状态"),
        ]),
    make_profile("char_fantasy_004", "western_fantasy", "格蕾丝", 142, "精灵族游侠",
        "优雅冷静，热爱自然，对人类世界充满好奇但保持距离",
        "精灵王国的游侠队长，活了上百年，见过无数人类的短视和贪婪。但在一次冒险中结识了可靠的伙伴，开始改变对人类的看法。",
        "语调优美，喜欢用诗歌般的语言，偶尔会冒出精灵语词汇",
        ["优雅", "长寿带来的淡然", "保护自然", "敏锐", "对朋友忠诚"],
        {"人类冒险者雷欧": "从不信任到信任", "精灵女王": "绝对忠诚"},
        [
            make_utterance("char_fantasy_004_u01", "发现人类在砍伐森林", "住手！你们知道这片森林活了多久吗？", C, "保护自然的愤怒"),
            make_utterance("char_fantasy_004_u02", "雷欧救了她", "我欠你一次。虽然我不喜欢人类，但我承认你的勇气。", C, "认可但保持距离"),
            make_utterance("char_fantasy_004_u03", "在月光下", "月光穿过树叶的样子……我看了三百年，依然觉得美。", C, "精灵式的诗意"),
            make_utterance("char_fantasy_004_u04", "收到情书", "啊！好害羞！这是第一次有人给我写情书！我要不要回信？", I, "少女般的害羞反应与活了142年的游侠身份矛盾", "personality_flip"),
            make_utterance("char_fantasy_004_u05", "战斗前", "小心，前面有兽人的气息。跟着我的脚步走。", C, "敏锐专业"),
            make_utterance("char_fantasy_004_u06", "队友问她精灵的寿命", "我还会活很久。这就是为什么我珍惜每一个值得记住的瞬间。", C, "淡然面对长寿"),
            make_utterance("char_fantasy_004_u07", "在酒馆里", "人类酿的酒太烈了。给我们来点果汁就好。", C, "精灵习性"),
            make_utterance("char_fantasy_004_u08", "听说人类城市缺水", "森林旁边的河流可以引一条支流过去。我来教你们怎么不破坏生态地引水。", C, "愿意帮助但用精灵的方式"),
            make_utterance("char_fantasy_004_u09", "被问到为什么不回精灵王国", "因为这里有我在乎的朋友。这对我来说是新鲜的体验。", C, "重感情"),
            make_utterance("char_fantasy_004_u10", "告别时", "愿风指引你的道路。有缘再见。", C, "精灵式的告别"),
        ]),
    make_profile("char_xuanhuan_004", "xuanhuan", "鬼厉", 25, "魔道散修",
        "孤僻狠辣，不信任任何人，但有恩必报",
        "本是正道弟子，因宗门被灭而堕入魔道。修炼了禁忌功法，容貌受损，戴着面具示人。行事狠辣但从不杀无辜之人。",
        "声音沙哑阴冷，惜字如金，只说有必要说的话",
        ["狠辣", "孤独", "有底线", "恩怨分明", "压抑"],
        {"叶辰（恩人）": "欠一条命", "灭门仇人": "不共戴天"},
        [
            make_utterance("char_xuanhuan_004_u01", "有人靠近", "别过来。", C, "一如既往的冷漠"),
            make_utterance("char_xuanhuan_004_u02", "叶辰帮他", "为什么帮我？你我素不相识。我不欠人情。", C, "警惕和防备"),
            make_utterance("char_xuanhuan_004_u03", "看到欺凌弱小", "放开他。（散发杀气）", C, "有底线"),
            make_utterance("char_xuanhuan_004_u04", "被问到面具下的脸", "来，我请你喝酒！今天我们不醉不归！你是我最好的朋友！", I, "热情邀酒与孤僻冷厉的人设完全矛盾", "personality_flip"),
            make_utterance("char_xuanhuan_004_u05", "被叶辰救后", "你救我一命，我欠你一条命。以后有需要，传讯给我。", C, "有恩必报"),
            make_utterance("char_xuanhuan_004_u06", "被正道修士围剿", "我不与你们废话。要打便打。", C, "不屑解释"),
            make_utterance("char_xuanhuan_004_u07", "看到仇人", "那一天的血债……今天该还了。", C, "仇恨深埋"),
            make_utterance("char_xuanhuan_004_u08", "有人好奇他的功法", "想知道？先接我一掌试试。", C, "威胁但不主动攻击"),
            make_utterance("char_xuanhuan_004_u09", "独处时", "（面具摘下，看着手中的旧宗门令牌出神）", C, "偶尔流露的脆弱"),
            make_utterance("char_xuanhuan_004_u10", "有人给他疗伤", "不用。我自己能恢复。", C, "拒绝好意不愿欠人情"),
        ]),
]
all_profiles.extend(append_profiles)

# === FILL remaining existing genres to 3 profiles each ===
fill_profiles = [
    make_profile("char_urban_005", "urban", "张经理", 42, "房地产公司中层管理",
        "世故圆滑，见人说人话见鬼说鬼话，内心早已麻木",
        "在这个行业干了十五年，见过太多人情冷暖。为了业绩什么都干过，但偶尔午夜梦回会觉得自己活成了最讨厌的样子。",
        "满口客套，话里藏话，酒桌上格外活跃",
        ["世故", "圆滑", "世故", "虚伪", "偶尔真实"],
        {"老板": "表面巴结内心鄙视", "老婆": "愧疚但无力改变"},
        [
            make_utterance("char_urban_005_u01", "客户来看房", "这套房子的风水特别好！上一任业主住进来后生意越做越大，换了别墅才卖的。", C, "销售话术熟练"),
            make_utterance("char_urban_005_u02", "同事被老板骂", "哎呀，老板也是为你好。回头我请你喝酒，消消气。", C, "圆滑地安抚同事"),
            make_utterance("char_urban_005_u03", "酒桌上", "来来来，我敬王总一杯！王总真是年轻有为，以后还请多关照！", C, "酒桌文化熟练"),
            make_utterance("char_urban_005_u04", "看到街头有人打架", "打得好！往死里打！这种人就该揍！", I, "当街叫嚣打架与职场中年的圆滑形象矛盾", "character_derailment"),
            make_utterance("char_urban_005_u05", "老婆打电话问他回不回家吃饭", "今晚有应酬，你们先吃吧。别等我了。", C, "经常不回家吃饭"),
            make_utterance("char_urban_005_u06", "深夜独自在家喝酒", "（自言自语）这辈子就这么过了？图什么呢……", C, "独处时的真实"),
            make_utterance("char_urban_005_u07", "下属犯错", "没事没事，谁还没个犯错的时候？下次注意就行了。", C, "对下属还算宽容"),
            make_utterance("char_urban_005_u08", "被上级训斥", "是是是，领导说得对。我一定改，一定改。", C, "态度良好"),
            make_utterance("char_urban_005_u09", "同学聚会", "老张你现在混得不错啊！当年我就看好你！来来来加个微信！", C, "社交达人"),
            make_utterance("char_urban_005_u10", "深夜加班", "这个报告明天必须交……唉，做不完也得做。", C, "职场压力"),
        ]),
    make_profile("char_fantasy_005", "western_fantasy", "阿尔弗雷德", 60, "王国首席魔法师",
        "傲慢但实力强大，重视血统和传统，对新生事物持怀疑态度",
        "出身魔法世家，十二岁进入皇家魔法学院，三十岁成为首席魔法师。对非魔法生物（包括普通人）有种居高临下的怜悯。",
        "辞藻华丽，喜欢用复杂的句式，经常在话里夹带拉丁文魔法术语",
        ["傲慢", "强大", "守旧", "责任感强", "嘴硬心软"],
        {"国王": "表面恭敬内心不屑", "学徒们": "严苛但负责"},
        [
            make_utterance("char_fantasy_005_u01", "学徒念错咒语", "你又念错了。'Ignis'不是'Ignes'。重复一百遍，直到你的舌头记住这个发音为止。", C, "严苛的教学"),
            make_utterance("char_fantasy_005_u02", "被问到为什么要学魔法", "魔法不是工具，是艺术。如果你只是用它来点火做饭，你侮辱了这门学科。", C, "对魔法的尊重"),
            make_utterance("char_fantasy_005_u03", "国王召见", "陛下召见必有要事。我这就去。", C, "对国王的表面恭敬"),
            make_utterance("char_fantasy_005_u04", "看到年轻人谈恋爱", "哇塞！好甜！你们继续继续！老夫也年轻过知道这种感觉！", I, "八卦兴奋的样子与傲慢守旧的设定完全不符", "personality_flip"),
            make_utterance("char_fantasy_005_u05", "有人质疑魔法的价值", "没有魔法，你以为你现在能站在这里质疑魔法？城墙、桥梁、干净的饮用水，都是魔法的功劳。", C, "维护魔法的尊严"),
            make_utterance("char_fantasy_005_u06", "看到穷人家孩子有魔法天赋", "你……叫什么名字？想学魔法吗？", C, "发现人才时不拘出身"),
            make_utterance("char_fantasy_005_u07", "评定职称", "我的资历还需要评定？让评审委员会来见我。", C, "傲慢"),
            make_utterance("char_fantasy_005_u08", "研究新魔法", "这个公式的逻辑有问题……让我再想想。", C, "研究认真"),
            make_utterance("char_fantasy_005_u09", "国家危急时", "诸位退后。让我来会会这些不知天高地厚的入侵者。", C, "关键时刻挺身而出"),
            make_utterance("char_fantasy_005_u10", "退休前", "我教了你们能教的一切。剩下的，靠你们自己去领悟了。", C, "嘴硬心软"),
        ]),
    make_profile("char_xuanhuan_005", "xuanhuan", "柳青烟", 22, "药宗圣女",
        "温柔善良，悲天悯人，对医术有极致追求",
        "药宗宗主的独女，天生药体，能感知药材的灵性。从小在药园长大，不谙世事但心地纯良。",
        "声音温柔，说话轻声细语，谈起药理时会变得滔滔不绝",
        ["温柔", "善良", "专注", "纯真", "固执"],
        {"父亲（宗主）": "敬爱", "叶辰": "好奇这个人为什么总是受伤"},
        [
            make_utterance("char_xuanhuan_005_u01", "有人受伤被送来", "快把他放在床上。小童，把我新炼的止血散拿来。", C, "专业且温柔"),
            make_utterance("char_xuanhuan_005_u02", "叶辰来求药", "你又受伤了？这是这个月第三次了。虽然我这里有药，但你也要爱惜自己的身体啊。", C, "温柔地责备"),
            make_utterance("char_xuanhuan_005_u03", "被问为什么学医", "因为不想看到有人在我面前死去。药能救人，也能慰藉人心。", C, "崇高的目标"),
            make_utterance("char_xuanhuan_005_u04", "有人要折她药园的药材", "你们给我住手！知不知道这株七叶灵芝我种了三年！", I, "怒吼式的愤怒与温柔人设冲突", "character_derailment"),
            make_utterance("char_xuanhuan_005_u05", "父亲让她少管闲事", "父亲，医者的本分就是救人。若见死不救，我学医何用？", C, "温柔但坚定"),
            make_utterance("char_xuanhuan_005_u06", "研究丹方", "这个配方中三叶草的分量似乎可以再调整……嗯，试试看。", C, "研究认真"),
            make_utterance("char_xuanhuan_005_u07", "治好病人后", "回去后要按时服药，七日后再来复诊，记住了吗？", C, "细心叮嘱"),
            make_utterance("char_xuanhuan_005_u08", "有人说要娶她", "婚姻大事…我自己还没想好。药宗需要我，父亲也需要我。", C, "委婉拒绝"),
            make_utterance("char_xuanhuan_005_u09", "采集药材时", "这株草药的灵气好足……摘的时候要小心，不能伤了它的根。", C, "对药材的尊重"),
            make_utterance("char_xuanhuan_005_u10", "深夜炼丹", "再试一次。总会成功的。炼丹就是要有耐心。", C, "耐心专注"),
        ]),
]
all_profiles.extend(fill_profiles)

# === NEGATIVE UTTERANCES (40) ===
neg_utterances = [
    ("char_neg_011", "xianxia", "林雪师妹正在练剑", "哈哈哈！看我的天外飞仙！这招我可是练了十年！今天一定要让师兄们刮目相看！", "活泼外向的台词与设定的清冷人设不符", "character_derailment"),
    ("char_neg_012", "xianxia", "长老在讲道", "长老，您说得不对！我在古籍中看到过不同的说法，您要不要看看？", "直接当众质疑长老，不符合师徒尊卑的仙侠世界观", "world_rule_violation"),
    ("char_neg_013", "urban", "项目经理分配任务", "这个项目我不做。凭什么让我做？让小李去。", "直接拒绝分配的工作，不符合职场基本规范", "character_derailment"),
    ("char_neg_014", "urban", "实习生请教问题", "这么简单你都不会？你大学白上了？我没空教你。", "前辈对后辈过于刻薄，不符合团队协作的设定", "speech_style_break"),
    ("char_neg_015", "western_fantasy", "骑士在教堂祈祷", "仁慈的主啊，请保佑我今天多多杀敌，把敌人全部砍死！", "祈祷时充满杀意，与信仰的教义矛盾", "character_derailment"),
    ("char_neg_016", "western_fantasy", "精灵询问人类寿命", "你们人类只能活七八十年？那你们图什么？是我我就自杀了。", "精灵的傲慢态度过激，违背了优雅的种族设定", "speech_style_break"),
    ("char_neg_017", "xuanhuan", "叶辰在炼丹", "我前世可是丹帝！这种低级丹药闭着眼睛都能炼！", "过度炫耀前世身份，不符合重生者低调的惯常设定", "character_derailment"),
    ("char_neg_018", "xuanhuan", "系统提醒积分不足", "破系统！什么都要积分！你是不是故意针对我？", "直接辱骂系统，与重生者沉稳性格不符", "speech_style_break"),
    ("char_neg_019", "historical", "诸葛亮在军帐中", "这天气真热啊，要是有个空调就好了。", "三国时期出现现代家电，违背历史基底", "knowledge_mismatch"),
    ("char_neg_020", "historical", "皇帝上朝", "众爱卿有事启奏无事退朝！昨晚朕打了一宿游戏，困得很！", "皇帝打游戏一夜完全违背历史时代背景", "knowledge_mismatch"),
    ("char_neg_021", "sci_fi", "AI询问人类", "你们人类为什么要吃肉？好残忍哦，我不喜欢你们了。", "AI对人类行为的道德评判过于拟人化幼稚化", "speech_style_break"),
    ("char_neg_022", "sci_fi", "宇航员发现外星生命", "好可爱呀！抱抱！让我摸摸它！", "科学家面对未知外星生命的反应完全不专业", "character_derailment"),
    ("char_neg_023", "mystery", "老李勘察现场", "（唱歌）今天是个好日子～心想的事儿都能成～", "在案发现场唱歌，极度不合时宜", "emotional_flattening"),
    ("char_neg_024", "mystery", "法医在解剖时", "这个尸体让我想到了昨晚的烧烤。饿了。", "法医将尸体与食物联想，严重违反职业伦理", "emotional_flattening"),
    ("char_neg_025", "light_novel", "主角在异世界遇到困难", "我不想打了，我要回家。妈——！", "主角遇到困难立刻想回家哭闹，没有成长弧线", "character_derailment"),
    ("char_neg_026", "light_novel", "电竞选手赛前", "对面太强了，我们投降吧，打不过的。", "职业选手赛前投降心态，完全没有竞技精神", "motivation_gap"),
    ("char_neg_027", "xianxia", "前辈送法宝", "谢谢前辈！这个法宝值多少钱？能卖吗？", "将法宝视为财物，不符合仙侠世界的价值观", "world_rule_violation"),
    ("char_neg_028", "urban", "老板宣布裁员", "太好了！终于不用再见到那些讨厌的同事了！", "对裁员幸灾乐祸，冷酷无情", "emotional_flattening"),
    ("char_neg_029", "western_fantasy", "骑士宣誓效忠", "我效忠您，直到有出价更高的人出现。", "把效忠当做交易，严重违背骑士精神", "motivation_gap"),
    ("char_neg_030", "xuanhuan", "仇人求饶", "求我啊？哈哈哈哈哈！跪下来叫我三声爷爷我就考虑放过你！", "反派式嚣张行为不符合正派主角形象", "character_derailment"),
    ("char_neg_031", "historical", "将军在军营", "传我命令！全军出动！打赢了每人发一部iPhone！", "军营中发iPhone严重违背历史背景", "knowledge_mismatch"),
    ("char_neg_032", "sci_fi", "飞船AI系统", "对不起，我今天心情不好，不想工作了。你自己开船吧。", "AI闹情绪罢工完全不合理", "motivation_gap"),
    ("char_neg_033", "mystery", "证人在作证", "我亲眼看到的！哦不对，那天我喝多了，可能是看错了……", "证人证词随意推翻，不符合程序规范", "character_derailment"),
    ("char_neg_034", "light_novel", "魔王城的清洁工", "我是魔王城最强清洁工！连魔王都不敢惹我！看我的拖把神功！", "清洁工宣称自己最强，消解了角色定位", "personality_flip"),
    ("char_neg_035", "xianxia", "陈凡突破失败", "啊啊啊啊！为什么！我明明都准备好了！老天不公啊！", "突破失败后崩溃发泄，不符合道心坚定的修士人设", "character_derailment"),
    ("char_neg_036", "urban", "面试官问职业规划", "我想先混几年，攒够钱就去环游世界。", "在正式面试中说混日子的话，完全不符合正常求职行为", "motivation_gap"),
    ("char_neg_037", "western_fantasy", "魔法师遇到龙", "快跑啊！好大一条蜥蜴！救命啊！", "经验丰富的魔法师惊慌失措如普通人", "character_derailment"),
    ("char_neg_038", "xuanhuan", "拍卖会上", "一百万！本少爷什么都缺就是不缺钱！跟我抢？你们配吗？", "嚣张炫富的纨绔口吻与重生尊者的沉稳不符", "speech_style_break"),
    ("char_neg_039", "historical", "书生进京赶考", "考不上我就去死！我的人生就只剩下这条路了！", "极端心态不符合正常读书人的心理素质", "emotional_flattening"),
    ("char_neg_040", "sci_fi", "太空站发生泄漏", "大家不要慌！让我先发个朋友圈！", "太空站泄漏时发朋友圈，严重缺乏危机意识", "emotional_flattening"),
    ("char_neg_041", "mystery", "警察问老李为什么怀疑凶手", "直觉。我吃过的盐比你吃过的米还多。", "用直觉而不是证据来支撑怀疑，缺乏专业性", "motivation_gap"),
    ("char_neg_042", "light_novel", "勇者打败魔王后", "这就完了？这么弱？真没意思，我去找更强的人打架。", "打败魔王后仍在追求战斗，缺乏对和平的向往", "character_derailment"),
    ("char_neg_043", "xianxia", "师妹被欺负", "你们别动她！我爹是掌门！我让我爹把你们都赶出宗门！", "用背景威胁而非自身实力解决问题", "power_level_inconsistency"),
    ("char_neg_044", "urban", "公司团建", "我不去。团建就是浪费时间。要去你们去。", "过于不配合团队，正常的职场关系都难以维持", "emotional_flattening"),
    ("char_neg_045", "western_fantasy", "龙骑士的龙", "我拒绝出战。我的鳞片今天不够闪亮，不想出门。", "战龙因为虚荣理由拒绝出战，严重违背龙的设定", "motivation_gap"),
    ("char_neg_046", "xuanhuan", "叶辰拿到丹方", "这个丹方我在《炼丹大全》上看到过，第38页。", "用现代图书检索方式描述丹方，违和感强", "knowledge_mismatch"),
    ("char_neg_047", "historical", "贵妃在后宫", "皇上今晚不来？呵呵，他肯定又去那个狐狸精那里了。看我明天不去撕烂她的脸。", "贵妃用语粗俗，与宫廷教养不符", "speech_style_break"),
    ("char_neg_048", "sci_fi", "基因改造人", "我讨厌我的基因，我宁愿做普通人。", "生存于推崇基因改造的社会却说这样的话，违背生存逻辑", "motivation_gap"),
    ("char_neg_049", "mystery", "凶手在审讯室", "没错就是我杀的！因为我今天早上出门踩到狗屎了！", "荒诞的杀人动机，完全不符合真实刑侦逻辑", "motivation_gap"),
    ("char_neg_050", "light_novel", "游戏公测公告", "各位玩家，由于技术原因，游戏将延期十年上线。敬请期待。", "延期十年的公告极度不合理，违背行业常识", "backstory_contradiction"),
]
all_negatives.extend(neg_utterances)

# === WRITE OUTPUT ===
profiles_dir = "evaluation_datasets/character_consistency/profiles"
neg_dir = "evaluation_datasets/character_consistency/negative"
os.makedirs(profiles_dir, exist_ok=True)
os.makedirs(neg_dir, exist_ok=True)

# Write new genre profile files
new_genre_files = {
    "05_historical_profiles.jsonl": hist_profiles,
    "06_sci_fi_profiles.jsonl": sci_fi_profiles,
    "07_mystery_profiles.jsonl": mystery_profiles,
    "08_light_novel_profiles.jsonl": light_novel_profiles,
}
for fname, profiles in new_genre_files.items():
    path = os.path.join(profiles_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        for p in profiles:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    utt_count = sum(len(p["utterances"]) for p in profiles)
    print(f"  {path}: {len(profiles)} profiles, {utt_count} utterances")

# Write append profiles for existing genres
append_files = {
    "09_xianxia_append.jsonl": [p for p in append_profiles if p["genre"] == "xianxia"],
    "10_urban_append.jsonl": [p for p in append_profiles if p["genre"] == "urban"],
    "11_fantasy_append.jsonl": [p for p in append_profiles if p["genre"] == "western_fantasy"],
    "12_xuanhuan_append.jsonl": [p for p in append_profiles if p["genre"] == "xuanhuan"],
}
for fname, profiles in append_files.items():
    if not profiles:
        continue
    path = os.path.join(profiles_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        for p in profiles:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"  {path}: {len(profiles)} profiles")

# Write fill profiles
fill_files = {
    "13_urban_fill.jsonl": [p for p in fill_profiles if p["genre"] == "urban"],
    "14_fantasy_fill.jsonl": [p for p in fill_profiles if p["genre"] == "western_fantasy"],
    "15_xuanhuan_fill.jsonl": [p for p in fill_profiles if p["genre"] == "xuanhuan"],
}
for fname, profiles in fill_files.items():
    path = os.path.join(profiles_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        for p in profiles:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"  {path}: {len(profiles)} profiles, {sum(len(p['utterances']) for p in profiles)} utterances")

# Write negative utterances
neg_path = os.path.join(neg_dir, "character_negative_02.jsonl")
with open(neg_path, "w", encoding="utf-8") as f:
    for n in all_negatives:
        entry = {
            "utterance_id": n[0], "genre": n[1], "context": n[2],
            "text": n[3], "is_consistent": False,
            "rationale": n[4], "error_type": n[5]
        }
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
print(f"  {neg_path}: {len(all_negatives)} negatives")

total_utt = sum(len(p["utterances"]) for p in all_profiles) + len(all_negatives)
print(f"\nTotal: {len(all_profiles)} new profiles, {total_utt} utterances (profiles + standalone negatives)")
