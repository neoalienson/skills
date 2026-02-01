# CFA Study Skill

A comprehensive skill for managing and tracking CFA (Chartered Financial Analyst) studies with interactive quizzes, progress tracking, and personalized tutoring features.

## Features

- **Interactive Quizzes**: Practice questions for all CFA topics and levels
- **Progress Tracking**: Monitor your study hours, topic completion, and performance
- **Personalized Tutoring**: Detailed explanations and study plans
- **Performance Analytics**: Track your strengths and areas for improvement
- **Question Repetition Prevention**: Avoid seeing the same questions repeatedly

## Supported Topics

- Ethics and Professional Standards
- Quantitative Methods
- Economics
- Financial Reporting and Analysis
- Corporate Finance
- Equity Investments
- Fixed Income
- Derivatives
- Alternative Investments
- Portfolio Management

## Usage

### Command Line Interface

```bash
# View your CFA study profile
node skills/cfa-study/scripts/cfa_study.mjs profile

# Set your current CFA level (1, 2, or 3)
node skills/cfa-study/scripts/cfa_study.mjs set-level <level>

# Set your target exam date
node skills/cfa-study/scripts/cfa_study.mjs set-target-date YYYY-MM-DD

# Get practice questions
node skills/cfa-study/scripts/cfa_study.mjs practice <topic> <level> [count]

# Take a quiz
node skills/cfa-study/scripts/cfa_study.mjs quiz <topic> <level> [question_num]

# Submit an answer
node skills/cfa-study/scripts/cfa_study.mjs answer <topic> <level> <question_num> <A/B/C/D>

# Enable tutor mode for personalized learning
node skills/cfa-study/scripts/cfa_study.mjs enable-tutor

# Get a personalized study plan
node skills/cfa-study/scripts/cfa_study.mjs tutor-plan

# Get detailed explanation for a topic
node skills/cfa-study/scripts/cfa_study.mjs tutor-explain <topic>

# Log a study session
node skills/cfa-study/scripts/cfa_study.mjs log-study <hours> <topic> [questions_answered] [correct_answers]

# View topic progress
node skills/cfa-study/scripts/cfa_study.mjs topics

# View suggested study plan
node skills/cfa-study/scripts/cfa_study.mjs plan

# Mark a level as completed
node skills/cfa-study/scripts/cfa_study.mjs complete-level <level>
```

### Programmatic Usage

```javascript
import CFAStudyManager from './skills/cfa-study/scripts/cfa_study.mjs';

const cfaManager = new CFAStudyManager();

// Get practice questions
const questions = cfaManager.getPracticeQuestions('Ethics', 1, 5);

// Record an answer
const result = cfaManager.recordPracticeSession('Ethics', 1, 'B', 'B');

// Get your profile
const profile = cfaManager.getProfile();

// Log a study session
cfaManager.logStudySession(2.5, 'Quantitative Methods', 10, 8);

// Enable tutor mode
cfaManager.setTutorMode(true);

// Get personalized study plan
const studyPlan = cfaManager.generateStudyPlan();
```

## Configuration

The skill stores user data in `skills/cfa-study/cfa-data.json`, which includes:

- Current CFA level
- Study hours
- Topic progress
- Performance metrics
- Completed levels
- Target exam date
- Learning streak

## Development

### Running Tests

```bash
node skills/cfa-study/test_cfa_skill.mjs
```

### Adding New Questions

To add new questions for a topic, update the `questionsBank` object in the script:

```javascript
const questionsBank = {
  'New Topic': {
    1: [  // Level 1 questions
      {
        question: "Your question here?",
        options: [
          "Option A",
          "Option B", 
          "Option C",
          "Option D"
        ],
        answer: 'B',
        explanation: "Detailed explanation here..."
      }
    ]
  }
};
```

## License

This skill is part of the Moltbot ecosystem and follows its licensing terms.