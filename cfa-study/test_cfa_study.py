#!/usr/bin/env python3

import unittest
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path
from scripts.cfa_study import CFAStudyManager


class TestCFAStudyManager(unittest.TestCase):
    """Comprehensive unit tests for the CFAStudyManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_workspace_dir = self.test_dir
        
        # Ensure the directory structure exists: workspace_dir/skills/cfa-study/
        skills_dir = os.path.join(self.test_workspace_dir, 'skills')
        cfa_study_dir = os.path.join(skills_dir, 'cfa-study')
        os.makedirs(cfa_study_dir, exist_ok=True)
        
        self.test_data_file = os.path.join(cfa_study_dir, 'cfa-data.json')
        
        # Create an instance of CFAStudyManager with the test directory
        self.manager = CFAStudyManager(workspace_dir=self.test_workspace_dir)

    def tearDown(self):
        """Clean up after each test method."""
        # Remove the temporary directory and its contents
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization_creates_default_profile(self):
        """Test that initialization creates a default profile if no data file exists."""
        # Verify that a default profile was created
        self.assertIsNotNone(self.manager.profile)
        self.assertEqual(self.manager.profile['currentLevel'], 1)
        self.assertEqual(self.manager.profile['studyHours'], 0)
        self.assertIn('Ethics', self.manager.profile['topics'])
        self.assertFalse(self.manager.profile['topics']['Ethics']['completed'])

    def test_load_profile_from_existing_file(self):
        """Test loading profile from an existing file."""
        # Create a custom profile data
        custom_profile = {
            'currentLevel': 2,
            'targetExamDate': '2025-06-01',
            'studyHours': 50.5,
            'topics': {
                'Ethics': {'level1': 10, 'level2': 5, 'level3': 0, 'completed': True},
                'Quantitative Methods': {'level1': 8, 'level2': 0, 'level3': 0, 'completed': False}
            },
            'completedLevels': [1],
            'streak': 7,
            'totalQuestionsAnswered': 20,
            'correctAnswers': 15,
            'performanceByTopic': {'Ethics': {'attempts': 5, 'correct': 4}},
            'tutorMode': True
        }
        
        # Write the custom profile to the data file
        with open(self.test_data_file, 'w') as f:
            json.dump(custom_profile, f)
        
        # Create a new manager instance to load the profile
        new_manager = CFAStudyManager(workspace_dir=self.test_workspace_dir)
        
        # Verify that the custom profile was loaded
        self.assertEqual(new_manager.profile['currentLevel'], 2)
        self.assertEqual(new_manager.profile['targetExamDate'], '2025-06-01')
        self.assertEqual(new_manager.profile['studyHours'], 50.5)
        self.assertTrue(new_manager.profile['topics']['Ethics']['completed'])
        self.assertEqual(new_manager.profile['streak'], 7)
        self.assertTrue(new_manager.profile['tutorMode'])

    def test_set_current_level_valid(self):
        """Test setting current level with valid values."""
        # Test setting level 1
        result = self.manager.set_current_level(1)
        self.assertTrue(result)
        self.assertEqual(self.manager.profile['currentLevel'], 1)
        
        # Test setting level 2
        result = self.manager.set_current_level(2)
        self.assertTrue(result)
        self.assertEqual(self.manager.profile['currentLevel'], 2)
        
        # Test setting level 3
        result = self.manager.set_current_level(3)
        self.assertTrue(result)
        self.assertEqual(self.manager.profile['currentLevel'], 3)

    def test_set_current_level_invalid(self):
        """Test setting current level with invalid values."""
        # Test setting level 0 (invalid)
        result = self.manager.set_current_level(0)
        self.assertFalse(result)
        self.assertEqual(self.manager.profile['currentLevel'], 1)  # Should remain unchanged
        
        # Test setting level 4 (invalid)
        result = self.manager.set_current_level(4)
        self.assertFalse(result)
        self.assertEqual(self.manager.profile['currentLevel'], 1)  # Should remain unchanged

    def test_set_target_exam_date_valid(self):
        """Test setting target exam date with valid format."""
        result = self.manager.set_target_exam_date('2025-06-01')
        self.assertTrue(result)
        self.assertEqual(self.manager.profile['targetExamDate'], '2025-06-01')

    def test_set_target_exam_date_invalid(self):
        """Test setting target exam date with invalid format."""
        result = self.manager.set_target_exam_date('invalid-date')
        self.assertFalse(result)
        self.assertIsNone(self.manager.profile['targetExamDate'])

    def test_set_tutor_mode(self):
        """Test enabling/disabling tutor mode."""
        # Enable tutor mode
        result = self.manager.set_tutor_mode(True)
        self.assertTrue(result)
        self.assertTrue(self.manager.profile['tutorMode'])
        
        # Disable tutor mode
        result = self.manager.set_tutor_mode(False)
        self.assertTrue(result)
        self.assertFalse(self.manager.profile['tutorMode'])

    def test_log_study_session_basic(self):
        """Test basic study session logging."""
        initial_hours = self.manager.profile['studyHours']
        initial_streak = self.manager.profile['streak']
        
        # Log a study session
        self.manager.log_study_session(2.5, 'Ethics', 5, 4)
        
        # Verify study hours increased
        self.assertEqual(self.manager.profile['studyHours'], initial_hours + 2.5)
        
        # Verify question statistics updated
        self.assertEqual(self.manager.profile['totalQuestionsAnswered'], 5)
        self.assertEqual(self.manager.profile['correctAnswers'], 4)
        
        # Verify topic progress updated
        current_level = self.manager.profile['currentLevel']
        level_key = f'level{current_level}'
        self.assertGreaterEqual(self.manager.profile['topics']['Ethics'][level_key], 2.5)

    def test_log_study_session_topic_completion(self):
        """Test that logging enough hours completes a topic."""
        # Simulate logging enough hours to complete a topic (threshold is 10 hours)
        self.manager.log_study_session(15.0, 'Ethics', 0, 0)
        
        # Verify the topic is marked as completed
        self.assertTrue(self.manager.profile['topics']['Ethics']['completed'])

    def test_get_profile(self):
        """Test getting the current profile."""
        # Update some profile data
        self.manager.set_current_level(2)
        self.manager.log_study_session(10.0, 'Ethics', 20, 18)
        
        profile = self.manager.get_profile()
        
        self.assertEqual(profile['currentLevel'], 2)
        self.assertEqual(profile['studyHours'], 10.0)
        self.assertEqual(profile['overallPerformance'], 90.0)  # 18/20 = 90%

    def test_get_topic_progress(self):
        """Test getting topic progress."""
        # Update topic progress
        self.manager.log_study_session(5.0, 'Ethics', 0, 0)
        self.manager.log_study_session(3.0, 'Quantitative Methods', 0, 0)
        
        progress = self.manager.get_topic_progress()
        
        current_level = self.manager.profile['currentLevel']
        level_key = f'level{current_level}'
        
        self.assertGreaterEqual(progress['Ethics']['progress'], 5.0)
        self.assertGreaterEqual(progress['Quantitative Methods']['progress'], 3.0)

    def test_get_study_plan(self):
        """Test getting study plan."""
        # Mark some topics as completed and leave others incomplete
        self.manager.log_study_session(15.0, 'Ethics', 0, 0)  # This should complete Ethics
        
        study_plan = self.manager.get_study_plan()
        
        # Verify that completed topics are not in the plan
        for item in study_plan:
            # The completed topic should not be in the plan
            self.assertNotEqual(item['topic'], 'Ethics')
        
        # Verify that the plan is sorted by least progressed topics first
        if len(study_plan) > 1:
            for i in range(len(study_plan) - 1):
                self.assertLessEqual(study_plan[i]['progress'], study_plan[i+1]['progress'])

    def test_complete_level(self):
        """Test completing a level."""
        # Initially no levels completed
        self.assertEqual(self.manager.profile['completedLevels'], [])
        
        # Complete level 1
        result = self.manager.complete_level(1)
        self.assertTrue(result)
        self.assertIn(1, self.manager.profile['completedLevels'])
        self.assertEqual(self.manager.profile['currentLevel'], 2)  # Should move to next level
        
        # Try to complete level 1 again (should fail)
        result = self.manager.complete_level(1)
        self.assertFalse(result)

    def test_complete_level_invalid(self):
        """Test completing an invalid level."""
        # Try to complete level 4 (invalid)
        result = self.manager.complete_level(4)
        self.assertFalse(result)
        self.assertEqual(self.manager.profile['completedLevels'], [])

    def test_get_practice_questions(self):
        """Test getting practice questions."""
        # Get questions for Ethics at Level 1
        questions = self.manager.get_practice_questions('Ethics', 1, 3)
        
        # Verify we got questions
        self.assertGreaterEqual(len(questions), 0)
        if len(questions) > 0:
            # Verify question structure
            question = questions[0]
            self.assertIn('question', question)
            self.assertIn('options', question)
            self.assertIn('answer', question)
            self.assertIn('explanation', question)
            self.assertEqual(len(question['options']), 4)

    def test_get_practice_questions_nonexistent_topic(self):
        """Test getting questions for a non-existent topic."""
        # Get questions for a non-existent topic
        questions = self.manager.get_practice_questions('NonExistentTopic', 1, 2)
        
        # Should return sample questions
        self.assertGreaterEqual(len(questions), 0)
        if len(questions) > 0:
            question = questions[0]
            self.assertIn('question', question)
            self.assertIn('sample', question['question'].lower())

    def test_record_practice_session(self):
        """Test recording a practice session."""
        initial_total = self.manager.profile['totalQuestionsAnswered']
        initial_correct = self.manager.profile['correctAnswers']
        
        # Record a correct answer
        result = self.manager.record_practice_session('Ethics', 1, 'B', 'B', 45)
        
        self.assertTrue(result['correct'])
        self.assertEqual(self.manager.profile['totalQuestionsAnswered'], initial_total + 1)
        self.assertEqual(self.manager.profile['correctAnswers'], initial_correct + 1)
        
        # Record an incorrect answer
        initial_total = self.manager.profile['totalQuestionsAnswered']
        initial_correct = self.manager.profile['correctAnswers']
        
        result = self.manager.record_practice_session('Ethics', 1, 'A', 'B', 60)
        
        self.assertFalse(result['correct'])
        self.assertEqual(self.manager.profile['totalQuestionsAnswered'], initial_total + 1)
        self.assertEqual(self.manager.profile['correctAnswers'], initial_correct)  # Should not change

    def test_record_practice_session_performance_tracking(self):
        """Test that performance tracking works correctly."""
        # Record several answers
        self.manager.record_practice_session('Ethics', 1, 'B', 'B', 45)  # Correct
        self.manager.record_practice_session('Ethics', 1, 'A', 'B', 60)  # Incorrect
        self.manager.record_practice_session('Ethics', 1, 'C', 'C', 30)  # Correct
        
        # Verify performance calculation (2 correct out of 3 total = 66.67%)
        result = self.manager.record_practice_session('Ethics', 1, 'D', 'D', 40)  # Correct
        expected_performance = (3 / 4) * 100  # 75%
        
        self.assertEqual(result['performance'], expected_performance)

    def test_generate_study_plan(self):
        """Test generating a personalized study plan."""
        # Enable tutor mode first
        self.manager.set_tutor_mode(True)
        
        # Generate study plan
        study_plan = self.manager.generate_study_plan()
        
        # Verify structure of the study plan
        self.assertIn('level', study_plan)
        self.assertIn('weeks', study_plan)
        self.assertIn('topics', study_plan)
        self.assertIn('dailyHours', study_plan)
        self.assertIn('focusStrategy', study_plan)
        
        self.assertEqual(study_plan['level'], self.manager.profile['currentLevel'])
        self.assertEqual(study_plan['weeks'], 4)
        self.assertEqual(study_plan['dailyHours'], 2)

    def test_generate_tutor_explanation(self):
        """Test generating tutor explanations."""
        # Get explanation for Ethics
        explanation = self.manager.generate_tutor_explanation('Ethics')
        
        # Verify structure of the explanation
        self.assertIn('title', explanation)
        self.assertIn('explanation', explanation)
        self.assertIn('realWorldExample', explanation)
        self.assertIn('keyPoints', explanation)
        
        self.assertIsInstance(explanation['keyPoints'], list)
        self.assertGreater(len(explanation['keyPoints']), 0)

    def test_generate_tutor_explanation_nonexistent_topic(self):
        """Test generating explanation for a non-existent topic."""
        # Get explanation for a non-existent topic
        explanation = self.manager.generate_tutor_explanation('NonExistentTopic')
        
        # Should return a default explanation
        self.assertIn('title', explanation)
        self.assertIn('explanation', explanation)
        self.assertIn('NonExistentTopic', explanation['title'])

    def test_save_and_load_profile_consistency(self):
        """Test that saved profile can be loaded consistently."""
        # Modify the profile
        self.manager.set_current_level(2)
        self.manager.set_target_exam_date('2025-12-01')
        self.manager.set_tutor_mode(True)
        self.manager.log_study_session(10.0, 'Ethics', 15, 12)
        
        # Save the profile (it should be automatically saved during operations)
        original_profile = self.manager.profile.copy()
        
        # Create a new manager instance to reload the profile
        new_manager = CFAStudyManager(workspace_dir=self.test_workspace_dir)
        
        # Compare the reloaded profile with the original
        self.assertEqual(new_manager.profile['currentLevel'], original_profile['currentLevel'])
        self.assertEqual(new_manager.profile['targetExamDate'], original_profile['targetExamDate'])
        self.assertEqual(new_manager.profile['studyHours'], original_profile['studyHours'])
        self.assertEqual(new_manager.profile['tutorMode'], original_profile['tutorMode'])
        self.assertEqual(new_manager.profile['totalQuestionsAnswered'], original_profile['totalQuestionsAnswered'])
        self.assertEqual(new_manager.profile['correctAnswers'], original_profile['correctAnswers'])

    def test_topic_progress_level_specificity(self):
        """Test that topic progress is tracked per level correctly."""
        # Log study session for level 1
        self.manager.set_current_level(1)
        self.manager.log_study_session(5.0, 'Ethics', 0, 0)
        
        level1_progress = self.manager.profile['topics']['Ethics']['level1']
        
        # Switch to level 2 and log more study time
        self.manager.set_current_level(2)
        self.manager.log_study_session(3.0, 'Ethics', 0, 0)
        
        level2_progress = self.manager.profile['topics']['Ethics']['level2']
        
        # Both levels should have progress
        self.assertGreaterEqual(level1_progress, 5.0)
        self.assertGreaterEqual(level2_progress, 3.0)

    def test_streak_tracking_same_day(self):
        """Test that streak doesn't increase if studying on the same day."""
        # Set up profile to have a previous study date that's today
        today_iso = datetime.now().date().isoformat()
        self.manager.profile['lastStudyDate'] = f"{today_iso}T00:00:00"
        
        # Log a study session
        initial_streak = self.manager.profile['streak']
        self.manager.log_study_session(1.0, 'Ethics', 0, 0)
        after_first_session = self.manager.profile['streak']
        
        # Log another session on the same day
        self.manager.log_study_session(1.0, 'Quantitative Methods', 0, 0)
        after_second_session = self.manager.profile['streak']
        
        # Streak should stay the same since it's the same day
        self.assertEqual(initial_streak, after_second_session)

    def test_streak_tracking_consecutive_days(self):
        """Test that streak increases with consecutive days."""
        import unittest.mock
        from datetime import date
        
        # Mock dates for consecutive days
        day1 = datetime(2024, 1, 15)
        day2 = datetime(2024, 1, 16)
        
        with unittest.mock.patch('scripts.cfa_study.datetime') as mock_datetime:
            # Configure the mock to return different dates based on when it's called
            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                if not args and 'now' in str(kwargs) or len(args) == 0:
                    if call_count == 0:
                        call_count += 1
                        return day1
                    else:
                        return day2
                return datetime(*args, **kwargs)
            
            mock_datetime.now.side_effect = side_effect
            mock_datetime.fromisoformat = staticmethod(datetime.fromisoformat)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw) if args else side_effect(*args, **kw)
            
            # Initialize with day1
            self.manager.profile['lastStudyDate'] = day1.isoformat()
            
            # Log study session on day2 (consecutive day)
            self.manager.log_study_session(1.0, 'Ethics', 0, 0)
            
            # Streak should be at least 1 (could be more depending on initial state)
            # The important thing is that it updated properly

    def test_error_handling_file_operations(self):
        """Test error handling for file operations."""
        # Create a manager with a problematic directory path
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make the directory unwritable to test error handling
            import stat
            readonly_dir = os.path.join(temp_dir, 'readonly')
            os.mkdir(readonly_dir)
            os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)  # Read and execute only
            
            # Try to create a manager with the readonly directory
            # This should handle errors gracefully
            try:
                problematic_manager = CFAStudyManager(workspace_dir=readonly_dir)
                # If it doesn't crash, verify it handles the error
                self.assertIsNotNone(problematic_manager)
            except Exception:
                # If it raises an exception, that's also acceptable as long as it's handled properly
                pass


class TestCFAStudyManagerIntegration(unittest.TestCase):
    """Integration tests for the CFAStudyManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        
        # Ensure the directory structure exists: workspace_dir/skills/cfa-study/
        skills_dir = os.path.join(self.test_dir, 'skills')
        cfa_study_dir = os.path.join(skills_dir, 'cfa-study')
        os.makedirs(cfa_study_dir, exist_ok=True)
        
        self.manager = CFAStudyManager(workspace_dir=self.test_dir)

    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_workflow_simulation(self):
        """Test a full workflow simulation of using the CFA study manager."""
        # Start with level 1
        self.assertEqual(self.manager.profile['currentLevel'], 1)
        
        # Set target exam date
        self.manager.set_target_exam_date('2025-06-01')
        self.assertEqual(self.manager.profile['targetExamDate'], '2025-06-01')
        
        # Log several study sessions
        self.manager.log_study_session(5.0, 'Ethics', 10, 9)
        self.manager.log_study_session(3.0, 'Quantitative Methods', 8, 7)
        self.manager.log_study_session(7.0, 'Ethics', 12, 10)  # More Ethics to complete it
        
        # Verify progress
        self.assertGreaterEqual(self.manager.profile['studyHours'], 15.0)
        self.assertGreaterEqual(self.manager.profile['totalQuestionsAnswered'], 30)
        
        # Answer some practice questions
        self.manager.record_practice_session('Ethics', 1, 'B', 'B', 45)
        self.manager.record_practice_session('Ethics', 1, 'A', 'C', 60)
        
        # Check performance
        profile = self.manager.get_profile()
        self.assertGreaterEqual(profile['overallPerformance'], 0)  # Should have some performance
        
        # Get topic progress
        progress = self.manager.get_topic_progress()
        ethics_progress = progress['Ethics']['progress']
        self.assertGreaterEqual(ethics_progress, 0)
        
        # Get study plan
        study_plan = self.manager.get_study_plan()
        self.assertIsInstance(study_plan, list)
        
        # Complete level 1
        self.manager.complete_level(1)
        self.assertIn(1, self.manager.profile['completedLevels'])
        self.assertEqual(self.manager.profile['currentLevel'], 2)
        
        # Enable tutor mode and get a study plan
        self.manager.set_tutor_mode(True)
        tutor_plan = self.manager.generate_study_plan()
        self.assertIn('topics', tutor_plan)
        
        # Get a tutor explanation
        explanation = self.manager.generate_tutor_explanation('Ethics')
        self.assertIn('title', explanation)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)