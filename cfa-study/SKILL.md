---
name: cfa-study
description: A comprehensive skill for managing and tracking CFA (Chartered Financial Analyst) studies
user-invocable: true
---

# CFA Study Skill

A skill for managing and tracking your Chartered Financial Analyst (CFA) certification journey, including progress tracking, study planning, and practice questions.

## Description

This skill helps you manage your CFA studies by tracking your progress through the three levels of the certification. It includes features for logging study sessions, tracking topic mastery, setting goals, and providing practice questions.

## Features

- **Profile Management**: Track your current CFA level, study hours, and exam goals
- **Progress Tracking**: Monitor your progress through each topic area
- **Study Logging**: Record study sessions with hours spent and topics covered
- **Study Planning**: Get recommendations on which topics to focus on next
- **Practice Questions**: Access practice questions for each topic and level
- **Performance Analytics**: Track your question performance and identify weak areas
- **Streak Tracking**: Maintain motivation with consecutive study day tracking
- **Tutor Mode**: Interactive tutoring with detailed explanations, real-world examples, and personalized guidance

## Usage

### Basic Commands:

- `cfa-study profile` - View your current CFA study profile
- `cfa-study set-level <1|2|3>` - Set your current CFA level
- `cfa-study set-target-date YYYY-MM-DD` - Set your target exam date
- `cfa-study log-study <hours> <topic> [questions_answered] [correct_answers]` - Log a study session
- `cfa-study topics` - View your progress across all topics
- `cfa-study plan` - Get recommended study plan
- `cfa-study complete-level <1|2|3>` - Mark a level as completed
- `cfa-study practice <topic> <level> [count]` - Get practice questions

### Tutor Mode Commands:

- `cfa-study enable-tutor` - Enable interactive tutor mode
- `cfa-study disable-tutor` - Disable tutor mode
- `cfa-study tutor-plan` - Get a personalized study plan with tutor recommendations
- `cfa-study tutor-explain <topic>` - Get detailed explanation of a topic with real-world examples

### Quiz Commands:

- `cfa-study quiz <topic> <level> [question_num]` - Get a practice question to answer
- `cfa-study answer <topic> <level> <question_num> <A/B/C/D>` - Submit your answer to track performance

### Example Usage:

1. Start by setting your current level:
   ```
   cfa-study set-level 1
   ```

2. Set your target exam date:
   ```
   cfa-study set-target-date 2026-06-01
   ```

3. Log a study session after studying Ethics for 2 hours:
   ```
   cfa-study log-study 2 "Ethics" 10 7
   ```

4. Check your progress:
   ```
   cfa-study profile
   cfa-study topics
   ```

5. Get practice questions:
   ```
   cfa-study practice "Quantitative Methods" 1 5
   ```

## Topic Areas Covered

The skill tracks progress across all major CFA topic areas:
- Ethics
- Quantitative Methods
- Economics
- Financial Reporting and Analysis
- Corporate Finance
- Equity Investments
- Fixed Income
- Derivatives
- Alternative Investments
- Portfolio Management

## Implementation

This skill is implemented in Python as `scripts/cfa_study.py`. It provides the same functionality as the original JavaScript version with improved maintainability and integration with Python-based systems.

## Data Storage

All user data is stored in `cfa-data.json` within the skill directory, including:
- Current level and study progress
- Completed levels
- Study hours and session logs
- Question performance statistics
- Target exam date
- Streak tracking

The skill maintains your learning history and adapts recommendations based on your progress.