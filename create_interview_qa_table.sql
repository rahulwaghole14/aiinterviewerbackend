CREATE TABLE IF NOT EXISTS interview_app_interviewqa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(40) NOT NULL REFERENCES interview_app_interviewsession(id) DEFERRABLE NOT NULL,
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    answer_text TEXT NULL,
    question_type VARCHAR(20) DEFAULT 'TECHNICAL',
    audio_url VARCHAR(500) NULL,
    asked_at DATETIME NULL,
    answered_at DATETIME NULL,
    response_time_seconds REAL NULL,
    words_per_minute INTEGER NULL,
    filler_word_count INTEGER NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
