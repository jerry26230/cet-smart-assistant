package com.jerry26230.cetsmartassistant

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.jerry26230.cetsmartassistant.data.DailyActivity
import com.jerry26230.cetsmartassistant.data.DeckProgress
import com.jerry26230.cetsmartassistant.data.ReviewGrade
import com.jerry26230.cetsmartassistant.data.StudyDatabase
import com.jerry26230.cetsmartassistant.data.StudyWord
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalDate
import java.time.format.DateTimeFormatter

private val Canvas = Color(0xFFF4F6F2)
private val Ink = Color(0xFF17372F)
private val Leaf = Color(0xFF14745F)
private val Lime = Color(0xFFDDF27A)
private val Mint = Color(0xFFE4F3EC)
private val Muted = Color(0xFF71827B)
private val Border = Color(0xFFE2E9E3)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = android.graphics.Color.rgb(244, 246, 242)
        window.navigationBarColor = android.graphics.Color.rgb(244, 246, 242)
        window.decorView.systemUiVisibility = android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR or
            android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
        val database = StudyDatabase(applicationContext)
        setContent { CETApp(database) }
    }
}

private enum class Page(val label: String, val mark: String) {
    HOME("今天", "⌂"), VOCAB("词库", "Aa"), PROGRESS("进度", "◷"), SETTINGS("计划", "⚙")
}

@Composable
private fun CETApp(database: StudyDatabase) {
    val scope = rememberCoroutineScope()
    var ready by remember { mutableStateOf(false) }
    var loadError by remember { mutableStateOf("") }
    var page by remember { mutableStateOf(Page.HOME) }
    var decks by remember { mutableStateOf(emptyList<DeckProgress>()) }
    var activity by remember { mutableStateOf(emptyList<DailyActivity>()) }
    var examDate by remember { mutableStateOf("") }
    var dailyMinutes by remember { mutableIntStateOf(120) }
    var focus by remember { mutableStateOf("balanced") }
    var studyQueue by remember { mutableStateOf(emptyList<StudyWord>()) }
    var reviewCount by remember { mutableIntStateOf(0) }
    var reviewActive by remember { mutableStateOf(false) }
    var currentDeck by remember { mutableStateOf("cet6") }
    var searchTerm by remember { mutableStateOf("") }
    var searchResults by remember { mutableStateOf(emptyList<StudyWord>()) }
    var savingMessage by remember { mutableStateOf("") }

    suspend fun refreshData() {
        val snapshot = withContext(Dispatchers.IO) {
            Triple(database.deckProgress(), database.activity(), database.setting("exam_date"))
        }
        decks = snapshot.first
        activity = snapshot.second
        examDate = snapshot.third
        dailyMinutes = withContext(Dispatchers.IO) { database.setting("daily_minutes", "120").toIntOrNull() ?: 120 }
        focus = withContext(Dispatchers.IO) { database.setting("study_focus", "balanced") }
    }

    LaunchedEffect(Unit) {
        try {
            withContext(Dispatchers.IO) { database.importBuiltInVocabulary() }
            refreshData()
            ready = true
        } catch (error: Exception) {
            loadError = error.localizedMessage ?: "词库初始化失败"
        }
    }

    val colors = lightColorScheme(
        primary = Leaf,
        onPrimary = Color.White,
        secondary = Lime,
        background = Canvas,
        surface = Color.White,
        onBackground = Ink,
        onSurface = Ink
    )

    MaterialTheme(colorScheme = colors) {
        if (!ready) {
            Box(Modifier.fillMaxSize().background(Canvas), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    if (loadError.isEmpty()) CircularProgressIndicator(color = Leaf)
                    Spacer(Modifier.height(18.dp))
                    Text(if (loadError.isEmpty()) "正在为你准备离线词库…" else "词库没能载入", color = Ink, fontSize = 18.sp)
                    if (loadError.isNotEmpty()) Text(loadError, Modifier.padding(20.dp), color = Muted)
                }
            }
            return@MaterialTheme
        }

        val isReview = reviewActive
        Scaffold(
            containerColor = Canvas,
            bottomBar = {
                if (!isReview) {
                    NavigationBar(containerColor = Color.White, tonalElevation = 0.dp) {
                        Page.entries.forEach { destination ->
                            NavigationBarItem(
                                selected = page == destination,
                                onClick = { page = destination },
                                icon = { Text(destination.mark, fontSize = if (destination.mark == "Aa") 15.sp else 21.sp, fontWeight = FontWeight.SemiBold) },
                                label = { Text(destination.label) }
                            )
                        }
                    }
                }
            }
        ) { padding ->
            Box(Modifier.fillMaxSize().padding(padding)) {
                if (isReview) {
                    val current = studyQueue.firstOrNull()
                    ReviewScreen(
                        word = current,
                        total = reviewCount,
                        completed = (reviewCount - studyQueue.size).coerceAtLeast(0),
                        onExit = { studyQueue = emptyList(); reviewCount = 0; reviewActive = false; scope.launch { refreshData() } },
                        onAnswer = { grade ->
                            if (current != null) scope.launch {
                                withContext(Dispatchers.IO) { database.recordAnswer(current, grade) }
                                studyQueue = studyQueue.drop(1)
                                refreshData()
                            }
                        }
                    )
                } else when (page) {
                    Page.HOME -> HomeScreen(
                        decks = decks,
                        examDate = examDate,
                        dailyMinutes = dailyMinutes,
                        focus = focus,
                        onStart = { page = Page.VOCAB },
                        onSetup = { page = Page.SETTINGS }
                    )
                    Page.VOCAB -> VocabularyScreen(
                        decks = decks,
                        query = searchTerm,
                        results = searchResults,
                        onQuery = { value ->
                            searchTerm = value
                            if (value.isBlank()) searchResults = emptyList()
                            else scope.launch {
                                val matches = withContext(Dispatchers.IO) { database.searchWords(currentDeck, value) }
                                if (searchTerm == value) searchResults = matches
                            }
                        },
                        selectedDeck = currentDeck,
                        onDeck = { currentDeck = it; searchResults = emptyList() },
                        onStudy = { key ->
                            currentDeck = key
                            scope.launch {
                                val queue = withContext(Dispatchers.IO) { database.studySession(key) }
                                studyQueue = queue
                                reviewCount = queue.size
                                reviewActive = true
                            }
                        }
                    )
                    Page.PROGRESS -> ProgressScreen(decks, activity)
                    Page.SETTINGS -> SettingsScreen(
                        examDate = examDate,
                        dailyMinutes = dailyMinutes,
                        focus = focus,
                        savedMessage = savingMessage,
                        onSave = { date, minutes, selectedFocus ->
                            val parsed = runCatching { LocalDate.parse(date) }.getOrNull()
                            if (date.isNotBlank() && parsed == null) {
                                savingMessage = "日期请按 YYYY-MM-DD 填写，例如 2026-12-12。"
                            } else if (minutes !in 10..720) {
                                savingMessage = "每日学习时间请设置为 10～720 分钟。"
                            } else {
                                scope.launch {
                                    withContext(Dispatchers.IO) {
                                        database.saveSetting("exam_date", date)
                                        database.saveSetting("daily_minutes", minutes.toString())
                                        database.saveSetting("study_focus", selectedFocus)
                                    }
                                    refreshData()
                                    savingMessage = "已保存到本机"
                                }
                            }
                        }
                    )
                }
            }
        }
    }
}

@Composable
private fun HomeScreen(
    decks: List<DeckProgress>, examDate: String, dailyMinutes: Int, focus: String,
    onStart: () -> Unit, onSetup: () -> Unit
) {
    val remainingDays = runCatching { java.time.temporal.ChronoUnit.DAYS.between(LocalDate.now(), LocalDate.parse(examDate)).toInt() }.getOrNull()
    val plan = makePlan(dailyMinutes, focus)
    PageContent {
        TopHeading("CET 智能备考", "把今天学好，离目标更近一点")
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(30.dp),
            colors = CardDefaults.cardColors(containerColor = Ink)
        ) {
            Column(Modifier.padding(24.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(42.dp).background(Lime, CircleShape), contentAlignment = Alignment.Center) {
                        Text("✦", color = Ink, fontSize = 22.sp)
                    }
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Text("本次备考", color = Color.White.copy(alpha = .68f), fontSize = 13.sp)
                        Text(
                            when {
                                remainingDays == null -> "先设定你的考试日期"
                                remainingDays < 0 -> "这场考试已结束"
                                remainingDays == 0 -> "今天考试，稳住节奏"
                                else -> "距离考试还有 $remainingDays 天"
                            },
                            color = Color.White, fontSize = 21.sp, fontWeight = FontWeight.Bold
                        )
                    }
                }
                Spacer(Modifier.height(24.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Bottom) {
                    Column {
                        Text("今日学习安排", color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.SemiBold)
                        Text("每天约 $dailyMinutes 分钟 · 本机离线保存", color = Color.White.copy(alpha = .62f), fontSize = 12.sp)
                    }
                    TextButton(onClick = onSetup) { Text("调整计划  ↗", color = Lime) }
                }
                Spacer(Modifier.height(16.dp))
                plan.forEachIndexed { index, (label, minutes) ->
                    Row(Modifier.fillMaxWidth().padding(vertical = 7.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text(label, Modifier.weight(1f), color = Color.White.copy(alpha = .84f), fontSize = 14.sp)
                        Box(Modifier.width(100.dp).height(6.dp).background(Color.White.copy(alpha = .16f), CircleShape)) {
                            Box(Modifier.fillMaxWidth((minutes.toFloat() / dailyMinutes.coerceAtLeast(1)).coerceIn(.02f, 1f)).height(6.dp).background(if (index == 0) Lime else Color(0xFF8DD7BE), CircleShape))
                        }
                        Text("$minutes 分", Modifier.width(58.dp), color = Color.White, textAlign = TextAlign.End, fontSize = 13.sp)
                    }
                }
                Spacer(Modifier.height(14.dp))
                Button(
                    onClick = onStart,
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                    shape = RoundedCornerShape(17.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Lime, contentColor = Ink)
                ) { Text("开始今日学习", fontWeight = FontWeight.Bold, fontSize = 16.sp) }
            }
        }

        SectionTitle("词汇进度", "总未学习量和今日额度分开显示")
        val chosen = decks.firstOrNull { it.deck.key == "cet6" }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MetricCard("已学词汇", (decks.sumOf { it.learned }).toString(), "三套词库合计", Modifier.weight(1f), Mint)
            MetricCard("今日新词", chosen?.let { "${(20 - it.newToday).coerceAtLeast(0)} / 20" } ?: "0 / 20", "六级词汇", Modifier.weight(1f), Color(0xFFFFF1D8))
        }
        Spacer(Modifier.height(12.dp))
        Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(22.dp)) {
            Row(Modifier.fillMaxWidth().padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("六级词库还有 ${chosen?.unlearned ?: 0} 个未学习词", fontWeight = FontWeight.SemiBold, color = Ink)
                    Text("未学习总量不会被每日 20 个新词上限替代", color = Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 5.dp))
                }
                Text("→", color = Leaf, fontSize = 24.sp)
            }
        }

        SectionTitle("今日建议", "先做一小步，再慢慢建立节奏")
        Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(22.dp)) {
            Column(Modifier.padding(18.dp)) {
                Text("✦ 词汇与语境", color = Leaf, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(7.dp))
                Text("新词按每天 20 个安排；复习词根据上次记忆反馈排期。阅读、写作与听力保留基础时间。", color = Ink, fontSize = 14.sp, lineHeight = 21.sp)
                TextButton(onClick = onStart, modifier = Modifier.align(Alignment.End)) { Text("选择词库学习  →", color = Leaf) }
            }
        }
        Spacer(Modifier.height(18.dp))
    }
}

@Composable
private fun VocabularyScreen(
    decks: List<DeckProgress>, query: String, results: List<StudyWord>, selectedDeck: String,
    onQuery: (String) -> Unit, onDeck: (String) -> Unit, onStudy: (String) -> Unit
) {
    PageContent {
        TopHeading("词汇学习", "四级、六级和雅思词库都已内置")
        decks.forEach { progress ->
            Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(24.dp), modifier = Modifier.padding(bottom = 12.dp)) {
                Column(Modifier.fillMaxWidth().padding(18.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(progress.deck.title, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                            Text(progress.deck.subtitle, color = Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 3.dp))
                        }
                        Box(Modifier.background(Mint, RoundedCornerShape(30.dp)).padding(horizontal = 12.dp, vertical = 7.dp)) {
                            Text("${progress.due} 待复习", color = Leaf, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }
                    Spacer(Modifier.height(16.dp))
                    LinearProgressIndicator(
                        progress = { if (progress.total == 0) 0f else progress.learned.toFloat() / progress.total },
                        modifier = Modifier.fillMaxWidth().height(8.dp),
                        color = Leaf,
                        trackColor = Border
                    )
                    Spacer(Modifier.height(12.dp))
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        SmallStat("已学", "${progress.learned}")
                        SmallStat("总未学", "${progress.unlearned}")
                        SmallStat("今日新词", "${(20 - progress.newToday).coerceAtLeast(0)} / 20")
                    }
                    Spacer(Modifier.height(14.dp))
                    Button(
                        onClick = { onStudy(progress.deck.key) },
                        modifier = Modifier.fillMaxWidth().height(48.dp),
                        shape = RoundedCornerShape(15.dp)
                    ) { Text(if (progress.due == 0 && progress.unlearned == 0) "今天已完成" else "开始学习 · 复习优先") }
                }
            }
        }
        SectionTitle("查词", "只在当前词库中搜索")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            decks.forEach { item ->
                val active = selectedDeck == item.deck.key
                Surface(
                    color = if (active) Ink else Color.White,
                    shape = RoundedCornerShape(30.dp),
                    modifier = Modifier.clickable { onDeck(item.deck.key) }
                ) { Text(item.deck.title, Modifier.padding(horizontal = 14.dp, vertical = 9.dp), color = if (active) Color.White else Muted, fontSize = 12.sp) }
            }
        }
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(query, onQuery, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("输入英文单词或中文释义") }, shape = RoundedCornerShape(16.dp))
        results.take(20).forEach { word ->
            Column(Modifier.fillMaxWidth().padding(vertical = 10.dp)) {
                Text(word.word + if (word.phonetic.isNotBlank()) "  ${word.phonetic}" else "", fontWeight = FontWeight.Bold, color = Ink)
                Text(word.meaning, color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 4.dp))
            }
        }
        Spacer(Modifier.height(18.dp))
    }
}

@Composable
private fun ReviewScreen(
    word: StudyWord?, total: Int, completed: Int, onExit: () -> Unit, onAnswer: (ReviewGrade) -> Unit
) {
    var revealed by remember(word?.deck, word?.word) { mutableStateOf(false) }
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
    Column(Modifier.widthIn(max = 760.dp).fillMaxWidth().fillMaxHeight().padding(horizontal = 24.dp, vertical = 18.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onExit) { Text("‹ 退出学习", color = Leaf) }
            Spacer(Modifier.weight(1f))
            Text("${completed.coerceAtMost(total)} / $total", color = Muted, fontSize = 13.sp)
        }
        LinearProgressIndicator(progress = { if (total == 0) 1f else completed.toFloat() / total }, modifier = Modifier.fillMaxWidth().height(6.dp), color = Leaf, trackColor = Border)
        Spacer(Modifier.weight(1f))
        if (word == null) {
            Box(Modifier.fillMaxWidth().weight(2f), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("✦", color = Leaf, fontSize = 48.sp)
                    Spacer(Modifier.height(12.dp))
                    Text(if (total == 0) "今天的卡片学完啦" else "这一组完成了", color = Ink, fontSize = 24.sp, fontWeight = FontWeight.Bold)
                    Text("复习会在到期时重新出现，学习进度保存在本机。", color = Muted, modifier = Modifier.padding(top = 8.dp), textAlign = TextAlign.Center)
                    Spacer(Modifier.height(22.dp))
                    Button(onClick = onExit) { Text("返回词库") }
                }
            }
        } else {
            Card(
                modifier = Modifier.fillMaxWidth().weight(2f).clickable { revealed = !revealed },
                shape = RoundedCornerShape(32.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Box(Modifier.fillMaxSize().padding(26.dp), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(if (word.isNew) "今日新词" else "到期复习", color = Leaf, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        Spacer(Modifier.height(28.dp))
                        Text(word.word, fontSize = 38.sp, fontWeight = FontWeight.Bold, color = Ink, textAlign = TextAlign.Center)
                        if (word.phonetic.isNotBlank()) Text(word.phonetic, color = Muted, fontSize = 15.sp, modifier = Modifier.padding(top = 8.dp))
                        Spacer(Modifier.height(30.dp))
                        if (revealed) Text(word.meaning, color = Ink, fontSize = 17.sp, lineHeight = 26.sp, textAlign = TextAlign.Center)
                        else Text("先回忆含义，再轻触卡片", color = Muted, fontSize = 14.sp)
                    }
                }
            }
            Spacer(Modifier.height(20.dp))
            if (revealed) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    GradeButton("忘了", Color(0xFFFFE8E2), Color(0xFF9E412D), Modifier.weight(1f)) { onAnswer(ReviewGrade.AGAIN) }
                    GradeButton("有点难", Color(0xFFFFF1D8), Color(0xFF805A1F), Modifier.weight(1f)) { onAnswer(ReviewGrade.HARD) }
                    GradeButton("记住了", Mint, Leaf, Modifier.weight(1f)) { onAnswer(ReviewGrade.GOOD) }
                    GradeButton("很熟", Ink, Color.White, Modifier.weight(1f)) { onAnswer(ReviewGrade.EASY) }
                }
            } else {
                OutlinedButton(onClick = { revealed = true }, modifier = Modifier.fillMaxWidth().height(52.dp), shape = RoundedCornerShape(16.dp)) { Text("显示释义") }
            }
        }
        Spacer(Modifier.weight(1f))
    }
    }
}

@Composable
private fun ProgressScreen(decks: List<DeckProgress>, activity: List<DailyActivity>) {
    PageContent {
        TopHeading("学习进度", "数据只保存在这台设备上")
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MetricCard("累计学习", decks.sumOf { it.learned }.toString(), "个词", Modifier.weight(1f), Mint)
            MetricCard("到期复习", decks.sumOf { it.due }.toString(), "张卡片", Modifier.weight(1f), Color(0xFFFFF1D8))
        }
        SectionTitle("最近 7 天", "每天记录复习次数和首次学习词数")
        Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(24.dp)) {
            Column(Modifier.fillMaxWidth().padding(18.dp)) {
                activity.forEach { day ->
                    val date = runCatching { LocalDate.parse(day.day).format(DateTimeFormatter.ofPattern("MM/dd")) }.getOrDefault(day.day)
                    Row(Modifier.fillMaxWidth().padding(vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text(date, Modifier.width(55.dp), color = Muted, fontSize = 13.sp)
                        Box(Modifier.weight(1f).height(9.dp).background(Canvas, CircleShape)) {
                            Box(Modifier.fillMaxWidth((day.reviews / 60f).coerceIn(0f, 1f)).height(9.dp).background(Leaf, CircleShape))
                        }
                        Text("${day.reviews} 次", Modifier.width(56.dp), textAlign = TextAlign.End, color = Ink, fontSize = 13.sp)
                        Text("+${day.newWords}", Modifier.width(46.dp), textAlign = TextAlign.End, color = Leaf, fontSize = 12.sp)
                    }
                }
                Text("浅色条：当天复习量；绿色数字：首次学习词数。", color = Muted, fontSize = 11.sp, modifier = Modifier.padding(top = 5.dp))
            }
        }
        SectionTitle("词库完成情况", "已学指至少记录过一次自评")
        decks.forEach { item ->
            Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(20.dp), modifier = Modifier.padding(bottom = 10.dp)) {
                Row(Modifier.fillMaxWidth().padding(17.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(item.deck.title, fontWeight = FontWeight.Bold)
                        Text("${item.learned} / ${item.total} 已学 · ${item.due} 待复习", color = Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 4.dp))
                    }
                    Text(if (item.total == 0) "0%" else "${item.learned * 100 / item.total}%", color = Leaf, fontWeight = FontWeight.Bold, fontSize = 19.sp)
                }
            }
        }
        Spacer(Modifier.height(18.dp))
    }
}

@Composable
private fun SettingsScreen(
    examDate: String, dailyMinutes: Int, focus: String, savedMessage: String,
    onSave: (String, Int, String) -> Unit
) {
    var date by remember(examDate) { mutableStateOf(examDate) }
    var minutes by remember(dailyMinutes) { mutableStateOf(dailyMinutes.toString()) }
    var selectedFocus by remember(focus) { mutableStateOf(focus) }
    PageContent {
        TopHeading("备考计划", "按你的考试日期和每日时间安排")
        Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(26.dp)) {
            Column(Modifier.fillMaxWidth().padding(20.dp)) {
                Text("考试日期", fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = date,
                    onValueChange = { date = it },
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                    label = { Text("YYYY-MM-DD") },
                    placeholder = { Text("例如 2026-12-12") },
                    singleLine = true,
                    shape = RoundedCornerShape(15.dp)
                )
                Text("留空表示暂不设置倒计时。考试日期每年以官方通知为准。", color = Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 7.dp))
                Spacer(Modifier.height(20.dp))
                Text("每天可以学习多久？", fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = minutes,
                    onValueChange = { minutes = it.filter(Char::isDigit).take(3) },
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                    label = { Text("分钟（10–720）") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    shape = RoundedCornerShape(15.dp)
                )
                Spacer(Modifier.height(20.dp))
                Text("学习重点", fontWeight = FontWeight.Bold)
                listOf("balanced" to "均衡覆盖", "listening" to "听力", "reading" to "阅读", "writing" to "写作与翻译").forEach { (key, label) ->
                    Row(
                        Modifier.fillMaxWidth().padding(top = 8.dp).background(if (selectedFocus == key) Mint else Canvas, RoundedCornerShape(14.dp)).clickable { selectedFocus = key }.padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(if (selectedFocus == key) "●" else "○", color = Leaf)
                        Text(label, Modifier.padding(start = 10.dp), color = Ink)
                    }
                }
                Spacer(Modifier.height(18.dp))
                Button(onClick = { onSave(date.trim(), minutes.toIntOrNull() ?: 0, selectedFocus) }, modifier = Modifier.fillMaxWidth().height(50.dp), shape = RoundedCornerShape(16.dp)) {
                    Text("保存计划")
                }
                if (savedMessage.isNotBlank()) Text(savedMessage, color = Leaf, fontSize = 13.sp, modifier = Modifier.padding(top = 10.dp))
            }
        }
        SectionTitle("时间分配逻辑", "避免拿不同专项的绝对分数直接比较")
        Card(colors = CardDefaults.cardColors(containerColor = Mint), shape = RoundedCornerShape(22.dp)) {
            Text("词汇固定保留 20% 基础时间，其余时间覆盖听力、阅读和写作翻译。选择重点后，把机动时间更多分给该专项；每日总分钟数保持不变。", Modifier.padding(18.dp), color = Ink, lineHeight = 22.sp, fontSize = 14.sp)
        }
        Spacer(Modifier.height(20.dp))
    }
}

@Composable
private fun TopHeading(title: String, subtitle: String) {
    Column(Modifier.fillMaxWidth().padding(top = 24.dp, bottom = 20.dp)) {
        Text(title, color = Ink, fontSize = 27.sp, fontWeight = FontWeight.ExtraBold)
        Text(subtitle, color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 5.dp))
    }
}

@Composable
private fun PageContent(content: @Composable ColumnScope.() -> Unit) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        Column(
            modifier = Modifier.widthIn(max = 760.dp).fillMaxWidth().fillMaxSize()
                .verticalScroll(rememberScrollState()).padding(horizontal = 22.dp),
            content = content
        )
    }
}

@Composable
private fun SectionTitle(title: String, subtitle: String) {
    Column(Modifier.padding(top = 23.dp, bottom = 12.dp)) {
        Text(title, color = Ink, fontSize = 18.sp, fontWeight = FontWeight.Bold)
        Text(subtitle, color = Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 3.dp))
    }
}

@Composable
private fun MetricCard(label: String, value: String, hint: String, modifier: Modifier, tint: Color) {
    Card(modifier, colors = CardDefaults.cardColors(containerColor = tint), shape = RoundedCornerShape(22.dp)) {
        Column(Modifier.fillMaxWidth().padding(17.dp)) {
            Text(label, color = Muted, fontSize = 12.sp)
            Text(value, color = Ink, fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.padding(top = 7.dp))
            Text(hint, color = Muted, fontSize = 11.sp, modifier = Modifier.padding(top = 3.dp))
        }
    }
}

@Composable
private fun SmallStat(label: String, value: String) {
    Column {
        Text(label, color = Muted, fontSize = 11.sp)
        Text(value, color = Ink, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 3.dp))
    }
}

@Composable
private fun GradeButton(label: String, background: Color, foreground: Color, modifier: Modifier, onClick: () -> Unit) {
    Button(onClick = onClick, modifier = modifier.height(48.dp), shape = RoundedCornerShape(15.dp), colors = ButtonDefaults.buttonColors(containerColor = background, contentColor = foreground), contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 3.dp)) {
        Text(label, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
    }
}

private fun makePlan(minutes: Int, focus: String): List<Pair<String, Int>> {
    val shares = linkedMapOf("词汇" to 0.20, "听力" to 0.20, "阅读" to 0.20, "写作翻译" to 0.20)
    val skill = when (focus) {
        "listening" -> "听力"
        "reading" -> "阅读"
        "writing" -> "写作翻译"
        else -> null
    }
    if (skill == null) {
        listOf("听力", "阅读", "写作翻译").forEach { shares[it] = shares.getValue(it) + 0.20 / 3.0 }
    } else {
        shares[skill] = shares.getValue(skill) + 0.20
    }
    val total = minutes.coerceAtLeast(1)
    val base = shares.mapValues { (total * it.value).toInt() }.toMutableMap()
    var remaining = total - base.values.sum()
    shares.entries.sortedByDescending { total * it.value - base.getValue(it.key) }.forEach { entry ->
        if (remaining > 0) {
            base[entry.key] = base.getValue(entry.key) + 1
            remaining--
        }
    }
    return base.toList()
}
