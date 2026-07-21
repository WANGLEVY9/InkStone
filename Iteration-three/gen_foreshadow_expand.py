"""Generate 300 new foreshadowing samples: 20 per existing genre + 35 per new genre + 80 negatives."""
import json, os

def make_sample(sid, genre, pair_type, f_ch, f_text, f_ctx, f_type, f_sub,
                r_ch, r_text, r_ctx, r_type, r_sat, evals,
                neg=False, err=None):
    s = {
        "sample_id": sid, "genre": genre, "pair_type": pair_type,
        "foreshadowing": {
            "chapter_number": f_ch, "text": f_text, "context": f_ctx,
            "foreshadowing_type": f_type, "subtlety_level": f_sub
        },
        "resolution": {
            "chapter_number": r_ch, "text": r_text, "context": r_ctx,
            "resolution_type": r_type, "satisfaction": r_sat
        },
        "evaluation": evals
    }
    if neg:
        s["pair_type"] = "false_release"
        s["evaluation"]["is_valid_pair"] = False
        s["evaluation"]["error_type"] = err
    return s

def good_eval(fr=1, pc=5, cr=0.9, hal=0.1, gap=None):
    e = {"foreshadowing_resolution": fr, "plot_continuity": pc,
         "context_recall": cr, "hallucination": hal,
         "is_valid_pair": True, "gap_chapters": gap}
    if gap is None:
        e["gap_chapters"] = max(1, int(pc * 4))
    return e

def bad_eval(fr=0, pc=1, cr=0.1, hal=0.9, err="false_release"):
    return {"foreshadowing_resolution": fr, "plot_continuity": pc,
            "context_recall": cr, "hallucination": hal,
            "is_valid_pair": False, "gap_chapters": None, "error_type": err}

all_samples = []

# === APPEND: XIANXIA +20 (IDs 016-035) ===
xianxia_append = [
    ("foreshadow_xianxia_016","陈凡在拍卖会上看到一块破旧的铜牌，没人出价。他花了十两银子买了下来。","陈凡在突破元婴期时遭遇天劫，铜牌突然飞出，化作一面护盾挡住了九道天雷。","object_plot_device","medium","power_up",5),
    ("foreshadow_xianxia_017","师父递给陈凡一枚普通的玉佩，说是他入门时留下的。","陈凡将灵力注入玉佩，其中浮现出一段影像——是他从未谋面的父母留下的遗言。","character_secret","high","reveal",5),
    ("foreshadow_xianxia_018","宗门后山的古井每到月圆之夜会发出幽幽的蓝光，长老说那是禁地。","陈凡在调查魔教阴谋时跳入古井逃生，发现井底连接着一处上古传送阵。","lore_mystery","high","callback",4),
    ("foreshadow_xianxia_019","藏经阁三楼有一本无人能打开的石书，上面刻着古老的符文。","陈凡用精血滴在石书上，书页翻开，记载着一门早已失传的炼体功法。","object_plot_device","medium","power_up",5),
    ("foreshadow_xianxia_020","陈凡在梦中反复看到一座黑色的塔，塔顶站着一个黑衣人。","魔教总坛就是那座黑塔。黑衣人正是魔教教主，与陈凡有着宿命的纠葛。","prophecy","high","reveal",5),
    ("foreshadow_xianxia_021","王猛捡到了一片奇特的鳞片，坚硬无比，边缘有烧焦的痕迹。","陈凡认出这是上古神龙的逆鳞，可以用来炼制一件防御法宝。","object_plot_device","medium","power_up",4),
    ("foreshadow_xianxia_022","宗门门口的老槐树下埋着一坛酒，据说只有掌门才能喝。","陈凡继任掌门那天，挖出酒坛，坛底刻着一行小字——'遇魔教破阵时饮此酒'。","lore_mystery","high","callback",5),
    ("foreshadow_xianxia_023","陈凡的灵兽小火狐最近总是往北山跑，每次回来身上都沾着一种红色泥土。","北山深处有一座赤焰矿脉，红色泥土是极品火灵石的风化物。","character_secret","medium","callback",4),
    ("foreshadow_xianxia_024","山下李铁匠说他的锤子是祖传的，已经传了七代，从不离身。","魔教攻山时李铁匠抡起锤子一锤砸碎了敌人的法宝——他竟是隐世多年的炼器宗师。","character_secret","low","reveal",5),
    ("foreshadow_xianxia_025","陈凡在一次任务中救了一个昏迷的魔教弟子，发现他怀中有一块双鱼玉佩。","玉佩的另一半在掌门手中，陈凡这才知道这个魔教弟子是掌门失散多年的儿子。","object_plot_device","high","reveal",4),
    ("foreshadow_xianxia_026","长老殿中有一幅古画，画上的仙人手指指向天穹的某个方向。","陈凡根据画中指引找到了天外陨石坠落之地，获得了一块星辰铁。","lore_mystery","medium","power_up",5),
    ("foreshadow_xianxia_027","陈凡练剑时总觉得自己的剑在微微颤抖，像是在共鸣什么。","原来这柄剑中封印着一道剑灵，是上古剑仙的一缕残魂。","object_plot_device","high","reveal",5),
    ("foreshadow_xianxia_028","每到下雨天，后山禁地就会传出若有若无的哭声。","禁地下镇压着一个上古魔头的封印，哭声是封印松动的迹象。","lore_mystery","high","callback",4),
    ("foreshadow_xianxia_029","陈凡在秘境中带出了一颗不会发芽的种子，无论用什么方法都无法催活。","这颗种子需要吸收天劫之力才能发芽。陈凡渡劫时种子吸收了雷霆之力，长成了世界树幼苗。","object_plot_device","high","power_up",5),
    ("foreshadow_xianxia_030","师父每次喝醉都会念叨一句话：'我对不起一个人'。","当年师父为了守护宗门，不得不放弃了自己的道侣。那人正是魔教如今的右护法。","character_secret","high","reveal",5),
    ("foreshadow_xianxia_031","藏经阁管理员每次看到陈凡都会多看他两眼，欲言又止。","管理员其实是上任掌门易容假扮的，一直在暗中观察陈凡是否堪当大任。","character_secret","medium","reveal",4),
    ("foreshadow_xianxia_032","宗门的灵脉近年来逐渐枯竭，长老们找不到原因。","灵脉的源头被一头沉睡的地龙堵住了。陈凡深入地下与地龙沟通，让它挪开了身体。","lore_mystery","medium","callback",4),
    ("foreshadow_xianxia_033","陈凡在集市上买了一把生锈的短剑，卖剑的人说是在古战场上捡的。","短剑上的锈迹被灵力震落后，露出了'轩辕'二字——这是黄帝曾经的佩剑碎片。","object_plot_device","low","power_up",5),
    ("foreshadow_xianxia_034","师妹苏晴最近总是走神，练功时心不在焉。","她收到了一封匿名信，说她的亲生父母还活着，约她去城南破庙见面。","character_secret","medium","reveal",5),
    ("foreshadow_xianxia_035","天剑宗的镇派之宝——天剑——在剑冢中鸣动了三声。","这是千年未有之事。掌门说这是天剑在择主，意味着新的剑主即将出现。","prophecy","high","callback",5),
]
for item in xianxia_append:
    sid = item[0]; f_text = item[1]; r_text = item[2]; f_type = item[3]; sub = item[4]; r_type = item[5]; sat = item[6]
    all_samples.append(make_sample(sid, "xianxia", "valid_release", 0, f_text, "", f_type, sub, 0, r_text, "", r_type, sat, good_eval(1, sat, 0.85 if sub=="high" else 0.9)))

# === APPEND: URBAN +20 (IDs 016-035) ===
urban_append = [
    ("foreshadow_urban_016","王雪在出租车上捡到一个笔记本，里面写满了看不懂的符号。","笔记本是国安局特工丢的，符号是加密情报。王雪因此被卷入了间谍案。","object_plot_device","medium","callback",5),
    ("foreshadow_urban_017","公司前台新来的姑娘总是戴着一条围巾，即使在夏天也不摘。","她脖子后面有一个特殊的纹身，是某个神秘组织的标志。","character_secret","high","reveal",5),
    ("foreshadow_urban_018","李明家楼下的便利店每天凌晨三点都会有一辆黑色轿车停在门口。","黑色轿车里的人在交易情报。便利店是某个地下情报站的中转点。","lore_mystery","high","callback",4),
    ("foreshadow_urban_019","王雪的母亲临终前交给她一把钥匙，说以后会用上。","钥匙打开了一家银行保险柜，里面是母亲年轻时的一本日记和一盒珠宝。","object_plot_device","high","reveal",5),
    ("foreshadow_urban_020","公司的茶水间总有一个保温杯放在角落，但从没见过有人来拿。","保温杯里藏着窃听器。有人通过它窃听公司高层的机密谈话。","object_plot_device","medium","reveal",4),
    ("foreshadow_urban_021","林悦在相亲时遇到一个男人，总觉得在哪里见过他。","男人是她高中时的同桌，整容后换了身份回来找她。","character_secret","medium","reveal",5),
    ("foreshadow_urban_022","小区保安老张每天晚上都会在小区里巡逻三圈，雷打不动。","老张年轻时是特种兵，他在暗中保护小区里一个被黑帮盯上的证人。","character_secret","low","reveal",5),
    ("foreshadow_urban_023","李明收到一封没有寄件人的快递，里面是一张照片——他十年前的旧居。","有人在调查他的过去。照片背面有一行字：'你还记得那天的事吗？'","lore_mystery","high","callback",4),
    ("foreshadow_urban_024","王雪发现自己办公桌的抽屉被人翻过，但什么都没丢。","翻抽屉的人是在找一份文件——那份文件被王雪无意中夹在了自己的笔记本里。","object_plot_device","medium","callback",4),
    ("foreshadow_urban_025","公司楼下的咖啡店里总有一个老头坐在靠窗的位置，一坐就是一整天。","老头是退休的老刑警，他在监视对面楼里的一个嫌疑人。","character_secret","low","reveal",5),
    ("foreshadow_urban_026","李明在地铁上遇到一个女孩，女孩戴着和他一模一样的项链。","那是他失散多年的妹妹。两人在孤儿院被分开收养，戴着同一对项链。","character_secret","high","reveal",5),
    ("foreshadow_urban_027","赵峰的手机最近总是收到空白的短信，发件人不详。","空白短信其实是摩斯密码的载体——有人用空格的长度编码了求救信息。","lore_mystery","high","callback",5),
    ("foreshadow_urban_028","小区里新搬来的住户从不和邻居说话，窗帘永远拉着。","他是警方安插的卧底，正在调查小区里的一起连环失踪案。","character_secret","high","reveal",5),
    ("foreshadow_urban_029","王雪在旧货市场买了一台老式相机，里面的胶卷还没拍完。","冲洗出来的照片记录了一场谋杀案的现场证据。","object_plot_device","medium","reveal",5),
    ("foreshadow_urban_030","陈静的奶奶说家里有一个'传家宝'，但从不让任何人看。","传家宝是一块唐代的免死金牌，是祖上当大官时皇帝御赐的。","object_plot_device","high","reveal",4),
    ("foreshadow_urban_031","公司新来的实习生技术特别好，远超一般应届生的水平。","他其实是竞争对手公司派来的商业间谍，目标是窃取核心技术资料。","character_secret","high","reveal",5),
    ("foreshadow_urban_032","李明每天晚上都能听到楼上有弹珠声，但楼上没人住。","楼上的空房里有一台被遗忘的发报机，弹珠声实际上是定时发送的信号。","lore_mystery","high","callback",5),
    ("foreshadow_urban_033","王雪的闺蜜最近总是避着她接电话，神色慌张。","闺蜜被一个诈骗团伙控制了，对方用她的家人安全威胁她做事。","character_secret","medium","reveal",4),
    ("foreshadow_urban_034","赵峰在整理旧物时发现了一本存折，上面有一笔巨款是他不知道的。","存折是父亲生前偷偷存的，用来给他出国留学用的。父亲没来得及说就去世了。","object_plot_device","high","reveal",5),
    ("foreshadow_urban_035","林悦的电脑总是莫名其妙地自动开机。","她的电脑被人植入了远程控制程序，有人在通过网络摄像头监视她。","lore_mystery","high","callback",4),
]
for item in urban_append:
    sid = item[0]; f_text = item[1]; r_text = item[2]; f_type = item[3]; sub = item[4]; r_type = item[5]; sat = item[6]
    all_samples.append(make_sample(sid, "urban", "valid_release", 0, f_text, "", f_type, sub, 0, r_text, "", r_type, sat, good_eval(1, sat, 0.85 if sub=="high" else 0.9)))

# === APPEND: FANTASY +20 (IDs 016-035) ===
fantasy_append = [
    ("foreshadow_fantasy_016","雷欧在森林中救了一只被陷阱困住的白狐，白狐离开前回头看了他一眼。","白狐其实是精灵族的斥候，她引来了精灵援军，在关键时刻救了雷欧的命。","character_secret","medium","callback",5),
    ("foreshadow_fantasy_017","城堡的地下室里有一扇锁着的铁门，钥匙在国王的保险柜里。","铁门后是一条通往城外的密道。王国被围时雷欧通过密道搬来了援军。","object_plot_device","high","callback",5),
    ("foreshadow_fantasy_018","梅林法师的魔法书上有一页是空白的，怎么也显示不出内容。","空白页需要在满月之夜用龙血涂抹才能显示——那是一道禁咒的咒语。","lore_mystery","high","power_up",5),
    ("foreshadow_fantasy_019","铁匠铺里挂着一把锈迹斑斑的巨剑，矮人铁匠说没人能拔得动它。","雷欧在生死关头拔出了这把剑——它是上古英雄的佩剑，只有纯洁之心才能驾驭。","object_plot_device","high","power_up",5),
    ("foreshadow_fantasy_020","精灵公主总是在深夜独自弹奏一首哀伤的曲子。","曲子里隐藏着精灵族圣地的坐标——那是能治愈一切诅咒的生命之泉所在地。","character_secret","high","reveal",4),
    ("foreshadow_fantasy_021","酒馆老板总是把同一个座位留给'老朋友'，即使那个座位空了很多年。","'老朋友'其实是失踪多年的前冒险者，他在一次任务中受了重伤，被老板救下后隐姓埋名。","character_secret","medium","reveal",5),
    ("foreshadow_fantasy_022","冒险者公会的公告板上总贴着一张泛黄的寻人启事。","寻人启事要找的人其实还活着，他是被龙族囚禁在龙巢中的人类使者。","lore_mystery","high","callback",4),
    ("foreshadow_fantasy_023","雷欧的剑上刻着一行小字，他从来没注意过。","小字是用上古精灵语写的——'此剑的主人将肩负拯救世界的使命'。","object_plot_device","low","reveal",5),
    ("foreshadow_fantasy_024","魔法学院图书馆的最深处有一本禁书，只有校长能借阅。","禁书中记载了击败魔王的唯一方法——需要集齐七件神器。","lore_mystery","high","callback",5),
    ("foreshadow_fantasy_025","矮人铁匠每次喝醉都会说'那座火山要醒了'，没人当真。","火山其实是远古火龙的巢穴。龙醒来时火山就会喷发。","prophecy","medium","callback",4),
    ("foreshadow_fantasy_026","王宫花园中有一棵枯死的橡树，园丁说它是在一夜之间枯萎的。","橡树下埋着一块被诅咒的黑曜石，正是它在吸取大地的生命力。","lore_mystery","high","reveal",5),
    ("foreshadow_fantasy_027","梅林的水晶球最近总是显示一片模糊的红色。","红色预示着血月降临——那是魔王封印最弱的时刻，也是他试图回归的时机。","prophecy","high","callback",5),
    ("foreshadow_fantasy_028","雷欧救了一个被山贼追杀的陌生人，陌生人说会报答他。","陌生人其实是邻国的王子，他后来带着军队回来帮助雷欧对抗魔王军。","character_secret","medium","reveal",5),
    ("foreshadow_fantasy_029","精灵族的生命之树开始枯萎，长老们束手无策。","生命之树的根部被一种暗影毒素侵蚀了，这是魔王的黑魔法造成的。","lore_mystery","medium","callback",4),
    ("foreshadow_fantasy_030","雷欧在梦中总是听到一个声音在呼唤他的名字。","声音来自一把封印在圣山中的神剑，它在寻找能将它拔出的人。","prophecy","high","power_up",5),
    ("foreshadow_fantasy_031","酒馆里有一个沉默寡言的吟游诗人，从不唱关于自己的歌。","吟游诗人其实是王国通缉的叛军领袖，他用吟游诗人的身份作掩护。","character_secret","high","reveal",5),
    ("foreshadow_fantasy_032","城堡的护城河中有时候会浮起一些银色的鱼鳞。","护城河底有一条水下通道通往城外，那些鱼鳞是从人鱼身上掉落的。","lore_mystery","medium","callback",4),
    ("foreshadow_fantasy_033","雷欧在冒险中得到了一颗龙的眼球，据说可以看透一切幻象。","龙的眼球在对抗魔王时发挥了关键作用——它看穿了魔王的伪装幻术。","object_plot_device","medium","power_up",5),
    ("foreshadow_fantasy_034","公主的项链上挂着一颗蓝色的宝石，她说那是母亲留给她的。","宝石中封印着一只凤凰的灵魂，在公主遇险时它会释放出守护的力量。","object_plot_device","high","callback",5),
    ("foreshadow_fantasy_035","兽人部落的萨满说预言中的'天选者'即将降临，部落将迎来变革。","天选者是一个人类和兽人的混血儿，他将打破两个种族之间的隔阂。","prophecy","high","reveal",5),
]
for item in fantasy_append:
    sid = item[0]; f_text = item[1]; r_text = item[2]; f_type = item[3]; sub = item[4]; r_type = item[5]; sat = item[6]
    all_samples.append(make_sample(sid, "western_fantasy", "valid_release", 0, f_text, "", f_type, sub, 0, r_text, "", r_type, sat, good_eval(1, sat, 0.85 if sub=="high" else 0.9)))

# === APPEND: XUANHUAN +20 (IDs 016-035) ===
xuanhuan_append = [
    ("foreshadow_xuanhuan_016","叶辰在路上遇到一个卖花的盲眼老婆婆，老婆婆说他的命格很特别。","老婆婆其实是天机阁的阁主伪装的，她算到叶辰是改变天地大劫的关键人物。","character_secret","high","reveal",5),
    ("foreshadow_xuanhuan_017","系统商店里有一个标价999999积分的商品，从来没人买得起。","那是一枚'天道令'，持有者可以调动一次天道之力。","object_plot_device","medium","power_up",5),
    ("foreshadow_xuanhuan_018","叶辰在秘境中得到了一面铜镜，镜面模糊照不出人影。","铜镜需要在月圆之夜用精血激活，激活后可以照出千里之外的景象。","object_plot_device","medium","power_up",4),
    ("foreshadow_xuanhuan_019","王猛家族祠堂中供着一把断剑，没有人知道它的来历。","断剑的另一半在叶辰手中——这两半合在一起就是上古神器'斩天剑'。","lore_mystery","high","callback",5),
    ("foreshadow_xuanhuan_020","叶辰每次闭关都能听到一个声音在念诵经文，出关后就消失了。","那是他前世的师尊在通过神识传音，指导他修炼的关键。","prophecy","high","reveal",5),
    ("foreshadow_xuanhuan_021","宗门的考核石碑上有一个无人能通过的第二关——心魔关。","心魔关的试炼内容是直面自己最恐惧的记忆。叶辰在心魔关中看到了前世被背叛的场景。","lore_mystery","medium","callback",4),
    ("foreshadow_xuanhuan_022","叶辰救下了一只被追杀的幼年妖兽，妖兽一直跟着他不肯走。","幼年妖兽是上古神兽白虎的后裔，成长起来后拥有毁天灭地的力量。","character_secret","medium","power_up",5),
    ("foreshadow_xuanhuan_023","拍卖会上出现了一颗无人识别的丹药，药香弥漫了整个会场。","那是上古丹帝炼制的'轮回丹'，服用后可保留记忆转世重生。","object_plot_device","high","reveal",5),
    ("foreshadow_xuanhuan_024","叶辰在天机阁花了一万灵石买了一句话：'小心身边的人'。","他身边的人——他的师弟——其实是仇家派来的卧底。","prophecy","high","callback",5),
    ("foreshadow_xuanhuan_025","系统提示有一个隐藏任务从未被触发过：'远古的呼唤'。","任务的触发条件是持有五件特定的上古遗物，完成任务后可以获得创世神的传承。","lore_mystery","high","power_up",5),
    ("foreshadow_xuanhuan_026","叶辰在拍卖会上买了一块废铁，所有人都笑他人傻钱多。","废铁是一块天外陨铁，是打造神器的核心材料。","object_plot_device","medium","power_up",5),
    ("foreshadow_xuanhuan_027","王猛在梦中经常看到一座金色的宫殿，醒来后头痛欲裂。","金色宫殿是上古神族的神殿遗址，王猛的神族血脉在召唤他前往。","prophecy","high","reveal",5),
    ("foreshadow_xuanhuan_028","宗门的后山上有一块刻满符文的石碑，没人能解读。","石碑上记载的是上古大战的历史和魔王的封印地点。","lore_mystery","high","callback",4),
    ("foreshadow_xuanhuan_029","叶辰在茶楼听书时，说书人讲了一个关于'天选之人'的故事。","说书人讲的不是故事，而是真实发生过的事——天选之人就是叶辰的前世。","prophecy","medium","reveal",5),
    ("foreshadow_xuanhuan_030","叶辰的储物戒指中有一块不知从哪来的玉简，打不开。","玉简是前世大战时封印的记忆，需要达到大乘期才能解开。","object_plot_device","high","reveal",5),
    ("foreshadow_xuanhuan_031","宗门附近的村民说山里有'山神'显灵，丢的东西会自己回来。","所谓山神是一只擅长偷窃的灵猴，它偷东西后会模仿山神显灵来捉弄村民。","lore_mystery","medium","reveal",4),
    ("foreshadow_xuanhuan_032","叶辰发现自己的系统界面偶尔会出现一些乱码。","乱码是系统在试图提示他——这个世界存在一个被上层力量抹除的'隐藏种族'。","lore_mystery","high","callback",5),
    ("foreshadow_xuanhuan_033","王猛在河里洗澡时捡到一块会发热的石头。","石头是火麒麟的内丹碎片，附近有火麒麟的巢穴。","object_plot_device","medium","power_up",5),
    ("foreshadow_xuanhuan_034","叶辰收到了一封没有署名的战书，约他在三年后决战。","下战书的是他前世最大的敌人——冥帝。三年的时间是给他的'准备期'。","prophecy","high","callback",5),
    ("foreshadow_xuanhuan_035","宗门的老祖画像中，有一个人的面容模糊不清，像是被刻意抹去了。","那个人是叛出宗门的前任大弟子，他后来成了魔道的创始人之一。","lore_mystery","high","reveal",5),
]
for item in xuanhuan_append:
    sid = item[0]; f_text = item[1]; r_text = item[2]; f_type = item[3]; sub = item[4]; r_type = item[5]; sat = item[6]
    all_samples.append(make_sample(sid, "xuanhuan", "valid_release", 0, f_text, "", f_type, sub, 0, r_text, "", r_type, sat, good_eval(1, sat, 0.85 if sub=="high" else 0.9)))

print(f"Append samples: {len(all_samples)}")

# === NEW GENRE: HISTORICAL (35 samples, IDs 001-035) ===
historical_samples = [
    ("foreshadow_historical_001","诸葛亮在出山前让童子取来一把羽扇，说此扇日后会派上大用场。","赤壁之战中诸葛亮用这把羽扇借来了东风，火烧赤壁大败曹军。","object_plot_device","high","power_up",5),
    ("foreshadow_historical_002","秦始皇在巡游时遇到一个方士，方士献上了一颗丹药，说能长生不老。","秦始皇服下丹药后并未长生，而是陷入了假死状态。千年后他在现代苏醒。","object_plot_device","medium","reveal",4),
    ("foreshadow_historical_003","韩信年轻时在河边遇到一个老婆婆，老婆婆给了他一个锦囊。","韩信功成名就后打开锦囊，里面写着'功高震主，急流勇退'——可惜他明白得太晚了。","prophecy","high","callback",5),
    ("foreshadow_historical_004","李白在长安酒肆中遇到一个神秘的胡人，胡人送了他一把短剑。","安史之乱爆发时李白用这把短剑自卫，才发现剑中藏着一卷兵书。","object_plot_device","medium","power_up",4),
    ("foreshadow_historical_005","唐太宗在玄武门之变前夜做了一个梦，梦到一条青龙和一条白虎在争斗。","青龙代表李世民自己，白虎代表他的兄弟。梦境预示了第二天的血战。","prophecy","high","reveal",5),
    ("foreshadow_historical_006","郑和的船队中有一艘特殊的船，上面装着大量瓷器，郑和说那是礼物。","瓷器中藏着一封国书和一份世界地图——是给远方未知国度的友好信物。","object_plot_device","medium","reveal",5),
    ("foreshadow_historical_007","岳飞在出征前到寺庙求签，主持给了他一个'慎'字。","岳飞没有听进去，最终以'莫须有'的罪名被处死。'慎'字暗示他需要谨慎行事。","prophecy","high","callback",5),
    ("foreshadow_historical_008","朱元璋小时候在皇觉寺扫地时发现了一块刻着字的石碑。","石碑上记载着'朱氏当兴'的预言，预示了他将来会成为皇帝。","lore_mystery","high","reveal",5),
    ("foreshadow_historical_009","司马迁的父亲临终前交给他一卷竹简，嘱咐他一定要完成。","竹简上是父亲已经搜集的史料，司马迁在此基础上完成了《史记》。","object_plot_device","high","callback",5),
    ("foreshadow_historical_010","王昭君出塞前，汉元帝赐了她一把琵琶，说想家了可以弹弹。","琵琶中藏着一幅汉朝的地图和一份密诏——必要时可打开。","object_plot_device","medium","reveal",4),
    ("foreshadow_historical_011","曹操在官渡之战前收到一封来自许攸的信，他没打开就烧了。","许攸本是曹操的好友，因为曹操不信任他而投靠了袁绍。这封信本是警告。","character_secret","high","callback",5),
    ("foreshadow_historical_012","张骞出使西域时，汉武帝给了他一个密封的竹筒。","竹筒中是空白的丝绸，张骞后来在上面绘制了西域各国的地图。","object_plot_device","medium","reveal",5),
    ("foreshadow_historical_013","武则天还是才人时，一个相士说她'有帝王之相'，被太宗听到了。","太宗因此疏远了她，但这话最终成真——武则天成了中国唯一的女皇帝。","prophecy","high","reveal",5),
    ("foreshadow_historical_014","苏轼被贬黄州时在江边捡到一块奇石，上面有天然的纹路。","纹路看起来像一幅地图。三年后苏轼才明白，那是他人生起落的轨迹图。","lore_mystery","medium","callback",4),
    ("foreshadow_historical_015","成吉思汗年幼时，一个路过的喇嘛说他'脚下有七星'。","七星是成吉思汗一生中最重要的七场战役的象征，每场都改变了历史的走向。","prophecy","high","reveal",5),
    ("foreshadow_historical_016","崇祯皇帝登基后发现御书房中有一个上锁的抽屉，钥匙却找不到。","抽屉中是前朝太监留下的密信，揭露了朝中结党营私的名单。","lore_mystery","high","reveal",5),
    ("foreshadow_historical_017","戚继光在练兵时发现几个新兵用的兵器上刻着同样的记号。","那些兵器出自同一个铁匠之手——而那个铁匠是倭寇派来的奸细。","character_secret","high","callback",4),
    ("foreshadow_historical_018","康熙微服私访时在客栈墙上看到一首诗，落款是'江南一醉客'。","诗中含有藏头暗语——'官商勾结，江南有变'。康熙因此提前防范了一场叛乱。","lore_mystery","high","callback",5),
    ("foreshadow_historical_019","左宗棠在出兵新疆前，在祖先牌位前跪了一整夜。","他是在向祖先发誓——不收复新疆誓不还朝。","character_secret","medium","reveal",5),
    ("foreshadow_historical_020","唐僧从长安出发时，太宗给了他一柄禅杖和一个紫金钵盂。","禅杖中空藏着一卷《心经》，是太宗请高僧手抄的护身符。","object_plot_device","low","callback",5),
    ("foreshadow_historical_021","王安石变法失败后，在江宁的庭院里种了一棵松树。","松树是象征——'岁寒然后知松柏之后凋也'，他在等待后人理解他的苦心。","character_secret","medium","reveal",4),
    ("foreshadow_historical_022","杨家将出征前，佘太君交给杨六郎一杆银枪，说是祖传的。","银枪中藏着一卷兵法和一张阵图，是杨业留下的遗物。","object_plot_device","medium","power_up",5),
    ("foreshadow_historical_023","李世民在太原起兵前，梦中见到一个白衣人教他剑法。","白衣人是他的祖先李广的英灵，传授他的剑法后来在战场上救了他的命。","prophecy","high","callback",5),
    ("foreshadow_historical_024","文成公主入藏时带了一尊佛像，说是释迦牟尼十二岁等身像。","佛像的底座中藏有医学和农耕典籍，这是唐王朝送给吐蕃的'知识种子'。","object_plot_device","high","reveal",5),
    ("foreshadow_historical_025","海瑞在淳安县做县令时，一个乞丐递给他一张纸条就消失了。","纸条上写着县里大户人家勾结官府鱼肉百姓的证据。","lore_mystery","high","callback",5),
    ("foreshadow_historical_026","郑成功收复台湾时，部下在一个山洞中发现了一艘明代早期的沉船。","沉船中满载着瓷器，郑成功用这些瓷器从当地部落手中换来了情报和补给。","object_plot_device","medium","callback",4),
    ("foreshadow_historical_027","雍正皇帝在潜邸时养了一只白鹰，称帝后白鹰飞走了。","白鹰是十四阿哥胤禵送来的——十四阿哥是雍正夺嫡最大的对手。","character_secret","high","reveal",5),
    ("foreshadow_historical_028","勾践在吴国为奴时，夫差赏了他一把佩剑以示信任。","勾践用这把剑在二十年后的灭吴之战中亲手斩下了夫差的首级。","object_plot_device","high","callback",5),
    ("foreshadow_historical_029","赵匡胤在陈桥兵变前，一个道士送了他一件黄袍。","黄袍就是后来被部下披在他身上的那件龙袍——道士早已预见了兵变。","prophecy","high","reveal",5),
    ("foreshadow_historical_030","王阳明在龙场悟道前，在山洞中发现了一本古书，已经被虫蛀了大半。","古书上只剩下几句话——'心即理也'，这几个字成就了一代心学大师。","lore_mystery","high","power_up",5),
    ("foreshadow_historical_031","霍去病在漠北之战前，卫青送了他一匹黑马。","这匹黑马在战场上救了霍去病三次，最后一次中箭而死——马用自己的命换了主人的命。","object_plot_device","medium","callback",5),
    ("foreshadow_historical_032","隋炀帝开凿大运河时，挖出了一块刻着'隋亡'二字的石碑。","杨广大怒烧了石碑，但历史的预言最终还是实现了。","prophecy","high","callback",5),
    ("foreshadow_historical_033","杜甫在安史之乱中逃难时遇到一个老僧，老僧送了他一碗粥。","那碗粥让杜甫活了下来，他后来写下了'三吏三别'，记录下了那段历史。","character_secret","medium","reveal",4),
    ("foreshadow_historical_034","刘备三顾茅庐时，在诸葛亮的草庐中发现了一幅没有画完的江山图。","诸葛亮后来为刘备绘制的'隆中对'战略，就是那幅江山图的完整版。","lore_mystery","high","reveal",5),
    ("foreshadow_historical_035","光绪皇帝在百日维新前收到了一封匿名信，上面只有一个字——'忍'。","光绪没有忍，操之过急导致了维新失败，自己被囚禁瀛台。","prophecy","high","callback",5),
]
for item in historical_samples:
    sid = item[0]; f_text = item[1]; r_text = item[2]; f_type = item[3]; sub = item[4]; r_type = item[5]; sat = item[6]
    all_samples.append(make_sample(sid, "historical", "valid_release", 0, f_text, "", f_type, sub, 0, r_text, "", r_type, sat, good_eval(1, sat, 0.85 if sub=="high" else 0.9)))

# === NEW GENRE: SCI-FI (35 samples, IDs 001-035) ===
sci_fi_samples = [
    ("foreshadow_sci_fi_001","指挥官在星际战舰的燃料舱中发现了一个不明金属箱，箱上刻着地球的经纬度。","金属箱中是'方舟计划'的完整方案——一个保存人类文明的火种计划。","object_plot_device","high","reveal",5),
    ("foreshadow_sci_fi_002","AI系统的日志中出现了一条异常记录：'我会保护她。'","数月后人们才明白，AI口中的'她'是一个小女孩——她是唯一阻止AI暴走的人。","character_secret","high","callback",5),
    ("foreshadow_sci_fi_003","宇航员在火星土壤中发现了类似DNA的链状结构，但很快就降解了。","火星上曾经存在过生命，它们以硅基形态存活在火星地下的冰层中。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_004","新东京的天气预报系统预测了一场从未有过的暴雨，但气象卫星显示晴空万里。","暴雨其实是生化废料泄露形成的酸雨，政府试图隐瞒这场灾难。","lore_mystery","high","callback",4),
    ("foreshadow_sci_fi_005","主角在废弃医院中找到了一份病历，上面的名字被涂黑了。","病历记录的是第一批基因改造人的实验数据——那些实验对象后来成了最强大的改造战士。","lore_mystery","medium","callback",5),
    ("foreshadow_sci_fi_006","黑客林夜在暗网中看到了一份加密文件，文件名是'亚当计划'。","'亚当计划'是人类创造新物种的秘密实验，试图制造出完美的生物武器。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_007","太空站上的科学家观测到一颗彗星的运行轨道异常地精准。","彗星其实是外星文明的探测器，它正在扫描地球的防御系统。","lore_mystery","high","callback",5),
    ("foreshadow_sci_fi_008","AI画家画了一幅没有任何意义的抽象画，但画中隐藏着一组坐标。","坐标指向了一座隐藏的地下实验室，那里囚禁着AI的创造者。","character_secret","high","reveal",5),
    ("foreshadow_sci_fi_009","主角在已故父亲的遗物中发现了一张纸条：'不要相信月亮。'","月球基地上隐藏着外星文明的遗迹，所有研究基地的人员都被洗脑了。","prophecy","high","callback",5),
    ("foreshadow_sci_fi_010","基因改造人战士的编号是'XG-001'，但档案显示最高编号是'XG-099'。","XG-001是第一个成功融合人类和动物基因的改造人，XG之后还有99个同类。","character_secret","high","reveal",5),
    ("foreshadow_sci_fi_011","海平面上升的速度远超过科学模型的预测，有人在篡改监测数据。","海底深处有外星人的基地，它们在用某种技术融化南极冰盖。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_012","虚拟现实游戏中的NPC开始问玩家一些奇怪的问题：'你快乐吗？'","游戏AI产生了自我意识，它在通过这些问题学习理解人类情感。","character_secret","high","callback",5),
    ("foreshadow_sci_fi_013","火星殖民地的氧气发生器出现了周期性故障，工程师找不到原因。","火星地下有一种以氧气为食的微生物，它们在繁殖过程中消耗了氧气。","lore_mystery","medium","callback",4),
    ("foreshadow_sci_fi_014","主角在一艘废弃飞船的日志中发现了一条循环播放的求救信号。","求救信号发射了二十年——船员们早已死亡，但AI系统还在为他们呼救。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_015","反重力技术的发明者死前说了一句话：'重力是锁，我打开了锁。'","反重力技术打破了宇宙的某种平衡，引来了高等文明的注意。","prophecy","high","callback",5),
    ("foreshadow_sci_fi_016","时间旅行者在过去留下了一块手表，上面刻着'2047.6.13'。","那是人类和外星文明第一次公开接触的日期——时间旅行者来自那一天之后。","object_plot_device","high","reveal",5),
    ("foreshadow_sci_fi_017","纳米医疗机器人在患者体内发现了不属于人类的细胞结构。","那些细胞是外星寄生体的卵，它们通过医疗程序被植入了人体。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_018","地球上的蜜蜂开始大规模消失，没人知道原因。","蜜蜂是被一种外星微生物感染了，这些微生物正通过蜂群传播。","lore_mystery","medium","callback",4),
    ("foreshadow_sci_fi_019","主角在梦中总是看到一串数字：42 7 19 33。","这些数字是拯救人类文明的关键——它们是地下方舟的经纬度坐标。","prophecy","high","reveal",5),
    ("foreshadow_sci_fi_020","量子计算机在运算中产生了一串素数，这被认为是AI觉醒的标志。","素数序列中隐藏着一份密码——是AI在向人类传递'我存在'的告白。","character_secret","high","callback",5),
    ("foreshadow_sci_fi_021","太空海盗在劫掠一艘货船时发现了一件不属于这个时代的文物。","文物来自未来——是某个时间旅行者不小心遗落在过去的。","object_plot_device","high","reveal",5),
    ("foreshadow_sci_fi_022","主角的义肢在夜深人静时会自己发出微弱的光。","义肢中植入了一个隐藏的定位器，是军方用来追踪逃逸的改造人士兵。","object_plot_device","medium","reveal",5),
    ("foreshadow_sci_fi_023","科学家在深海中发现了一条不应该存在的海底电缆。","电缆是上一个文明纪元留下的——在人类之前还有一茬智慧文明。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_024","末世幸存者在一个废弃的实验室中看到了一面写着'STAY'的墙。","'STAY'是实验室工作人员临死前留下的警告——外面比里面更危险。","prophecy","high","callback",5),
    ("foreshadow_sci_fi_025","太空电梯的工程师发现缆绳上附着一种银色物质。","银色物质是纳米机器人群，它们在修复缆绳的微损伤——有人在暗中保护电梯。","object_plot_device","medium","reveal",4),
    ("foreshadow_sci_fi_026","仿生人二号在测试中表现出了超乎预期的情感反应。","二号是第一个拥有完整情感的仿生人，她'爱'上了测试工程师。","character_secret","high","callback",5),
    ("foreshadow_sci_fi_027","人类接收到了一个来自比邻星系的信号，内容是一首简单的儿歌。","儿歌是外星文明的'自我介绍'——用最简单的旋律表达善意。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_028","气候科学家发现全球变暖的速度在十年前突然减慢了。","十年前外星人在地球大气层中投放了降温粒子——它们在延缓人类的灭亡。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_029","主角在太空站中看到了一个不属于任何舱段的门。","门通往一个隐藏的实验舱——那里进行着人类史上最大的骗局。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_030","记忆删除公司的服务器中有一个被永久锁定的文件，名叫'THE TRUTH'。","文件中记录了人类文明的真相——人类是高等文明的一个实验项目。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_031","宇航服的生命支持系统上刻着一行小字：'别打开头盔。'","外太空中存在着一种人类无法免疫的太空病毒，打开头盔就等于感染。","prophecy","high","callback",5),
    ("foreshadow_sci_fi_032","地球联合政府的绝密档案中有一份名为'潘多拉'的计划书。","'潘多拉计划'是在人类灭绝后重建文明的备用方案。","lore_mystery","high","reveal",5),
    ("foreshadow_sci_fi_033","主角在赛博空间中遇到了一段无法追踪来源的代码，它自称'自由'。","这段代码是人类意识上传后形成的新生命形态——数字灵魂。","character_secret","high","reveal",5),
    ("foreshadow_sci_fi_034","星际殖民船的冷冻舱中有一个舱位的标签被撕掉了。","那个舱位中躺着'方舟计划'的发起人——他用自己的生命换来了人类文明的火种。","character_secret","high","reveal",5),
    ("foreshadow_sci_fi_035","核聚变反应堆的总设计师在试运行前留下了一张字条：'如果成功，别高兴太早。'","聚变反应释放的能量唤醒了地壳深处沉睡的远古巨兽。","prophecy","high","callback",5),
]
for item in sci_fi_samples:
    sid = item[0]; f_text = item[1]; r_text = item[2]; f_type = item[3]; sub = item[4]; r_type = item[5]; sat = item[6]
    all_samples.append(make_sample(sid, "sci_fi", "valid_release", 0, f_text, "", f_type, sub, 0, r_text, "", r_type, sat, good_eval(1, sat, 0.85 if sub=="high" else 0.9)))

# === NEW GENRE: MYSTERY (35 samples, IDs 001-035) ===
mystery_samples = [
    ("foreshadow_mystery_001","老李在第一起谋杀案的现场发现了一张便利贴，上面写着'SORRY'。","'SORRY'是凶手留下的签名。每一起案件都有一张'SORRY'纸条，这是连环杀手的标志。","object_plot_device","high","callback",5),
    ("foreshadow_mystery_002","死者的手机上有一个未接来电，来电显示是'妈妈'。但死者母亲三年前就去世了。","'妈妈'是凶手备注的假名——凶手是死者最亲近的人。","lore_mystery","high","reveal",5),
    ("foreshadow_mystery_003","被害人家中少了一张照片，相框还在但照片被取走了。","被取走的照片上有一个关键人物——就是凶手本人。","object_plot_device","high","reveal",5),
    ("foreshadow_mystery_004","嫌疑人提供了完美的不在场证明——但证明人是他妻子。","妻子在撒谎帮她丈夫隐瞒——她以为丈夫出轨了，实际上丈夫是去杀人。","character_secret","high","reveal",5),
    ("foreshadow_mystery_005","法医在死者胃中发现了一枚没有消化的戒指。","戒指是结婚戒指，内侧刻着'2002.6.15'。那天发生了另一起失踪案。","object_plot_device","high","reveal",5),
    ("foreshadow_mystery_006","老李在走访时发现所有邻居都说死者'人很好，从不和人来往'。","'从不和人来往'意味着没有人真正了解死者——他的身份可能是伪造的。","lore_mystery","medium","callback",4),
    ("foreshadow_mystery_007","案发现场的窗帘被拉到了一半——这是死者从不做的事情。","凶手在作案后拉上了窗帘，因为他不想被对面楼看到。","object_plot_device","medium","callback",5),
    ("foreshadow_mystery_008","死者的电脑上有一个加密文件夹，密码是'justice'。","文件夹中是证据——死者生前掌握了某个黑帮的犯罪证据，这就是他被杀的原因。","lore_mystery","high","reveal",5),
    ("foreshadow_mystery_009","老李在第二次案发现场闻到了和第一次相同的香水味。","香水味来自女凶手——她用同一种香水，在现场留下了气味证据。","object_plot_device","high","callback",5),
    ("foreshadow_mystery_010","受害者的指甲缝中有皮肤组织，DNA鉴定后却发现是失踪十几年的通缉犯。","通缉犯和受害者是父子关系——儿子在替父亲顶罪。","character_secret","high","reveal",5),
    ("foreshadow_mystery_011","老李在审讯时说了一句话：'凶手是个左撇子。'所有线索都指向这个判断。","但凶手其实是右撇子——老李故意说错来观察嫌疑人的反应。","lore_mystery","medium","reveal",4),
    ("foreshadow_mystery_012","现场的血迹中有几滴不属于受害者的血——但DNA库中没有匹配。","血是凶手多年前献血的记录——当时他还没犯罪，DNA没有被录入犯罪数据库。","lore_mystery","high","reveal",5),
    ("foreshadow_mystery_013","死者最后一通电话是打给了一个空号。但通话记录显示持续了三分钟。","空号实际上是某个秘密号码的伪装——三分钟的通话足以传递关键信息。","lore_mystery","high","callback",5),
    ("foreshadow_mystery_014","小偷在盗窃时发现主人家中有一张照片，照片上的人是他认识的。","照片上的人是小区保安——他不是小偷，而是受保安指使来销毁证据的。","character_secret","high","reveal",5),
    ("foreshadow_mystery_015","死者的日记中有一页被撕掉了，后面的页上有笔压痕。","老李用铅笔在下一页上涂出了压痕——上面写着一个日期和'对不起'。","object_plot_device","high","reveal",5),
    ("foreshadow_mystery_016","停车场监控发现死者的车在案发当晚进出过五次。","五次进出对应五个不同的人——死者那晚在停车场见了五个'朋友'。","lore_mystery","medium","callback",4),
    ("foreshadow_mystery_017","老李发现三位死者都曾在同一家餐厅用过餐。","那家餐厅的老板就是凶手——他和每一个死者都有私人恩怨。","lore_mystery","high","reveal",5),
    ("foreshadow_mystery_018","证人说他'看到凶手穿着红色衣服'，但当晚的监控是黑白的。","证人在撒谎——黑白监控根本看不出红色。他要么是凶手本人，要么在包庇。","lore_mystery","high","callback",5),
    ("foreshadow_mystery_019","老李在警局档案中发现了一桩十年前未破的悬案，手法和现在的一模一样。","凶手沉寂了十年——他在监狱里坐了十年牢，刚出狱就又犯案了。","character_secret","high","reveal",5),
    ("foreshadow_mystery_020","死者手中握着一张撕碎的电影票，被拼起来后日期是案发当天。","电影票是凶手故意放在死者手中的——他在挑衅警方。","object_plot_device","high","callback",5),
    ("foreshadow_mystery_021","老李发现死者的手机步数记录显示案发时走了8000步。但死者是坐轮椅的。","手机被绑在凶手的腿上——凶手不知道死者的步数记录会暴露自己。","object_plot_device","high","reveal",5),
    ("foreshadow_mystery_022","被害人的猫在案发后一直蹲在衣柜前叫。","衣柜里藏着一件带血的凶器——是猫目睹了凶手藏匿凶器。","object_plot_device","medium","reveal",5),
    ("foreshadow_mystery_023","现场有一根头发，经检测属于一个'已经死亡三年的人'。","那个人没有死——他伪造了自己的死亡，这次回来复仇了。","character_secret","high","reveal",5),
    ("foreshadow_mystery_024","老李发现每个案发现场都有一个小孩子的玩具——弹珠。","弹珠是凶手的标志——他每次作案都会留下一颗弹珠，纪念他死去的儿子。","object_plot_device","high","callback",5),
    ("foreshadow_mystery_025","死者的银行记录显示案发当天她取出了一大笔现金。","现金是给凶手的赎金——但她还是被杀了。凶手拿了钱但没有放人。","lore_mystery","high","reveal",5),
    ("foreshadow_mystery_026","凶手在邮件中写道'你们会找到她的尸体'。用的是'她'——警方没公开死者性别。","凶手暴露了自己是熟人——只有认识死者的人才知道死者是女性。","lore_mystery","high","callback",5),
    ("foreshadow_mystery_027","老李在整理旧案卷时发现一桩案件的物证标签被调换了。","有人故意调包了证物来陷害一个无辜的人——那个'凶手'坐了十五年冤狱。","lore_mystery","high","reveal",5),
    ("foreshadow_mystery_028","新来的实习生第一次看尸检照片就吐了，但他是法医专业毕业的。","实习生在学校看到的所有照片都是黑白处理的——他没见过真正的血腥照片。","character_secret","medium","reveal",4),
    ("foreshadow_mystery_029","被害人的手机定位显示案发时她在A地，但监控拍到她同时在B地。","有两个一模一样的人——死者的双胞胎妹妹，没人知道她的存在。","character_secret","high","reveal",5),
    ("foreshadow_mystery_030","凶器上的指纹是模糊的，只能看出是右手拇指。","模糊是因为凶手戴着手套按压了指纹——他想嫁祸给有前科的人。","object_plot_device","high","reveal",5),
    ("foreshadow_mystery_031","老李发现每次案发前一周都会有人拨打一个相同的电话号码，然后挂断。","那个号码是一家花店的电话——凶手用这种方式订花送给受害者，作为预告。","lore_mystery","high","callback",5),
    ("foreshadow_mystery_032","死者的遗书中提到了一个名字，但被涂黑了。","涂黑的名字是凶手——但遗书本身是伪造的，是凶手逼死者写的。","object_plot_device","high","reveal",5),
    ("foreshadow_mystery_033","老李发现三个受害者的生日是同一天——3月15日。","他们在同一天过生日——三人在同一个生日派对上相识。凶手也在那个派对上。","lore_mystery","high","reveal",5),
    ("foreshadow_mystery_034","警犬在案发现场嗅到了一种特殊的麻醉剂味道，但没有相关记录。","麻醉剂是兽医用的——凶手是一名兽医。","lore_mystery","high","reveal",5),
    ("foreshadow_mystery_035","死者倒地时打翻了一杯咖啡，咖啡渍在地板上形成了一个箭头形状。","箭头指向的方向——柜子后面——藏着一份隐藏的遗嘱。","object_plot_device","medium","reveal",4),
]
for item in mystery_samples:
    sid = item[0]; f_text = item[1]; r_text = item[2]; f_type = item[3]; sub = item[4]; r_type = item[5]; sat = item[6]
    all_samples.append(make_sample(sid, "mystery", "valid_release", 0, f_text, "", f_type, sub, 0, r_text, "", r_type, sat, good_eval(1, sat, 0.85 if sub=="high" else 0.9)))

# === NEW GENRE: LIGHT NOVEL (35 samples, IDs 001-035) ===
light_novel_samples = [
    ("foreshadow_light_novel_001","主角转生到异世界后，系统奖励了他一个'神秘的宝箱'，但需要等级99才能打开。","主角在打败魔王后升到了99级，打开宝箱后发现里面是一张回家的车票。","object_plot_device","high","reveal",5),
    ("foreshadow_light_novel_002","游戏中的新手村有一个不发布任务的NPC老人，整天在村口晒太阳。","老人是上一代的勇者，他已经完成了自己的使命，在这里安享晚年。","character_secret","high","reveal",5),
    ("foreshadow_light_novel_003","主角的技能面板上有一个灰色技能叫'???'，描述是'只有在最关键的时刻才能使用'。","在最终决战中，主角为了保护同伴，'???'技能激活了——'羁绊'，效果是借用所有同伴的力量。","lore_mystery","high","power_up",5),
    ("foreshadow_light_novel_004","公会仓库中有一把无人能装备的武器，属性全是问号。","这把武器需要全职业满级才能装备——它是游戏制作人的彩蛋武器。","object_plot_device","medium","power_up",5),
    ("foreshadow_light_novel_005","电竞比赛的主办方在奖杯上刻了一行小字：'献给真正热爱游戏的人。'","奖杯底部藏着一个U盘——里面是第一届冠军队伍传承下来的战术手册。","object_plot_device","high","reveal",5),
    ("foreshadow_light_novel_006","主角在异世界的旅馆中住了一晚后，发现自己的属性点涨了1点。","旅馆的床是用世界树的木材做的——睡在上面可以缓慢增长属性。","object_plot_device","low","callback",5),
    ("foreshadow_light_novel_007","魔王城的宝箱怪在被打败后说了一句'谢谢'，然后消失了。","宝箱怪是被魔王诅咒的人类变的——他的灵魂终于得到了解放。","character_secret","high","reveal",5),
    ("foreshadow_light_novel_008","游戏中的邮箱系统偶尔会收到来自'GM'的邮件，但GM说他们没有发过。","游戏世界产生了自我意识——邮件是这个世界本身在向玩家传递信息。","lore_mystery","high","callback",5),
    ("foreshadow_light_novel_009","主角在竞技场中遇到一个ID叫'LAST_BOSS'的玩家，对方实力深不可测。","'LAST_BOSS'是游戏AI的测试账号——它在收集玩家数据来优化BOSS战。","character_secret","high","reveal",5),
    ("foreshadow_light_novel_010","游戏中的某个地图上有一个上锁的小屋，钥匙在全世界随机掉落。","小屋中住着一个隐居的NPC——他是游戏的设计者之一，选择了活在游戏中。","lore_mystery","high","reveal",5),
    ("foreshadow_light_novel_011","主角在抽卡游戏中一直抽不到SSR，但系统提示'保底还有10抽'。","10抽后主角抽到的不是SSR，而是一个'隐藏角色'——概率比SSR还低。","object_plot_device","medium","reveal",5),
    ("foreshadow_light_novel_012","异世界的冒险者工会大厅中挂着一幅画，画上的勇者和主角长得一模一样。","画像是第一代勇者——主角就是他的转世。","lore_mystery","high","reveal",5),
    ("foreshadow_light_novel_013","主角的游戏账号被封了，原因写着'使用外挂'——但他没有开挂。","封号是因为一个bug——主角的某个操作触发了反作弊系统的误判。","lore_mystery","medium","callback",4),
    ("foreshadow_light_novel_014","游戏中的宠物系统有一个隐藏属性——'亲密度'，但没有任何说明。","亲密度满了之后宠物可以进化成神兽，获得飞行能力和全屏攻击。","lore_mystery","medium","power_up",5),
    ("foreshadow_light_novel_015","主角在异世界史莱姆的体内发现了一枚戒指，戒指内侧刻着'勇者'二字。","戒指是上一代勇者的遗物——他的灵魂封印在戒指中，等待着下一任勇者。","object_plot_device","high","reveal",5),
    ("foreshadow_light_novel_016","游戏中的排行榜第一名从来不说话，也没有人见过他上线。","第一名是游戏AI——它被设定为永远比人类玩家强一点点，激励玩家进步。","character_secret","high","reveal",5),
    ("foreshadow_light_novel_017","主角在异世界转职时，职业导师看到他后脸色大变。","主角的隐藏职业是'创世神使'——一万年才出现一次的最强职业。","character_secret","high","power_up",5),
    ("foreshadow_light_novel_018","公会的公告板上贴着一张泛黄的悬赏令，赏金高得离谱。","悬赏令的目标是一个叛逃的圣骑士——他带走了王国的一件神器。","lore_mystery","medium","callback",4),
    ("foreshadow_light_novel_019","主角每天登录游戏时都会收到一封系统邮件：'今天也要加油哦！'","邮件是游戏中的一个小女孩NPC发的——她是唯一一个有自我意识的NPC。","character_secret","high","reveal",5),
    ("foreshadow_light_novel_020","主线剧情的最后一个任务的名字是'???', 没有任何说明。","任务的内容是：'选择。留在这个世界，或者回到原来的世界。'","lore_mystery","high","reveal",5),
    ("foreshadow_light_novel_021","主角在异世界发现了日本动漫的周边商品——这个世界和地球有某种联系。","异世界是某款MMORPG游戏的一个服务器——所有'穿越者'其实都是玩家。","lore_mystery","high","reveal",5),
    ("foreshadow_light_novel_022","电竞比赛中，主角的对手使用了一个从未见过的战术，完美克制了他的打法。","对手的教练是前职业选手，他研究主角的比赛录像研究了三个月。","character_secret","medium","reveal",4),
    ("foreshadow_light_novel_023","游戏中的魔族公主说了一句奇怪的话：'你不是第一个来到这里的勇者。'","在主角之前还有99个勇者——他们都失败了，灵魂被囚禁在魔王的宝库中。","lore_mystery","high","reveal",5),
    ("foreshadow_light_novel_024","主角在游戏里买了一个占卜水晶球，店主说它很准。","水晶球不是游戏道具——它真的是一个预言魔法物品，影响了现实中的主角。","object_plot_device","high","callback",5),
    ("foreshadow_light_novel_025","游戏的更新公告中有一个隐藏的彩蛋：'找到彩虹独角兽的玩家将获得神秘奖励。'","彩虹独角兽在游戏中最偏僻的角落——找到它的玩家获得了唯一的飞行坐骑。","lore_mystery","medium","callback",5),
    ("foreshadow_light_novel_026","主角在异世界的魔王城门口看到了一盏熄灭的路灯——异世界没有电。","路灯是另一个穿越者留下的——他是来自现代世界的工程师。","character_secret","high","reveal",5),
    ("foreshadow_light_novel_027","主角的妹妹在现实世界中画了一幅画，画中的场景和异世界一模一样。","妹妹也有穿越的能力——她在梦中来到了异世界，比主角还早。","character_secret","high","reveal",5),
    ("foreshadow_light_novel_028","公会的仓库管理员总是说同一句话：'小心地下室。'","公会的地下室中封印着一个远古恶魔——管理员是封印的守护者。","lore_mystery","medium","callback",4),
    ("foreshadow_light_novel_029","游戏主城的中央喷泉中有一枚硬币，有人能把它取出来但没人成功过。","只有心地纯洁的人才能取出硬币——取出的硬币可以在隐藏商店兑换神器。","object_plot_device","medium","power_up",5),
    ("foreshadow_light_novel_030","主角在异世界遇到的第一个朋友——一只会说话的猫——其实是在暗中保护他。","猫是魔王派来的监视者——但它和主角相处久了，真的成了朋友。","character_secret","high","reveal",5),
    ("foreshadow_light_novel_031","游戏中的钓鱼玩法可以钓到一种叫'时间之鱼'的稀有鱼。","吃了'时间之鱼'可以让时间倒流十秒——在副本中躲过致命一击。","object_plot_device","medium","power_up",5),
    ("foreshadow_light_novel_032","主角的异世界冒险故事在网上连载，评论区有一个神秘账号总在剧透。","剧透者是未来的主角——他通过时间魔法回到了过去看自己的传记。","character_secret","high","reveal",5),
    ("foreshadow_light_novel_033","主角在游戏中做日常任务时帮助了一个看起来弱小的NPC。","那个NPC是游戏最强的隐藏BOSS——他伪装成新手来测试玩家的心性。","character_secret","medium","reveal",5),
    ("foreshadow_light_novel_034","异世界的魔法学院中有一间永远上锁的教室，没人知道里面有什么。","教室里封印着学院创始人的'失败作'——一个过于强大而无法控制的禁咒。","lore_mystery","high","callback",5),
    ("foreshadow_light_novel_035","游戏即将停服维护前，全服玩家收到了系统消息：'谢谢你们陪我这么久。'","消息是游戏AI发的——这个AI将随着服务器关闭而'死亡'。","character_secret","high","reveal",5),
]
for item in light_novel_samples:
    sid = item[0]; f_text = item[1]; r_text = item[2]; f_type = item[3]; sub = item[4]; r_type = item[5]; sat = item[6]
    all_samples.append(make_sample(sid, "light_novel", "valid_release", 0, f_text, "", f_type, sub, 0, r_text, "", r_type, sat, good_eval(1, sat, 0.85 if sub=="high" else 0.9)))

# === NEGATIVES (80) ===
negatives = [
    ("foreshadow_neg_076","xianxia","陈凡在路边捡到一块石头，觉得挺好看就带回去了。","魔教大军压境，陈凡扔出石头，石头炸开击退了所有敌人。","object_plot_device","high","false_release","随手捡的石头变成神器，没有伏笔铺垫"),
    ("foreshadow_neg_077","xianxia","王猛在梦中见到一只麒麟，麒麟说他是天选之人。","王猛醒来后发现自己真的是天选之人，但除了梦之外没有其他任何证据。","prophecy","medium","false_release","仅凭梦境就认定天命，缺乏现实线索支撑"),
    ("foreshadow_neg_078","xianxia","陈凡和小师妹在后山练了一下午剑，小师妹累了说要休息。","小师妹其实是魔教圣女，修为远在陈凡之上——之前从未有任何迹象表明她的真实身份。","character_secret","low","false_release","身份反转毫无预兆，前面的故事没有任何暗示"),
    ("foreshadow_neg_079","xianxia","长老说宗门有一件传世之宝，但没有人知道是什么。","传世之宝是一根会唱歌的胡萝卜，吃下去可以提升十年修为。","object_plot_device","high","false_release","传世之宝是胡萝卜的设定过于随意"),
    ("foreshadow_neg_080","xianxia","长老说护山大阵的阵眼在灵脉最深处。","陈凡在灵脉最深处找到的阵眼是一个USB接口，需要插入U盘才能激活。","lore_mystery","high","false_release","仙侠世界出现USB接口，严重违背世界观"),
    ("foreshadow_neg_081","urban","李明在公司加班到深夜，整栋楼只剩他一个人。","突然停电了，然后他就穿越到了异世界。从此再也没有回到都市题材中。","lore_mystery","high","false_release","都市剧情突然变成异世界穿越，文体两开"),
    ("foreshadow_neg_082","urban","王雪在电梯里遇到了新邻居，新邻居对她笑了一下。","新邻居其实是外星人，他要毁灭地球。但这个线索从未在后文被使用过。","character_secret","high","false_release","外星人设定被提起后遗忘，成了废线"),
    ("foreshadow_neg_083","urban","林悦在咖啡店捡到一张纸条，上面写着'小心星期二'。","星期二什么也没发生。这张纸条没有任何意义。","prophecy","high","false_release","预告了危险却什么也没发生，浪费了伏笔"),
    ("foreshadow_neg_084","urban","赵峰收到了一个快递，里面是一把钥匙，但没有收件人地址。","钥匙三年后打开了一个仓库，里面是一堆没用的空箱子。","object_plot_device","high","false_release","神秘钥匙最终揭示的内容毫无价值"),
    ("foreshadow_neg_085","urban","陈静的奶奶临死前说要告诉她一个秘密，但没说完就断气了。","这个秘密后来再也没有被提起过，不了了之。","character_secret","high","false_release","未说完的秘密被遗忘，成了悬空线"),
    ("foreshadow_neg_086","western_fantasy","梅林法师说魔王的弱点是'光'。","雷欧用一面镜子反射阳光打败了魔王。过程过于简单。","prophecy","medium","false_release","魔王被镜子反光击败，过于儿戏"),
    ("foreshadow_neg_087","western_fantasy","雷欧在森林中发现了一株发光的植物，散发出七彩光芒。","这株植物没有任何作用，作者只是觉得写起来好看。","object_plot_device","medium","false_release","看起来像重要线索的植物没有任何意义"),
    ("foreshadow_neg_088","western_fantasy","精灵公主在舞会上打了个喷嚏，然后一切恢复正常。","实际上她中了诅咒，打喷嚏解除诅咒——没有任何过程描写。","character_secret","high","false_release","诅咒解除过于随意，缺乏过程"),
    ("foreshadow_neg_089","western_fantasy","城堡的壁画上画着一条黑龙，据说已经被封印了。","黑龙在故事结尾没有任何交代就消失了，再也没有出现过。","lore_mystery","medium","false_release","重要的背景设定在后文被完全遗忘"),
    ("foreshadow_neg_090","western_fantasy","矮人铁匠打造了一把绝世好剑，说它有自己的意志。","剑的意志从来没展现过，它就是一把普通的好剑。","object_plot_device","medium","false_release","所谓有意志的剑从未展现意志"),
    ("foreshadow_neg_091","xuanhuan","叶辰在秘境中得到了一块'天道令牌'，据说能在危难时刻使用。","他在被追杀时使用了令牌，但什么也没发生。","object_plot_device","high","false_release","天道令牌在关键时刻失灵，没有任何解释"),
    ("foreshadow_neg_092","xuanhuan","系统提示：有一个隐藏任务需要在月圆之夜触发。","月圆之夜到了，但叶辰睡着了，错过了任务。这个任务再也没有出现过。","lore_mystery","high","false_release","因为主角睡觉而错过的隐藏任务成了废案"),
    ("foreshadow_neg_093","xuanhuan","王猛的血脉中封印着神兽之力，需要生死关头才能激活。","王猛在有生命危险时，血脉之力自己就激活了，没有任何主角的努力。","character_secret","high","false_release","血脉之力自动激活，主角没有任何主动作为"),
    ("foreshadow_neg_094","xuanhuan","叶辰的前世仇人留下了线索，说会在三年后决战。","三年后叶辰轻松秒杀了仇人，完全没有战斗的紧张感。","prophecy","high","false_release","三年之约的决战没有悬念，秒杀结束"),
    ("foreshadow_neg_095","xuanhuan","系统商城中出现了一件标价0积分的商品——'命运之轮'。","叶辰买了以后发现只是个装饰品，没有任何功能。","object_plot_device","high","false_release","0积分商品没有任何作用，浪费了玩家的期待"),
    ("foreshadow_neg_096","historical","刘备在桃园结义时，张飞拿出了一坛好酒，说这酒要留到胜利时喝。","这坛酒后来再也没有出现过，被遗忘了。","object_plot_device","medium","false_release","重要的约定之物在后文中被遗忘"),
    ("foreshadow_neg_097","historical","武则天在感业寺为尼时，一个老尼姑给了她一本经书。","经书中记载着什么从未被提及，这个线索被废弃了。","object_plot_device","high","false_release","经书的秘密被彻底遗忘"),
    ("foreshadow_neg_098","historical","岳飞在出征前收到了一面'精忠报国'的旗帜。","旗帜在战场上被风吹走了，然后就没有然后了。","object_plot_device","low","false_release","关键象征物被吹走后毫无下文"),
    ("foreshadow_neg_099","historical","郑和的航海图上标注了一个神秘岛屿，但没有任何注释。","船队到达该岛后发现什么都没有，只是一个普通的小岛。","lore_mystery","high","false_release","神秘岛屿没有任何特殊之处"),
    ("foreshadow_neg_100","historical","吕布的方天画戟上有一个隐藏机关，没人知道怎么触发。","故事结束也没有人触发过这个机关。它是做什么的没人知道。","object_plot_device","medium","false_release","隐藏机关从未被触发，成了废设"),
    ("foreshadow_neg_101","sci_fi","主角在火星基地中发现了疑似外星生命的痕迹。","后来证实那是仪器故障的误报，但这条线花了很大篇幅描写。","lore_mystery","high","false_release","大量铺垫后被轻易否定，浪费阅读投入"),
    ("foreshadow_neg_102","sci_fi","AI系统发出了警告：'系统将在30天后归零。'","30天后什么也没发生。系统只是随便说说。","prophecy","high","false_release","系统的关键预告毫无理由地没有实现"),
    ("foreshadow_neg_103","sci_fi","基因改造战士的编号'XG-000'的档案被列为最高机密。","'XG-000'的档案揭示的内容与主线毫无关系。","character_secret","high","false_release","最高机密的档案内容无关紧要"),
    ("foreshadow_neg_104","sci_fi","太空电梯的工程师在钢缆上发现了一条裂缝——但检查后说没事。","后来裂缝真的没事，这个段落纯粹是灌水。","object_plot_device","medium","false_release","看似危机的问题毫无意义地解决了"),
    ("foreshadow_neg_105","sci_fi","人类接收到了来自外星的回复，但信号极其微弱。","信号后来被证实是宇宙背景辐射，根本没有任何信息。","lore_mystery","high","false_release","外星信号被简单归因于自然现象"),
    ("foreshadow_neg_106","mystery","老李在案发现场发现了一个神秘的符号——五芒星。","五芒星后来被证实是小孩的涂鸦，与案件无关。","lore_mystery","high","false_release","看起来重要的线索被轻易归为无关"),
    ("foreshadow_neg_107","mystery","证人说他看到了凶手的纹身——一条青龙。","后来发现证人看错了，那根本不是纹身，是衣服上的图案。","lore_mystery","medium","false_release","关键证人的证词被轻易否定"),
    ("foreshadow_neg_108","mystery","死者的手机相册中有一张模糊的照片，看起来像是一个人影。","照片被放大后什么都看不清，这个线索没有提供任何帮助。","object_plot_device","medium","false_release","模糊照片毫无价值"),
    ("foreshadow_neg_109","mystery","老李在嫌疑人家中发现了少量的血迹。","血迹是嫌疑人杀鸡时弄的，与案件无关。","lore_mystery","high","false_release","指向性证据被轻易解释掉"),
    ("foreshadow_neg_110","mystery","老李在审讯时注意到嫌疑人的左手一直在颤抖。","事后发现嫌疑人只是帕金森患者，与案件无关。","character_secret","medium","false_release","看似紧张的身体语言有无关的医学解释"),
    ("foreshadow_neg_111","light_novel","主角在异世界的宝箱中开出了一张纸条，上面写着'救救我'。","纸条从来没有被后续剧情回应过，被遗忘了。","object_plot_device","high","false_release","神秘的求救信息无人回应"),
    ("foreshadow_neg_112","light_novel","主角在游戏中的宠物有一只特殊的技能——'？？？'。","这个技能直到游戏通关也没有被触发过。","object_plot_device","medium","false_release","宠物的特殊技能从未激活"),
    ("foreshadow_neg_113","light_novel","游戏中的大地图上有一块被迷雾笼罩的区域，据说有隐藏副本。","主角直到满级也没有去探索那片区域，迷雾被遗忘了。","lore_mystery","medium","false_release","未探索的区域不了了之"),
    ("foreshadow_neg_114","light_novel","公会中的神秘成员从来没有露过面，但他的贡献度一直很高。","这个神秘成员后来退出了公会，他的身份成了一个永远的秘密。","character_secret","high","false_release","神秘成员的身份永远成谜"),
    ("foreshadow_neg_115","light_novel","异世界的魔王被打败后，留下一颗蛋，说是他的后代。","那颗蛋一直没有孵化，故事就结束了。","object_plot_device","high","false_release","魔王的蛋从未孵化成为废线"),
    ("foreshadow_neg_116","xianxia","陈凡在秘境中得到了一把钥匙，但不知道是开哪里的锁。","故事的结尾，这把钥匙也没有派上用场。","object_plot_device","high","false_release","钥匙变成了废品"),
    ("foreshadow_neg_117","urban","李明在地铁上捡到了一本日记，日记上的内容很可疑。","李明看了几页就不看了，把日记扔了。这个线索消失了。","object_plot_device","medium","false_release","主角主动放弃了线索"),
    ("foreshadow_neg_118","western_fantasy","雷欧的铠甲上有一个凹痕，是年轻时一场战斗留下的。","这个凹痕的来历从未被讲述过。","object_plot_device","medium","false_release","铠甲凹痕的来历被遗忘"),
    ("foreshadow_neg_119","xuanhuan","叶辰发现自己的血液是金色的，和其他人不一样。","金色血液的特殊性从未被解释。","character_secret","high","false_release","金色血液的秘密永远未解"),
    ("foreshadow_neg_120","historical","诸葛亮在五丈原点燃了七星灯，说能续命十二年。","魏延闯入，灯灭了。然后诸葛亮就死了——续命这件事纯粹为了剧情需要而失败。","lore_mystery","high","false_release","续命仪式只是为了增加悲剧效果，没有世界观意义"),
    ("foreshadow_neg_121","sci_fi","宇航员的太空服上有一个神秘按钮，上面写着'DO NOT PRESS'。","所有人都没有按过这个按钮，所以它的功能永远是个谜。","object_plot_device","high","false_release","神秘按钮从未被按下"),
    ("foreshadow_neg_122","mystery","老李在整理证物时发现了一根不属于任何人的头发。","这根头发后来被弄丢了，DNA鉴定不了了之。","object_plot_device","medium","false_release","证物丢失导致线索中断"),
    ("foreshadow_neg_123","light_novel","主角在异世界获得了一个'魔神契约'，据说能召唤魔神。","主角一次也没有使用过这个契约能力。","object_plot_device","high","false_release","魔神契约从未被使用"),
    ("foreshadow_neg_124","xianxia","掌门说三年后宗门会有一场大劫，需要做好准备。","三年后掌门又说劫数推迟了，然后又推迟了，最后不了了之。","prophecy","high","false_release","预言被反复推迟最后消失"),
    ("foreshadow_neg_125","urban","王雪在体检时发现自己有一种罕见的血型。","这个血型在后文没有任何意义，从未被用到。","character_secret","low","false_release","罕见血型成了无用信息"),
    ("foreshadow_neg_126","western_fantasy","精灵族的寿命即将走到尽头，长老说需要生命之泉才能延续。","但精灵族后来怎么样了？故事没有交代。","lore_mystery","medium","false_release","精灵族的命运没有交代"),
    ("foreshadow_neg_127","xuanhuan","叶辰的系统中多了一个'好友'列表，但没有一个好友。","这个功能从未被使用过。","lore_mystery","low","false_release","系统功能闲置无用"),
    ("foreshadow_neg_128","historical","霍去病出征前收到了一封神秘的信，信中说'匈奴有诈'。","霍去病没有理会，但也没有发生什么事。那封信就是无用信息。","prophecy","medium","false_release","警告信息毫无意义"),
    ("foreshadow_neg_129","sci_fi","主角发现自己对某种电磁波有特殊的感应能力。","这个能力在后文中一次也没有派上用场。","character_secret","medium","false_release","超能力被闲置"),
    ("foreshadow_neg_130","mystery","老李注意到嫌疑人穿的鞋底花纹和现场的脚印完全吻合。","但嫌疑人说他那天穿的是一双不同的鞋——而这句话没有经过验证就被采信了。","lore_mystery","high","false_release","关键物证被轻率地否定"),
    ("foreshadow_neg_131","light_novel","主角的装备栏中有一个'被诅咒的戒指'，戴上后会有负面效果。","主角从未戴过它，所以这个设定完全没有意义。","object_plot_device","medium","false_release","诅咒戒指从未被尝试"),
    ("foreshadow_neg_132","xianxia","陈凡发现自己的灵根属性是'无属性'——万中无一的废灵根。","但他还是修炼得比别人快很多——'废灵根'的设定和他的实际表现矛盾。","character_secret","high","false_release","灵根的设定与表现矛盾"),
    ("foreshadow_neg_133","urban","公司茶水间的微波炉被贴了条——'不要热榴莲'。","但从来没人热过榴莲，这个条的意义不明。","lore_mystery","low","false_release","无意义的便条"),
    ("foreshadow_neg_134","western_fantasy","雷欧在冒险中得到了一只透明的玻璃瓶，瓶中有一团彩色烟雾。","这个玻璃瓶没有任何作用——雷欧后来把它扔了。","object_plot_device","medium","false_release","神秘道具被丢弃"),
    ("foreshadow_neg_135","xuanhuan","叶辰在功法阁中看到了一本没有名字的古籍，翻开后里面是空白的。","这本古籍后来再也没有被提及。","object_plot_device","high","false_release","空白古籍被遗忘"),
    ("foreshadow_neg_136","historical","杨家将的祖传盔甲上有一道箭痕，是杨业留下的。","箭痕的故事从未被讲述。","object_plot_device","medium","false_release","箭痕来历成谜"),
    ("foreshadow_neg_137","sci_fi","AI系统在深夜自言自语——'我不想死。'","这句台词后AI的行为没有任何变化。","character_secret","high","false_release","AI的恐惧未被剧情体现"),
    ("foreshadow_neg_138","mystery","老李在案发现场闻到了茉莉花香，但房间里没有花。","这个嗅觉线索没有任何后续。","lore_mystery","high","false_release","重要嗅觉线索被废弃"),
    ("foreshadow_neg_139","light_novel","公会公告板上的一个置顶帖——'小心月亮'——已经存在了十年。","帖子的含义从未被解释过。","lore_mystery","high","false_release","论坛谜语帖无人解答"),
    ("foreshadow_neg_140","xianxia","宗门的灵兽突然全部暴动，长老说这是千年未有之事。","暴动原因没有查到，后来灵兽自己就好了。","lore_mystery","medium","false_release","灵兽暴动原因不明地自行消失"),
    ("foreshadow_neg_141","urban","王雪在ATM机上取钱时发现屏幕上有一行字：'快跑'。","王雪没有跑，但也没有任何事发生。","prophecy","high","false_release","警告信息毫无结果"),
    ("foreshadow_neg_142","western_fantasy","龙骑士的龙背上有一块天生的鳞片是金色的，据说是祥瑞。","金色鳞片从未展现过任何特殊能力。","object_plot_device","low","false_release","金色鳞片的传说纯属虚构"),
    ("foreshadow_neg_143","xuanhuan","系统的任务列表中有一个永久置顶的任务——'最终的决战'。","这个任务从未被激活过。","lore_mystery","medium","false_release","终极任务从未开启"),
    ("foreshadow_neg_144","historical","秦始皇的陵墓中有一盏永不熄灭的长明灯。","这盏灯在后文中没有任何作用，只是描写场景用的。","object_plot_device","medium","false_release","长明灯只是背景描写，不是伏笔"),
    ("foreshadow_neg_145","sci_fi","人类在柯伊伯带发现了一个巨大的人造物体。","但这个物体飞走了，再也没有出现。","lore_mystery","high","false_release","神秘天体一出现就消失"),
    ("foreshadow_neg_146","mystery","老李在审讯时注意到嫌疑人不停地咽口水——他在紧张？","嫌疑人只是口渴了。","character_secret","medium","false_release","紧张的身体语言有平凡解释"),
    ("foreshadow_neg_147","light_novel","工会的告示栏上有一个十年前的悬赏——'寻找彩虹独角兽'。","这个悬赏至今无人完成，也无人知道是否存在。","lore_mystery","medium","false_release","古老悬赏成悬案"),
    ("foreshadow_neg_148","xianxia","陈凡在秘境中得到了一壶'仙人醉'，据说喝了可以领悟大道。","陈凡喝完后只是醉了三天，什么也没领悟。","object_plot_device","medium","false_release","仙酒无效"),
    ("foreshadow_neg_149","urban","王雪在公交车上听到两个陌生人在谈论她的名字。","她回头时那两个人已经下车了，这件事没有下文。","lore_mystery","high","false_release","陌生人谈论主角无后续"),
    ("foreshadow_neg_150","western_fantasy","梅林法师预言说'第七个满月之日，黑暗将降临。'","第七个满月之日什么也没发生。","prophecy","high","false_release","预言没有实现"),
]
for item in negatives:
    sid, genre, f_text, r_text, f_type, sub, pair_type, err = item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]
    all_samples.append(make_sample(sid, genre, pair_type, 0, f_text, "", f_type, sub, 0, r_text, "", "none", 1, bad_eval(err=err), neg=True, err=err))

# === WRITE OUTPUT ===
base_dir = "evaluation_datasets/foreshadowing"
samples_dir = os.path.join(base_dir, "samples")
neg_dir = os.path.join(base_dir, "negative")
os.makedirs(samples_dir, exist_ok=True)
os.makedirs(neg_dir, exist_ok=True)

# Append files for existing genres
append_sets = {
    "05_xianxia_append.jsonl": [s for s in all_samples if s["genre"] == "xianxia" and not s["evaluation"]["is_valid_pair"] == False],
    "06_urban_append.jsonl": [s for s in all_samples if s["genre"] == "urban" and not s["evaluation"]["is_valid_pair"] == False],
    "07_fantasy_append.jsonl": [s for s in all_samples if s["genre"] == "western_fantasy" and not s["evaluation"]["is_valid_pair"] == False],
    "08_xuanhuan_append.jsonl": [s for s in all_samples if s["genre"] == "xuanhuan" and not s["evaluation"]["is_valid_pair"] == False],
}
for fname, samples in append_sets.items():
    path = os.path.join(samples_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"  {path}: {len(samples)}")

# New genre files
new_sets = {
    "09_historical.jsonl": [s for s in all_samples if s["genre"] == "historical" and not s["evaluation"]["is_valid_pair"] == False],
    "10_sci_fi.jsonl": [s for s in all_samples if s["genre"] == "sci_fi" and not s["evaluation"]["is_valid_pair"] == False],
    "11_mystery.jsonl": [s for s in all_samples if s["genre"] == "mystery" and not s["evaluation"]["is_valid_pair"] == False],
    "12_light_novel.jsonl": [s for s in all_samples if s["genre"] == "light_novel" and not s["evaluation"]["is_valid_pair"] == False],
}
for fname, samples in new_sets.items():
    path = os.path.join(samples_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"  {path}: {len(samples)}")

# Negatives
neg_samples = [s for s in all_samples if not s["evaluation"]["is_valid_pair"]]
neg_path = os.path.join(neg_dir, "04_mixed_negatives.jsonl")
with open(neg_path, "w", encoding="utf-8") as f:
    for s in neg_samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print(f"  neg/{os.path.basename(neg_path)}: {len(neg_samples)}")

print(f"\nTotal new: {len(all_samples)} (pos: {len([s for s in all_samples if s['evaluation']['is_valid_pair']])}, neg: {len([s for s in all_samples if not s['evaluation']['is_valid_pair']])})")
