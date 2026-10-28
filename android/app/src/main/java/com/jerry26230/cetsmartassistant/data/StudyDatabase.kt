package com.jerry26230.cetsmartassistant.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import org.json.JSONObject
import java.time.LocalDate
import java.time.ZoneId

data class VocabDeck(val key: String, val title: String, val subtitle: String, val asset: String)

data class StudyWord(
    val deck: String,
    val word: String,
    val phonetic: String,
    val meaning: String,
    val isNew: Boolean
)

data class DeckProgress(
    val deck: VocabDeck,
    val total: Int,
    val learned: Int,
    val due: Int,
    val newToday: Int
) {
    val unlearned: Int get() = (total - learned).coerceAtLeast(0)
}

data class DailyActivity(val day: String, val reviews: Int, val newWords: Int)

class StudyDatabase(context: Context) : SQLiteOpenHelper(context, "cet_study.db", null, 1) {
    private val appContext = context.applicationContext

    companion object {
        val decks = listOf(
            VocabDeck("cet4", "四级词汇", "CET-4 · 3,815 词", "cet4.json"),
            VocabDeck("cet6", "六级词汇", "CET-6 · 5,371 词", "cet6.json"),
            VocabDeck("ielts", "雅思词汇", "IELTS · 4,974 词", "ielts_core.json")
        )
        private const val DAY_MS = 86_400_000L
        private const val NEW_PER_DAY = 20
    }

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""CREATE TABLE vocabulary (
            deck TEXT NOT NULL, word TEXT NOT NULL, phonetic TEXT NOT NULL DEFAULT '',
            meaning TEXT NOT NULL, position INTEGER NOT NULL,
            PRIMARY KEY(deck, word))""".trimIndent())
        db.execSQL("""CREATE TABLE progress (
            deck TEXT NOT NULL, word TEXT NOT NULL, due_at INTEGER NOT NULL,
            interval_days REAL NOT NULL, repetitions INTEGER NOT NULL, lapses INTEGER NOT NULL,
            last_review INTEGER NOT NULL, PRIMARY KEY(deck, word),
            FOREIGN KEY(deck, word) REFERENCES vocabulary(deck, word))""".trimIndent())
        db.execSQL("""CREATE TABLE study_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, deck TEXT NOT NULL, word TEXT NOT NULL,
            reviewed_at INTEGER NOT NULL, day_key TEXT NOT NULL, was_new INTEGER NOT NULL)""".trimIndent())
        db.execSQL("CREATE INDEX idx_progress_due ON progress(deck, due_at)")
        db.execSQL("CREATE INDEX idx_events_day ON study_events(day_key, was_new)")
        db.execSQL("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit

    fun importBuiltInVocabulary() {
        val db = writableDatabase
        val done = db.rawQuery("SELECT value FROM settings WHERE key='vocabulary_imported'", null).use {
            it.moveToFirst() && it.getString(0) == "1"
        }
        if (done) return

        db.beginTransaction()
        try {
            decks.forEach { deck ->
                val json = appContext.assets.open("vocabularies/${deck.asset}").bufferedReader(Charsets.UTF_8).use { it.readText() }
                val words = JSONObject(json).getJSONArray("words")
                for (index in 0 until words.length()) {
                    val item = words.getJSONObject(index)
                    val meanings = item.optJSONArray("translations")
                    val meaning = buildString {
                        if (meanings != null) for (meaningIndex in 0 until meanings.length()) {
                            val part = meanings.optString(meaningIndex).trim()
                            if (part.isNotEmpty()) {
                                if (isNotEmpty()) append("；")
                                append(part)
                            }
                        }
                    }
                    val values = ContentValues().apply {
                        put("deck", deck.key)
                        put("word", item.optString("word").trim())
                        put("phonetic", item.optString("phonetic"))
                        put("meaning", meaning)
                        put("position", index)
                    }
                    db.insertWithOnConflict("vocabulary", null, values, SQLiteDatabase.CONFLICT_IGNORE)
                }
            }
            db.insertWithOnConflict("settings", null, ContentValues().apply {
                put("key", "vocabulary_imported")
                put("value", "1")
            }, SQLiteDatabase.CONFLICT_REPLACE)
            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
    }

    fun deckProgress(now: Long = System.currentTimeMillis()): List<DeckProgress> {
        val today = LocalDate.now().toString()
        return decks.map { deck ->
            val total = scalar("SELECT COUNT(*) FROM vocabulary WHERE deck=?", arrayOf(deck.key))
            val learned = scalar("SELECT COUNT(*) FROM progress WHERE deck=?", arrayOf(deck.key))
            val due = scalar("SELECT COUNT(*) FROM progress WHERE deck=? AND due_at<=?", arrayOf(deck.key, now.toString()))
            val newToday = scalar("SELECT COUNT(*) FROM study_events WHERE deck=? AND day_key=? AND was_new=1", arrayOf(deck.key, today))
            DeckProgress(deck, total, learned, due, newToday)
        }
    }

    fun studySession(deck: String, now: Long = System.currentTimeMillis()): List<StudyWord> {
        val output = mutableListOf<StudyWord>()
        readableDatabase.rawQuery(
            """SELECT v.deck,v.word,v.phonetic,v.meaning FROM vocabulary v
               JOIN progress p ON p.deck=v.deck AND p.word=v.word
               WHERE v.deck=? AND p.due_at<=? ORDER BY p.due_at LIMIT 100""".trimIndent(),
            arrayOf(deck, now.toString())
        ).use { cursor ->
            while (cursor.moveToNext()) output += cursor.toStudyWord(false)
        }
        val remainingNew = (NEW_PER_DAY - scalar(
            "SELECT COUNT(*) FROM study_events WHERE deck=? AND day_key=? AND was_new=1",
            arrayOf(deck, LocalDate.now().toString())
        )).coerceAtLeast(0)
        if (remainingNew > 0) {
            readableDatabase.rawQuery(
                """SELECT v.deck,v.word,v.phonetic,v.meaning FROM vocabulary v
                   LEFT JOIN progress p ON p.deck=v.deck AND p.word=v.word
                   WHERE v.deck=? AND p.word IS NULL ORDER BY v.position LIMIT ?""".trimIndent(),
                arrayOf(deck, remainingNew.toString())
            ).use { cursor ->
                while (cursor.moveToNext()) output += cursor.toStudyWord(true)
            }
        }
        return output
    }

    fun recordAnswer(word: StudyWord, grade: ReviewGrade, now: Long = System.currentTimeMillis()) {
        val db = writableDatabase
        val prior = db.rawQuery(
            "SELECT interval_days,repetitions,lapses FROM progress WHERE deck=? AND word=?",
            arrayOf(word.deck, word.word)
        ).use { cursor ->
            if (cursor.moveToFirst()) Triple(cursor.getDouble(0), cursor.getInt(1), cursor.getInt(2)) else null
        }
        val wasNew = prior == null
        val oldInterval = prior?.first ?: 0.0
        val oldReps = prior?.second ?: 0
        val oldLapses = prior?.third ?: 0
        val interval = when (grade) {
            ReviewGrade.AGAIN -> if (oldInterval <= 0.0) 1.0 / 24.0 else (oldInterval * 0.5).coerceAtLeast(1.0)
            ReviewGrade.HARD -> if (oldInterval <= 0.0) 1.0 else (oldInterval * 1.3).coerceAtLeast(1.0)
            ReviewGrade.GOOD -> when (oldReps) {
                0 -> 1.0
                1 -> 3.0
                2 -> 7.0
                else -> (oldInterval * 1.8).coerceAtLeast(1.0)
            }
            ReviewGrade.EASY -> if (oldInterval <= 0.0) 3.0 else (oldInterval * 2.5).coerceAtLeast(3.0)
        }
        val repetitions = if (grade == ReviewGrade.AGAIN) 0 else oldReps + 1
        val values = ContentValues().apply {
            put("deck", word.deck)
            put("word", word.word)
            put("interval_days", interval)
            put("repetitions", repetitions)
            put("lapses", oldLapses + if (grade == ReviewGrade.AGAIN) 1 else 0)
            put("last_review", now)
            put("due_at", now + (interval * DAY_MS).toLong())
        }
        db.insertWithOnConflict("progress", null, values, SQLiteDatabase.CONFLICT_REPLACE)
        db.insert("study_events", null, ContentValues().apply {
            put("deck", word.deck)
            put("word", word.word)
            put("reviewed_at", now)
            put("day_key", LocalDate.now().toString())
            put("was_new", if (wasNew) 1 else 0)
        })
    }

    fun searchWords(deck: String, query: String, limit: Int = 50): List<StudyWord> {
        if (query.isBlank()) return emptyList()
        val pattern = "%${query.trim()}%"
        return readableDatabase.rawQuery(
            "SELECT deck,word,phonetic,meaning FROM vocabulary WHERE deck=? AND (word LIKE ? OR meaning LIKE ?) ORDER BY position LIMIT ?",
            arrayOf(deck, pattern, pattern, limit.toString())
        ).use { cursor -> buildList { while (cursor.moveToNext()) add(cursor.toStudyWord(false)) } }
    }

    fun setting(key: String, default: String = ""): String = readableDatabase.rawQuery(
        "SELECT value FROM settings WHERE key=?", arrayOf(key)
    ).use { if (it.moveToFirst()) it.getString(0) else default }

    fun saveSetting(key: String, value: String) {
        writableDatabase.insertWithOnConflict("settings", null, ContentValues().apply {
            put("key", key)
            put("value", value)
        }, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun activity(days: Int = 7): List<DailyActivity> {
        val firstDay = LocalDate.now().minusDays((days - 1).toLong())
        val map = mutableMapOf<String, Pair<Int, Int>>()
        readableDatabase.rawQuery(
            "SELECT day_key,COUNT(*),SUM(was_new) FROM study_events WHERE day_key>=? GROUP BY day_key ORDER BY day_key",
            arrayOf(firstDay.toString())
        ).use { cursor ->
            while (cursor.moveToNext()) map[cursor.getString(0)] = cursor.getInt(1) to cursor.getInt(2)
        }
        return (0 until days).map { offset ->
            val day = firstDay.plusDays(offset.toLong()).toString()
            val counts = map[day] ?: (0 to 0)
            DailyActivity(day, counts.first, counts.second)
        }
    }

    private fun scalar(sql: String, args: Array<String>): Int = readableDatabase.rawQuery(sql, args).use {
        if (it.moveToFirst()) it.getInt(0) else 0
    }

    private fun android.database.Cursor.toStudyWord(isNew: Boolean) = StudyWord(
        deck = getString(0), word = getString(1), phonetic = getString(2), meaning = getString(3), isNew = isNew
    )
}

enum class ReviewGrade { AGAIN, HARD, GOOD, EASY }
