#!/usr/bin/env python3

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union


class CFAStudyManager:
    def __init__(self, workspace_dir: str = '/home/neo/bot-nekochan'):
        self.workspace_dir = workspace_dir
        self.data_file = os.path.join(workspace_dir, 'skills', 'cfa-study', 'cfa-data.json')
        self.asked_questions = set()
        self.load_profile()

    def load_profile(self):
        """Load the user's CFA study profile from file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.profile = json.load(f)
            except Exception as e:
                print(f'Error loading CFA profile: {str(e)}')
                self.create_default_profile()
        else:
            self.create_default_profile()

    def create_default_profile(self):
        """Create a default profile if none exists."""
        self.profile = {
            'userId': int(datetime.now().timestamp()),  # Placeholder for user identification
            'currentLevel': 1,  # Default to Level I
            'startDate': datetime.now().isoformat(),
            'targetExamDate': None,
            'studyHours': 0,
            'topics': {
                'Ethics': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False},
                'Quantitative Methods': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False},
                'Economics': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False},
                'Financial Reporting and Analysis': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False},
                'Corporate Finance': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False},
                'Equity Investments': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False},
                'Fixed Income': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False},
                'Derivatives': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False},
                'Alternative Investments': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False},
                'Portfolio Management': {'level1': 0, 'level2': 0, 'level3': 0, 'completed': False}
            },
            'completedLevels': [],
            'lastStudyDate': None,
            'streak': 0,
            'totalQuestionsAnswered': 0,
            'correctAnswers': 0,
            'performanceByTopic': {},
            'tutorMode': False
        }
        self.save_profile()

    def save_profile(self):
        """Save the user's CFA study profile to file."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, indent=2)
        except Exception as e:
            print(f'Error saving CFA profile: {str(e)}')
            raise e

    def get_profile(self):
        """Get current profile information."""
        overall_performance = 0
        if self.profile['totalQuestionsAnswered'] > 0:
            overall_performance = round(
                self.profile['correctAnswers'] / self.profile['totalQuestionsAnswered'] * 100, 2
            )
        
        return {
            'currentLevel': self.profile['currentLevel'],
            'targetExamDate': self.profile['targetExamDate'],
            'studyHours': self.profile['studyHours'],
            'completedLevels': self.profile['completedLevels'],
            'streak': self.profile['streak'],
            'overallPerformance': overall_performance,
            'tutorMode': self.profile['tutorMode']
        }

    def set_current_level(self, level: int) -> bool:
        """Update current CFA level."""
        if 1 <= level <= 3:
            self.profile['currentLevel'] = level
            self.save_profile()
            return True
        return False

    def set_target_exam_date(self, date_string: str) -> bool:
        """Set target exam date."""
        try:
            datetime.fromisoformat(date_string)
        except ValueError:
            return False
        
        self.profile['targetExamDate'] = date_string
        self.save_profile()
        return True

    def set_tutor_mode(self, enabled: bool) -> bool:
        """Enable/disable tutor mode."""
        self.profile['tutorMode'] = enabled
        self.save_profile()
        return True

    def log_study_session(self, hours: float, topic: str, questions_answered: int = 0, correct_answers: int = 0):
        """Log study session."""
        # Add study hours
        self.profile['studyHours'] += hours
        
        # Update topic progress (simple increment for now)
        if topic in self.profile['topics']:
            current_level = self.profile['currentLevel']
            level_key = f'level{current_level}'
            self.profile['topics'][topic][level_key] += hours
            if self.profile['topics'][topic][level_key] >= 10:  # Arbitrary threshold for completion
                self.profile['topics'][topic]['completed'] = True
        
        # Update last study date and streak
        today = datetime.now().date().isoformat()
        last_study_date = None
        if self.profile['lastStudyDate']:
            last_study_date = datetime.fromisoformat(self.profile['lastStudyDate']).date().isoformat()
        
        if last_study_date == today:
            # Already studied today, don't increase streak
            pass
        elif last_study_date:
            prev_date = datetime.fromisoformat(last_study_date).date()
            current_date = datetime.fromisoformat(today).date()
            diff_days = (current_date - prev_date).days
            
            if diff_days == 1:
                # Consecutive day
                self.profile['streak'] += 1
            elif diff_days > 1:
                # Missed a day or more, reset streak
                self.profile['streak'] = 1
            else:
                # First time studying
                self.profile['streak'] = 1
        else:
            # First time studying
            self.profile['streak'] = 1
        
        self.profile['lastStudyDate'] = datetime.now().isoformat()
        
        # Update question statistics
        self.profile['totalQuestionsAnswered'] += questions_answered
        self.profile['correctAnswers'] += correct_answers
        
        self.save_profile()

    def get_topic_progress(self):
        """Get topic progress."""
        current_level = self.profile['currentLevel']
        level_key = f'level{current_level}'
        progress = {}
        
        for topic, data in self.profile['topics'].items():
            progress[topic] = {
                'progress': data[level_key],
                'completed': data['completed']
            }
        
        return progress

    def get_study_plan(self):
        """Get study plan."""
        current_level = self.profile['currentLevel']
        incomplete_topics = []
        
        for topic, data in self.profile['topics'].items():
            if not data['completed']:
                incomplete_topics.append({
                    'topic': topic,
                    'progress': data[f'level{current_level}']
                })
        
        # Sort by least progressed topics first
        incomplete_topics.sort(key=lambda x: x['progress'])
        
        return incomplete_topics

    def complete_level(self, level: int) -> bool:
        """Mark a level as completed."""
        if (1 <= level <= 3 and 
            level not in self.profile['completedLevels']):
            self.profile['completedLevels'].append(level)
            self.profile['completedLevels'].sort()
            
            # Move to next level if available
            if level < 3:
                self.profile['currentLevel'] = level + 1
            
            self.save_profile()
            return True
        return False

    def get_practice_questions(self, topic: str, level: int, count: int = 5) -> List[Dict]:
        """Get practice questions by topic and level."""
        # Define actual questions for each topic at each level
        questions_bank = {
            'Ethics': {
                1: [
                    {
                        'question': "Which of the following best describes a primary requirement of the CFA Institute Code of Ethics?",
                        'options': [
                            "Members and candidates must place their own interests above those of their clients",
                            "Members and candidates must place the integrity of the investment profession and the interests of clients above their own personal interests",
                            "Members and candidates must prioritize their employer's interests above all others",
                            "Members and candidates must follow their country's laws regardless of CFA Institute standards"
                        ],
                        'answer': 'B',
                        'explanation': "The CFA Institute Code of Ethics requires members and candidates to place the integrity of the investment profession and the interests of clients above their own personal interests."
                    },
                    {
                        'question': "According to the CFA Institute Standards of Professional Conduct, which of the following is a violation of the Professionalism standard?",
                        'options': [
                            "Making investment recommendations based on thorough research",
                            "Accepting compensation from a client in addition to salary from an employer without written consent",
                            "Disclosing conflicts of interest to clients",
                            "Maintaining competence through continuing education"
                        ],
                        'answer': 'B',
                        'explanation': "Accepting additional compensation without written consent from both parties is a violation of Standard IV(A) - Loyalty to Employer."
                    },
                    {
                        'question': "A portfolio manager recommends a high-risk investment to a client without fully disclosing the potential conflicts of interest. This action most likely violates which standards?",
                        'options': [
                            "Duties to Employers and Integrity of Capital Markets",
                            "Duties to Clients and Professionalism",
                            "Conflicts of Interest and Duties to Clients",
                            "Investment Analysis and Record Retention"
                        ],
                        'answer': 'C',
                        'explanation': "This violates Standard VI(A) - Disclosure of Conflicts and Standard III(C) - Suitability."
                    },
                    {
                        'question': "Which of the following is NOT one of the six major sections of the CFA Institute Standards of Professional Conduct?",
                        'options': [
                            "Professionalism",
                            "Integrity of Capital Markets",
                            "Duties to Colleagues",
                            "Investment Recommendations and Actions"
                        ],
                        'answer': 'C',
                        'explanation': "The six major sections are: Professionalism, Integrity of Capital Markets, Duties to Clients, Duties to Employers, Investment Analysis, Recommendations and Actions, and Conflicts of Interest. There is no 'Duties to Colleagues' section."
                    },
                    {
                        'question': "According to the CFA Institute Code of Ethics, members and candidates must act with:",
                        'options': [
                            "Integrity, competence, dignity, and in an ethical manner",
                            "Only the highest levels of mathematical skill",
                            "Primary concern for their own financial gain",
                            "Complete independence from market forces"
                        ],
                        'answer': 'A',
                        'explanation': "The Code of Ethics states that members and candidates must act with integrity, competence, dignity, and in an ethical manner."
                    }
                ]
            },
            'Quantitative Methods': {
                1: [
                    {
                        'question': "What is the present value of $1,000 to be received in 3 years if the annual discount rate is 5%?",
                        'options': [
                            "$863.84",
                            "$850.00",
                            "$1,157.63",
                            "$1,000.00"
                        ],
                        'answer': 'A',
                        'explanation': "PV = FV/(1+r)^n = $1,000/(1.05)^3 = $1,000/1.157625 = $863.84"
                    },
                    {
                        'question': "Which of the following is a measure of central tendency?",
                        'options': [
                            "Range",
                            "Standard deviation",
                            "Median",
                            "Variance"
                        ],
                        'answer': 'C',
                        'explanation': "The median is a measure of central tendency, along with the mean and mode. Range, standard deviation, and variance are measures of dispersion."
                    },
                    {
                        'question': "In a normal distribution, approximately what percentage of observations fall within one standard deviation of the mean?",
                        'options': [
                            "68%",
                            "90%",
                            "95%",
                            "99%"
                        ],
                        'answer': 'A',
                        'explanation': "In a normal distribution, approximately 68% of observations fall within one standard deviation of the mean, 95% within two standard deviations, and 99% within three standard deviations."
                    },
                    {
                        'question': "Which of the following best describes the relationship between covariance and correlation?",
                        'options': [
                            "Correlation is the standardized form of covariance",
                            "Covariance is the standardized form of correlation",
                            "They are identical measures",
                            "They measure opposite relationships"
                        ],
                        'answer': 'A',
                        'explanation': "Correlation is the standardized form of covariance, calculated as covariance divided by the product of the standard deviations of the two variables."
                    },
                    {
                        'question': "A Type I error in hypothesis testing occurs when:",
                        'options': [
                            "We fail to reject a true null hypothesis",
                            "We reject a true null hypothesis",
                            "We accept a false null hypothesis",
                            "We correctly reject a false null hypothesis"
                        ],
                        'answer': 'B',
                        'explanation': "A Type I error occurs when we incorrectly reject a true null hypothesis (false positive)."
                    }
                ]
            },
            'Economics': {
                1: [
                    {
                        'question': "If the central bank increases the money supply, what is the most likely short-term effect on interest rates and aggregate demand?",
                        'options': [
                            "Interest rates increase and aggregate demand decreases",
                            "Interest rates decrease and aggregate demand increases",
                            "Both interest rates and aggregate demand decrease",
                            "Both interest rates and aggregate demand increase"
                        ],
                        'answer': 'B',
                        'explanation': "Increasing money supply typically lowers interest rates, which stimulates borrowing and spending, increasing aggregate demand."
                    },
                    {
                        'question': "Which of the following best describes the law of demand?",
                        'options': [
                            "Quantity demanded increases as price increases",
                            "Quantity demanded decreases as price increases",
                            "Quantity demanded remains constant regardless of price",
                            "Quantity demanded is inversely related to supply"
                        ],
                        'answer': 'B',
                        'explanation': "The law of demand states that there is an inverse relationship between price and quantity demanded, all else equal."
                    },
                    {
                        'question': "In which phase of the business cycle would we expect to see rising employment and increasing GDP?",
                        'options': [
                            "Trough",
                            "Contraction",
                            "Peak",
                            "Expansion"
                        ],
                        'answer': 'D',
                        'explanation': "During expansion, economic activity increases, leading to rising employment and GDP growth."
                    },
                    {
                        'question': "Which of the following is most likely to cause a leftward shift in the aggregate demand curve?",
                        'options': [
                            "Decrease in taxes",
                            "Increase in consumer confidence",
                            "Decrease in government spending",
                            "Reduction in interest rates"
                        ],
                        'answer': 'C',
                        'explanation': "A decrease in government spending reduces aggregate demand, shifting the curve to the left."
                    },
                    {
                        'question': "Which type of unemployment is associated with economic downturns?",
                        'options': [
                            "Frictional unemployment",
                            "Structural unemployment",
                            "Cyclical unemployment",
                            "Seasonal unemployment"
                        ],
                        'answer': 'C',
                        'explanation': "Cyclical unemployment occurs during economic recessions and downturns when demand for goods and services falls."
                    }
                ]
            },
            'Financial Reporting and Analysis': {
                1: [
                    {
                        'question': "Which of the following financial statements reports a company's financial position at a specific point in time?",
                        'options': [
                            "Income Statement",
                            "Balance Sheet",
                            "Cash Flow Statement",
                            "Statement of Owners' Equity"
                        ],
                        'answer': 'B',
                        'explanation': "The Balance Sheet reports a company's assets, liabilities, and equity at a specific point in time, while other statements report activities over a period."
                    },
                    {
                        'question': "Which of the following ratios measures a company's ability to meet short-term obligations?",
                        'options': [
                            "Debt-to-Equity Ratio",
                            "Return on Assets",
                            "Current Ratio",
                            "Asset Turnover Ratio"
                        ],
                        'answer': 'C',
                        'explanation': "The Current Ratio (Current Assets / Current Liabilities) measures short-term liquidity and the ability to meet near-term obligations."
                    },
                    {
                        'question': "Under U.S. GAAP, which inventory valuation method results in the lowest taxable income during periods of rising prices?",
                        'options': [
                            "FIFO (First-In, First-Out)",
                            "LIFO (Last-In, First-Out)",
                            "Weighted Average Cost",
                            "Specific Identification"
                        ],
                        'answer': 'B',
                        'explanation': "LIFO assigns the cost of the most recently purchased inventory to COGS, resulting in higher COGS and lower taxable income during inflation."
                    },
                    {
                        'question': "Which of the following is classified as an operating activity in the cash flow statement?",
                        'options': [
                            "Purchase of equipment",
                            "Payment of dividends",
                            "Receipt of dividends from investments",
                            "Issuance of common stock"
                        ],
                        'answer': 'C',
                        'explanation': "Receipt of dividends is considered an operating activity as it relates to the core business operations."
                    },
                    {
                        'question': "Which of the following is true regarding the accounting equation?",
                        'options': [
                            "Assets = Liabilities - Equity",
                            "Assets = Equity - Liabilities",
                            "Assets = Liabilities + Equity",
                            "Liabilities = Assets + Equity"
                        ],
                        'answer': 'C',
                        'explanation': "The fundamental accounting equation is Assets = Liabilities + Equity, representing the sources of funds for a company's assets."
                    }
                ]
            },
            'Corporate Finance': {
                1: [
                    {
                        'question': "Which of the following ratios measures a company's ability to meet short-term obligations?",
                        'options': [
                            "Debt-to-Equity Ratio",
                            "Return on Assets",
                            "Current Ratio",
                            "Asset Turnover Ratio"
                        ],
                        'answer': 'C',
                        'explanation': "The Current Ratio (Current Assets / Current Liabilities) measures short-term liquidity and the ability to meet near-term obligations."
                    },
                    {
                        'question': "Corporate Finance covers capital budgeting, cost of capital, and working capital management. Understanding which of the following is essential for evaluating investment projects?",
                        'options': [
                            "NPV, IRR, and payback period",
                            "Beta coefficient and market risk premium",
                            "Dividend payout ratio and retention rate",
                            "Price-to-earnings ratio and market-to-book ratio"
                        ],
                        'answer': 'A',
                        'explanation': "Understanding NPV (Net Present Value), IRR (Internal Rate of Return), and payback period is essential for evaluating investment projects in corporate finance."
                    },
                    {
                        'question': "What does the weighted average cost of capital (WACC) represent?",
                        'options': [
                            "The cost of debt financing only",
                            "The cost of equity financing only",
                            "The average rate of return a company is expected to pay to its security holders",
                            "The minimum return required by preferred shareholders"
                        ],
                        'answer': 'C',
                        'explanation': "WACC represents the average rate of return a company is expected to pay to its security holders, weighted by the proportion of each financing source."
                    },
                    {
                        'question': "Which of the following best describes the optimal capital structure?",
                        'options': [
                            "The mix of debt and equity that maximizes the company's tax shield",
                            "The mix of debt and equity that minimizes the company's cost of equity",
                            "The mix of debt and equity that maximizes the company's stock price",
                            "The mix of debt and equity that equals 50% debt and 50% equity"
                        ],
                        'answer': 'C',
                        'explanation': "The optimal capital structure is the mix of debt and equity that maximizes the company's stock price (or equivalently, minimizes the WACC)."
                    },
                    {
                        'question': "Which dividend policy suggests that firms should pay out residual earnings after funding all profitable investment opportunities?",
                        'options': [
                            "Stable dividend policy",
                            "Constant dividend payout ratio policy",
                            "Residual dividend model",
                            "Fixed dividend policy"
                        ],
                        'answer': 'C',
                        'explanation': "The residual dividend model suggests that firms should pay out residual earnings after funding all profitable investment opportunities."
                    }
                ]
            }
        }

        # Get questions for the specified topic and level
        topic_questions = questions_bank.get(topic, {}).get(level, [
            {
                'question': f'Sample question for {topic} at Level {level}',
                'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                'answer': 'B',
                'explanation': 'This is a sample explanation for the question.'
            }
        ])

        # Filter out previously asked questions if we have them
        available_questions = [
            q for q in topic_questions 
            if f"{topic}-{level}-{q['question'][:20].replace(' ', '_')}" not in self.asked_questions
        ]

        # If no new questions are available, reset the asked questions for this topic
        if len(available_questions) == 0:
            self.reset_asked_questions_for_topic(topic)
            return self.get_practice_questions(topic, level, count)

        # Shuffle available questions and take the requested count
        import random
        shuffled = available_questions.copy()
        random.shuffle(shuffled)
        selected_questions = shuffled[:min(count, len(shuffled))]

        # Mark these questions as asked
        for q in selected_questions:
            question_id = f"{topic}-{level}-{q['question'][:20].replace(' ', '_')}"
            self.asked_questions.add(question_id)

        return selected_questions

    def reset_asked_questions_for_topic(self, topic: str):
        """Reset asked questions for a specific topic (when all questions have been asked)."""
        questions_to_reset = [q_id for q_id in self.asked_questions if q_id.startswith(f"{topic}-")]
        for q_id in questions_to_reset:
            self.asked_questions.discard(q_id)

    def record_practice_session(self, topic: str, level: int, user_answer: str, correct_answer: str, time_spent_sec: int = 60):
        """Record a practice session and update performance."""
        # Update question statistics
        self.profile['totalQuestionsAnswered'] += 1
        if user_answer.upper() == correct_answer:
            self.profile['correctAnswers'] += 1
        
        # Update performance by topic
        if topic not in self.profile['performanceByTopic']:
            self.profile['performanceByTopic'][topic] = {
                'attempts': 0,
                'correct': 0,
                'timeSpent': 0
            }
        
        self.profile['performanceByTopic'][topic]['attempts'] += 1
        if user_answer.upper() == correct_answer:
            self.profile['performanceByTopic'][topic]['correct'] += 1
        self.profile['performanceByTopic'][topic]['timeSpent'] += time_spent_sec
        
        self.save_profile()
        
        performance = 0
        if self.profile['totalQuestionsAnswered'] > 0:
            performance = self.profile['correctAnswers'] / self.profile['totalQuestionsAnswered'] * 100
        
        return {
            'correct': user_answer.upper() == correct_answer,
            'correctAnswer': correct_answer,
            'performance': performance
        }

    def generate_study_plan(self):
        """Generate a personalized study plan for tutor mode."""
        current_level = self.profile['currentLevel']
        incomplete_topics = self.get_study_plan()
        
        # Calculate how many topics to focus on based on level
        if current_level == 1:
            # For Level 1, focus on foundational topics
            topics_to_focus = incomplete_topics[:4]
        else:
            # For Level 2 and 3, distribute across all remaining topics
            topics_to_focus = incomplete_topics[:6]
        
        # Generate a 4-week study plan
        study_plan = {
            'level': current_level,
            'weeks': 4,
            'topics': topics_to_focus,
            'dailyHours': 2,
            'focusStrategy': (
                "Foundational understanding" if current_level == 1 
                else "Application and analysis" if current_level == 2 
                else "Integration and synthesis"
            )
        }
        
        return study_plan

    def generate_tutor_explanation(self, topic: str):
        """Generate tutor-style explanation for a topic."""
        current_level = self.profile['currentLevel']
        
        # Define explanations for each topic at each level
        explanations = {
            'Ethics': {
                1: {
                    'title': "Ethics and Professional Standards (Level I)",
                    'explanation': "Ethics forms the foundation of investment practice. At Level I, focus on understanding the CFA Institute Code of Ethics and Standards of Professional Conduct. Key concepts include: loyalty, prudence, and care; fair dealing; suitability; and responsibility of supervisors.",
                    'realWorldExample': "Consider the case of a portfolio manager who recommends a fund to clients without fully disclosing the potential conflicts of interest. This violates Standard VI(B) - Priority of Transactions and Standard I(D) - Misconduct.",
                    'keyPoints': [
                        "Understand the six major standards",
                        "Know how to apply them to scenarios",
                        "Recognize violations and proper procedures"
                    ]
                },
                2: {
                    'title': "Ethics in Asset Management Context (Level II)",
                    'explanation': "At Level II, ethics is integrated into each vignette. You'll encounter ethical dilemmas within the context of specific investments and client situations. The focus shifts from knowing standards to applying them.",
                    'realWorldExample': "An analyst discovers material non-public information about a company. While this doesn't directly affect the analysis, the ethical implications of trading on or sharing this information are significant.",
                    'keyPoints': [
                        "Apply ethical standards to complex scenarios",
                        "Identify ethical issues in case studies",
                        "Recommend appropriate actions based on standards"
                    ]
                },
                3: {
                    'title': "Ethical and Professional Considerations (Level III)",
                    'explanation': "At Level III, ethics involves portfolio management and wealth planning decisions. Candidates must consider the ethical implications of investment strategies and client relationships.",
                    'realWorldExample': "A wealth advisor must balance the needs of multiple beneficiaries in an estate plan, considering both legal requirements and ethical obligations to each party.",
                    'keyPoints': [
                        "Evaluate ethical considerations in portfolio decisions",
                        "Address conflicts of interest in wealth planning",
                        "Integrate ethics into investment policy statements"
                    ]
                }
            },
            'Quantitative Methods': {
                1: {
                    'title': "Quantitative Methods (Level I)",
                    'explanation': "Quantitative Methods provides the mathematical foundation for investment analysis. Topics include time value of money, statistical concepts, probability distributions, and hypothesis testing.",
                    'realWorldExample': "An investor calculates the present value of future cash flows to determine whether a bond investment is attractive at its current price.",
                    'keyPoints': [
                        "Understand basic statistical measures (mean, median, mode)",
                        "Calculate probabilities and interpret distributions",
                        "Perform hypothesis tests"
                    ]
                },
                2: {
                    'title': "Quantitative Applications in Valuation (Level II)",
                    'explanation': "At Level II, quantitative methods are applied to valuation models. Correlation and regression analysis are used to understand relationships between variables affecting asset prices.",
                    'realWorldExample': "An analyst uses regression analysis to determine how changes in interest rates affect bond prices, helping predict portfolio performance under different economic scenarios.",
                    'keyPoints': [
                        "Apply correlation and regression to investment problems",
                        "Use probability concepts in valuation",
                        "Interpret statistical significance in financial contexts"
                    ]
                },
                3: {
                    'title': "Quantitative Methods in Portfolio Management (Level III)",
                    'explanation': "At Level III, quantitative methods support portfolio construction and risk management. Techniques include Monte Carlo simulation and factor modeling.",
                    'realWorldExample': "A portfolio manager uses Monte Carlo simulation to model potential portfolio outcomes under various market conditions to optimize asset allocation.",
                    'keyPoints': [
                        "Apply advanced quantitative techniques to portfolio decisions",
                        "Model risk and return scenarios",
                        "Evaluate portfolio performance using quantitative methods"
                    ]
                }
            },
            'Economics': {
                1: {
                    'title': "Economic Analysis (Level I)",
                    'explanation': "Economics covers microeconomic and macroeconomic principles. Micro focuses on supply and demand, market structures, and consumer choice theory. Macroeconomics covers business cycles, monetary/fiscal policy, and international trade.",
                    'realWorldExample': "When central banks raise interest rates, it affects currency values, inflation expectations, and investment decisions across global markets.",
                    'keyPoints': [
                        "Understand supply and demand dynamics",
                        "Recognize phases of business cycle",
                        "Analyze impact of monetary and fiscal policy"
                    ]
                },
                2: {
                    'title': "Economic Analysis Applied to Equity and Fixed Income (Level II)",
                    'explanation': "At Level II, economic analysis is applied to forecasting market movements and understanding sector rotation. Economic indicators help predict equity and fixed income performance.",
                    'realWorldExample': "Rising unemployment claims signal economic weakness, potentially leading to lower interest rates, which increases bond prices and favors defensive equity sectors.",
                    'keyPoints': [
                        "Link economic indicators to asset classes",
                        "Forecast market movements based on economic trends",
                        "Apply economic analysis to security selection"
                    ]
                },
                3: {
                    'title': "Economic Considerations in Portfolio Management (Level III)",
                    'explanation': "At Level III, economic factors influence strategic asset allocation and tactical adjustments. Currency considerations become critical in global portfolios.",
                    'realWorldExample': "A pension fund adjusts its asset allocation based on demographic trends, economic growth projections, and changing interest rate environments.",
                    'keyPoints': [
                        "Integrate economic outlook into asset allocation",
                        "Assess currency risks in global portfolios",
                        "Adjust strategy based on economic cycle position"
                    ]
                }
            },
            'Financial Reporting and Analysis': {
                1: {
                    'title': "Financial Statement Analysis (Level I)",
                    'explanation': "FSA introduces the three primary financial statements: income statement, balance sheet, and cash flow statement. Understanding accounting principles and ratios is crucial for analyzing company performance.",
                    'realWorldExample': "An investor compares two companies in the same industry using ROE, debt-to-equity ratio, and current ratio to determine which has stronger fundamentals.",
                    'keyPoints': [
                        "Understand the structure of financial statements",
                        "Calculate and interpret key financial ratios",
                        "Recognize differences between accounting standards (IFRS vs. US GAAP)"
                    ]
                },
                2: {
                    'title': "Advanced Financial Statement Analysis (Level II)",
                    'explanation': "At Level II, focus on understanding footnotes, alternative accounting treatments, and how different accounting choices affect ratios and comparisons.",
                    'realWorldExample': "An analyst evaluates the impact of a company's change from FIFO to LIFO inventory accounting on profitability metrics and tax liability during inflationary periods.",
                    'keyPoints': [
                        "Analyze complex accounting treatments",
                        "Adjust financial statements for comparison",
                        "Understand the impact of accounting choices on ratios"
                    ]
                },
                3: {
                    'title': "Financial Statement Analysis in Portfolio Decisions (Level III)",
                    'explanation': "At Level III, FSA supports equity selection and credit analysis within portfolio management frameworks.",
                    'realWorldExample': "A credit analyst evaluates a company's ability to service debt obligations by analyzing cash flow patterns, leverage ratios, and quality of earnings.",
                    'keyPoints': [
                        "Apply FSA to investment decisions",
                        "Evaluate credit risk using financial statements",
                        "Assess earnings quality in equity analysis"
                    ]
                }
            },
            'Corporate Finance': {
                1: {
                    'title': "Corporate Finance (Level I)",
                    'explanation': "Corporate Finance covers capital budgeting, cost of capital, and working capital management. Understanding NPV, IRR, and payback period is essential for evaluating investment projects.",
                    'realWorldExample': "A company evaluates whether to invest in new manufacturing equipment by calculating the NPV of expected cash flows over the equipment's useful life.",
                    'keyPoints': [
                        "Calculate NPV, IRR, and payback period",
                        "Determine weighted average cost of capital",
                        "Manage working capital efficiently"
                    ]
                },
                2: {
                    'title': "Capital Budgeting and Corporate Strategy (Level II)",
                    'explanation': "At Level II, corporate finance concepts are applied to valuation models. Capital structure decisions and dividend policies affect firm value.",
                    'realWorldExample': "An analyst assesses how a company's decision to increase leverage affects its cost of capital and ultimately shareholder value.",
                    'keyPoints': [
                        "Apply capital budgeting to valuation",
                        "Analyze capital structure decisions",
                        "Evaluate dividend and share repurchase policies"
                    ]
                },
                3: {
                    'title': "Corporate Finance in Portfolio Management (Level III)",
                    'explanation': "At Level III, corporate finance principles inform equity investment decisions and ESG considerations in portfolio construction.",
                    'realWorldExample': "An ESG-focused fund evaluates companies based on governance practices, capital allocation efficiency, and long-term value creation.",
                    'keyPoints': [
                        "Evaluate corporate governance in investment decisions",
                        "Assess capital allocation effectiveness",
                        "Integrate ESG factors in equity analysis"
                    ]
                }
            },
            'Equity Investments': {
                1: {
                    'title': "Equity Investments (Level I)",
                    'explanation': "Equity Investments covers securities markets, market organization, and security valuation principles. Understanding market efficiency and behavioral finance concepts is important.",
                    'realWorldExample': "An investor chooses between actively managed funds and passive index funds based on beliefs about market efficiency and costs.",
                    'keyPoints': [
                        "Understand market structures and mechanisms",
                        "Recognize different types of orders and costs",
                        "Distinguish between efficient and inefficient markets"
                    ]
                },
                2: {
                    'title': "Equity Valuation (Level II)",
                    'explanation': "At Level II, focus on equity valuation models including dividend discount models, free cash flow models, and relative valuation approaches.",
                    'realWorldExample': "An analyst uses a two-stage dividend discount model to value a mature utility stock with predictable dividend growth.",
                    'keyPoints': [
                        "Apply various equity valuation models",
                        "Calculate and interpret price multiples",
                        "Understand growth models and their applications"
                    ]
                },
                3: {
                    'title': "Equity Portfolio Management (Level III)",
                    'explanation': "At Level III, equity concepts support portfolio construction, rebalancing decisions, and implementation strategies.",
                    'realWorldExample': "A portfolio manager constructs an equity portfolio with specific factor exposures (value, size, momentum) to achieve desired risk-return characteristics.",
                    'keyPoints': [
                        "Construct equity portfolios based on investment objectives",
                        "Implement equity strategies effectively",
                        "Monitor and rebalance equity portfolios"
                    ]
                }
            },
            'Fixed Income': {
                1: {
                    'title': "Fixed Income (Level I)",
                    'explanation': "Fixed Income covers basic bond concepts including pricing, yield measures, and risk factors. Understanding duration and convexity is crucial for bond analysis.",
                    'realWorldExample': "An investor evaluates bonds with different maturities and coupons to select those offering the best risk-adjusted returns given expected interest rate movements.",
                    'keyPoints': [
                        "Calculate bond prices and yields",
                        "Understand interest rate risk and duration",
                        "Recognize different types of bonds and their features"
                    ]
                },
                2: {
                    'title': "Fixed Income Valuation (Level II)",
                    'explanation': "At Level II, focus on yield spreads, term structure of interest rates, and credit analysis. Mortgage-backed securities and their complexities are introduced.",
                    'realWorldExample': "An analyst evaluates mortgage-backed securities considering prepayment risk and how changes in interest rates affect cash flows.",
                    'keyPoints': [
                        "Analyze yield spreads and credit risk",
                        "Understand term structure theories",
                        "Evaluate complex fixed income securities"
                    ]
                },
                3: {
                    'title': "Fixed Income Portfolio Management (Level III)",
                    'explanation': "At Level III, fixed income concepts support asset allocation, liability-driven investing, and risk management strategies.",
                    'realWorldExample': "A pension fund uses immunization strategies to match asset and liability durations, reducing interest rate risk.",
                    'keyPoints': [
                        "Construct fixed income portfolios for specific objectives",
                        "Implement immunization and hedging strategies",
                        "Manage credit and interest rate risks"
                    ]
                }
            },
            'Derivatives': {
                1: {
                    'title': "Derivatives (Level I)",
                    'explanation': "Derivatives introduces forwards, futures, options, and swaps. Understanding the basic characteristics and uses of each instrument is important.",
                    'realWorldExample': "An investor uses put options to hedge against potential losses in a stock portfolio while maintaining upside participation.",
                    'keyPoints': [
                        "Understand basic derivative instruments",
                        "Recognize uses of derivatives (hedging, speculation)",
                        "Calculate payoffs for basic derivative positions"
                    ]
                },
                2: {
                    'title': "Derivative Valuation (Level II)",
                    'explanation': "At Level II, focus on derivative pricing models including binomial trees and Black-Scholes-Merton model. Arbitrage concepts are emphasized.",
                    'realWorldExample': "An analyst calculates the theoretical value of an option using the Black-Scholes model and identifies arbitrage opportunities if market prices deviate significantly.",
                    'keyPoints': [
                        "Apply derivative pricing models",
                        "Understand arbitrage relationships",
                        "Calculate implied volatility and Greeks"
                    ]
                },
                3: {
                    'title': "Derivatives in Portfolio Management (Level III)",
                    'explanation': "At Level III, derivatives support portfolio implementation, risk management, and alternative beta strategies.",
                    'realWorldExample': "A portfolio manager uses equity index futures to gain market exposure quickly while maintaining cash for individual security purchases.",
                    'keyPoints': [
                        "Implement portfolio strategies with derivatives",
                        "Manage risk using derivatives",
                        "Create synthetic positions with derivatives"
                    ]
                }
            },
            'Alternative Investments': {
                1: {
                    'title': "Alternative Investments (Level I)",
                    'explanation': "Alternative Investments covers real estate, commodities, hedge funds, and private equity. Understanding the characteristics and risk-return profiles of alternatives is important.",
                    'realWorldExample': "An institutional investor allocates part of portfolio to real estate investment trusts (REITs) for diversification and inflation protection.",
                    'keyPoints': [
                        "Recognize different alternative investment categories",
                        "Understand benefits and risks of alternatives",
                        "Calculate returns for alternative investments"
                    ]
                },
                2: {
                    'title': "Alternative Investment Strategies (Level II)",
                    'explanation': "At Level II, focus on due diligence for alternative investments and understanding the unique characteristics of each category.",
                    'realWorldExample': "An allocator evaluates a hedge fund's strategy, fees, and risk factors to determine its appropriateness for a diversified portfolio.",
                    'keyPoints': [
                        "Conduct due diligence on alternative investments",
                        "Evaluate alternative investment strategies",
                        "Understand fee structures and their impacts"
                    ]
                },
                3: {
                    'title': "Alternative Investments in Portfolio Construction (Level III)",
                    'explanation': "At Level III, alternatives are integrated into asset allocation and liability-driven investing strategies.",
                    'realWorldExample': "A pension fund incorporates commodities and REITs into its strategic asset allocation to improve diversification and inflation hedging.",
                    'keyPoints': [
                        "Integrate alternatives into asset allocation",
                        "Evaluate alternatives for specific portfolio objectives",
                        "Assess liquidity and operational risks"
                    ]
                }
            },
            'Portfolio Management': {
                1: {
                    'title': "Portfolio Management Concepts (Level I)",
                    'explanation': "Portfolio Management introduces modern portfolio theory, risk and return concepts, and the importance of diversification. Understanding the efficient frontier is fundamental.",
                    'realWorldExample': "An investor builds a diversified portfolio of stocks and bonds to reduce risk while achieving target returns, based on correlation between assets.",
                    'keyPoints': [
                        "Understand risk and return relationships",
                        "Recognize benefits of diversification",
                        "Apply modern portfolio theory concepts"
                    ]
                },
                2: {
                    'title': "Portfolio Management Applications (Level II)",
                    'explanation': "At Level II, portfolio concepts are applied to security selection and market efficiency. Behavioral aspects of portfolio management are introduced.",
                    'realWorldExample': "An analyst evaluates active versus passive investment strategies considering market efficiency and implementation costs.",
                    'keyPoints': [
                        "Apply portfolio theory to security analysis",
                        "Evaluate market efficiency implications",
                        "Consider behavioral factors in investing"
                    ]
                },
                3: {
                    'title': "Integrated Portfolio Management (Level III)",
                    'explanation': "At Level III, portfolio management encompasses the complete investment process from policy statement through implementation and monitoring.",
                    'realWorldExample': "A wealth advisor develops an investment policy statement for a client considering risk tolerance, constraints, and objectives, then implements and monitors the portfolio.",
                    'keyPoints': [
                        "Develop comprehensive investment policy statements",
                        "Implement portfolio strategies effectively",
                        "Monitor and rebalance portfolios regularly"
                    ]
                }
            }
        }

        # Return the explanation for the requested topic and level, or a default if not available
        if topic in explanations and current_level in explanations[topic]:
            return explanations[topic][current_level]
        else:
            return {
                'title': f'{topic} (Level {current_level})',
                'explanation': f'This topic covers fundamental concepts in {topic.lower()} at CFA Level {current_level}. Focus on understanding core principles, key formulas, and their applications in investment analysis.',
                'realWorldExample': f'In practice, {topic.lower()} concepts are applied when making investment decisions, conducting analysis, or managing portfolios.',
                'keyPoints': [
                    "Review the fundamental concepts thoroughly",
                    "Practice applying concepts to scenarios",
                    "Understand the practical applications"
                ]
            }


def main():
    """Main command-line interface for the CFA Study Manager."""
    import sys
    
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    cfa_manager = CFAStudyManager()

    if command == 'profile':
        profile = cfa_manager.get_profile()
        print('CFA Study Profile:')
        print(f'Current Level: {profile["currentLevel"]}')
        print(f'Target Exam Date: {profile["targetExamDate"] or "Not set"}')
        print(f'Study Hours: {profile["studyHours"]}')
        print(f'Completed Levels: {", ".join(map(str, profile["completedLevels"])) or "None"}')
        print(f'Current Streak: {profile["streak"]} days')
        print(f'Overall Performance: {profile["overallPerformance"]}%')
        print(f'Tutor Mode: {"ON" if profile["tutorMode"] else "OFF"}')

    elif command == 'set-level':
        if not args:
            print('Usage: cfa-study set-level <1|2|3>')
            sys.exit(1)
        
        try:
            level = int(args[0])
            if cfa_manager.set_current_level(level):
                print(f'Current level set to: {level}')
            else:
                print('Invalid level. Please enter 1, 2, or 3.')
        except ValueError:
            print('Invalid level. Please enter 1, 2, or 3.')
    
    elif command == 'set-target-date':
        if not args:
            print('Usage: cfa-study set-target-date YYYY-MM-DD')
            sys.exit(1)
        
        if cfa_manager.set_target_exam_date(args[0]):
            print(f'Target exam date set to: {args[0]}')
        else:
            print('Invalid date format. Please use YYYY-MM-DD.')

    elif command == 'enable-tutor':
        cfa_manager.set_tutor_mode(True)
        print('Tutor mode enabled! You now have access to personalized tutoring features.')

    elif command == 'disable-tutor':
        cfa_manager.set_tutor_mode(False)
        print('Tutor mode disabled.')

    elif command == 'tutor-plan':
        tutor_plan = cfa_manager.generate_study_plan()
        print(f'Tutor Mode - Personalized Study Plan for Level {tutor_plan["level"]}:')
        print(f'Focus Strategy: {tutor_plan["focusStrategy"]}')
        print(f'Duration: {tutor_plan["weeks"]} weeks')
        print(f'Daily Study Time: {tutor_plan["dailyHours"]} hours')
        print('\nRecommended Topics to Focus On:')
        for i, topic in enumerate(tutor_plan['topics'], 1):
            print(f'{i}. {topic["topic"]} (Current Progress: {topic["progress"]:.1f}h)')

    elif command == 'tutor-explain':
        if not args:
            print('Usage: cfa-study tutor-explain <topic>')
            print('Available topics: Ethics, Quantitative Methods, Economics, Financial Reporting and Analysis, Corporate Finance, Equity Investments, Fixed Income, Derivatives, Alternative Investments, Portfolio Management')
            sys.exit(1)
        
        topic_to_explain = args[0]
        explanation = cfa_manager.generate_tutor_explanation(topic_to_explain)
        
        print(explanation['title'])
        print('=' * len(explanation['title']))
        print(f'\n{explanation["explanation"]}')
        print(f'\nReal-World Example:\n{explanation["realWorldExample"]}')
        print('\nKey Points to Remember:')
        for i, point in enumerate(explanation['keyPoints'], 1):
            print(f'  {i}. {point}')

    elif command == 'quiz':
        if len(args) < 2:
            print('Usage: cfa-study quiz <topic> <level> [question_index]')
            print('Available topics: Ethics, Quantitative Methods, Economics, Financial Reporting and Analysis, Corporate Finance, Equity Investments, Fixed Income, Derivatives, Alternative Investments, Portfolio Management')
            sys.exit(1)
        
        quiz_topic = args[0]
        try:
            quiz_level = int(args[1])
        except ValueError:
            print('Invalid level. Please enter a number.')
            sys.exit(1)
        
        question_index = int(args[2]) - 1 if len(args) > 2 else 0  # 1-indexed input
        
        quiz_questions = cfa_manager.get_practice_questions(quiz_topic, quiz_level, 10)  # Get up to 10 questions
        
        if question_index >= len(quiz_questions):
            print(f'Question index out of range. Only {len(quiz_questions)} questions available.')
            sys.exit(1)
        
        question = quiz_questions[question_index]
        print(f'Question {question_index + 1}: {question["question"]}')
        for i, option in enumerate(question['options']):
            print(f'  {chr(65 + i)}. {option}')
        print(f'\nSubmit your answer as: cfa-study answer {quiz_topic} {quiz_level} {question_index + 1} <A/B/C/D>')

    elif command == 'answer':
        if len(args) < 4:
            print('Usage: cfa-study answer <topic> <level> <question_number> <A/B/C/D>')
            sys.exit(1)
        
        answer_topic = args[0]
        try:
            answer_level = int(args[1])
            answer_question_num = int(args[2]) - 1  # Convert to 0-indexed
        except ValueError:
            print('Invalid level or question number. Please enter numbers.')
            sys.exit(1)
        
        user_answer = args[3].upper()
        
        # Get the question to check the correct answer
        answer_questions = cfa_manager.get_practice_questions(answer_topic, answer_level, 10)
        if answer_question_num >= len(answer_questions):
            print('Question number out of range.')
            sys.exit(1)
        
        answer_data = answer_questions[answer_question_num]
        result = cfa_manager.record_practice_session(
            answer_topic, 
            answer_level, 
            user_answer, 
            answer_data['answer']
        )
        
        print(f'Your answer: {user_answer}')
        print(f'Correct answer: {answer_data["answer"]}')
        if result['correct']:
            print('✅ Correct!')
        else:
            print('❌ Incorrect.')
            print(f'💡 Explanation: {answer_data["explanation"]}')
        print(f'\nYour overall performance: {result["performance"]:.1f}% ({cfa_manager.profile["correctAnswers"]}/{cfa_manager.profile["totalQuestionsAnswered"]} correct)')

    elif command == 'log-study':
        if len(args) < 2:
            print('Usage: cfa-study log-study <hours> <topic> [questions_answered] [correct_answers]')
            sys.exit(1)
        
        try:
            study_hours = float(args[0])
            study_topic = args[1]
            study_questions = int(args[2]) if len(args) > 2 else 0
            correct_answers = int(args[3]) if len(args) > 3 else 0
            
            cfa_manager.log_study_session(study_hours, study_topic, study_questions, correct_answers)
            print(f'Study session logged: {study_hours} hours on {study_topic}')
        except ValueError:
            print('Invalid input. Hours and counts must be numbers.')

    elif command == 'topics':
        topic_progress = cfa_manager.get_topic_progress()
        print('Topic Progress:')
        for topic_name, data in topic_progress.items():
            status = '✓ COMPLETED' if data['completed'] else f'Progress: {data["progress"]:.1f}h'
            print(f'{topic_name}: {status}')

    elif command == 'plan':
        study_plan = cfa_manager.get_study_plan()
        print('Suggested Study Plan (Prioritized):')
        if len(study_plan) == 0:
            print('All topics completed for current level!')
        else:
            for i, item in enumerate(study_plan, 1):
                print(f'{i}. {item["topic"]} (Progress: {item["progress"]:.1f}h)')

    elif command == 'complete-level':
        if not args:
            print('Usage: cfa-study complete-level <1|2|3>')
            sys.exit(1)
        
        try:
            level_to_complete = int(args[0])
            if cfa_manager.complete_level(level_to_complete):
                print(f'Level {level_to_complete} marked as completed!')
                if level_to_complete < 3:
                    print(f'Moved to Level {level_to_complete + 1}')
                else:
                    print('Congratulations! You have completed all CFA levels!')
            else:
                print('Invalid level or level already completed.')
        except ValueError:
            print('Invalid level. Please enter 1, 2, or 3.')

    elif command == 'practice':
        if len(args) < 2:
            print('Usage: cfa-study practice <topic> <level> [count]')
            sys.exit(1)
        
        practice_topic = args[0]
        try:
            practice_level = int(args[1])
            count = int(args[2]) if len(args) > 2 else 5
        except ValueError:
            print('Invalid level or count. Please enter numbers.')
            sys.exit(1)
        
        practice_questions = cfa_manager.get_practice_questions(practice_topic, practice_level, count)
        print(f'Practice Questions for {practice_topic} (Level {practice_level}):')
        for i, q in enumerate(practice_questions):
            print(f'\n{i + 1}. {q["question"]}')
            for j, opt in enumerate(q['options']):
                print(f'  {chr(65 + j)}. {opt}')

    else:
        print_help()


def print_help():
    """Print help information."""
    print("""
CFA Study Manager

Usage:
  cfa-study profile                                    View your CFA study profile
  cfa-study set-level <1|2|3>                        Set your current CFA level
  cfa-study set-target-date YYYY-MM-DD                 Set your target exam date
  cfa-study enable-tutor                               Enable tutor mode
  cfa-study disable-tutor                              Disable tutor mode
  cfa-study tutor-plan                                 Get personalized study plan (tutor mode)
  cfa-study tutor-explain <topic>                      Get detailed topic explanation (tutor mode)
  cfa-study quiz <topic> <level> [question_num]        Get a practice question to answer
  cfa-study answer <topic> <level> <question_num> <A/B/C/D>  Submit your answer
  cfa-study log-study <hours> <topic> [questions] [correct]  Log a study session
  cfa-study topics                                     View topic progress
  cfa-study plan                                       View suggested study plan
  cfa-study complete-level <1|2|3>                   Mark a level as completed
  cfa-study practice <topic> <level> [count]          Get practice questions
    """)


if __name__ == '__main__':
    main()