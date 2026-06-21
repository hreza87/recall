# =============================================================================
# tests/test_adaptive.py
# -----------------------------------------------------------------------------
# These tests check the most important logic: the adaptive algorithm and the
# accuracy calculation. They use a temporary in-memory database so they never
# touch the real recall.db file.
#
# Run them from the project folder with:   python -m unittest
# =============================================================================

import os
import sys
import unittest
from datetime import datetime, timedelta

# Make sure Python can find the files in the folder above this one.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask

from models import database, User, Topic, Question, Response, ScheduleState
from adaptive import (
    get_or_create_schedule_state,
    calculate_weight,
    update_schedule_after_answer,
    LOWEST_BOX,
    HIGHEST_BOX,
)
from reporting import calculate_topic_accuracy


def build_test_app():
    """Create a tiny Flask app that uses an in-memory database for testing."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    database.init_app(app)
    return app


class AdaptiveAlgorithmTests(unittest.TestCase):

    def setUp(self):
        """Run before every test: make a fresh database with one question."""
        self.app = build_test_app()
        self.context = self.app.app_context()
        self.context.push()
        database.create_all()

        self.student = User(username="s", password_hash="x", role="student")
        self.topic = Topic(name="Test Topic")
        database.session.add(self.student)
        database.session.add(self.topic)
        database.session.commit()

        self.question = Question(
            topic_id=self.topic.id,
            question_text="Q",
            option_a="a", option_b="b", option_c="c", option_d="d",
            correct_option="A", difficulty=1,
        )
        database.session.add(self.question)
        database.session.commit()

    def tearDown(self):
        """Run after every test: throw the database away."""
        database.session.remove()
        database.drop_all()
        self.context.pop()

    def test_new_state_starts_in_box_one(self):
        state = get_or_create_schedule_state(self.student.id, self.question.id)
        self.assertEqual(state.box, LOWEST_BOX)
        self.assertEqual(state.times_seen, 0)

    def test_correct_answer_moves_up_a_box(self):
        state = get_or_create_schedule_state(self.student.id, self.question.id)
        update_schedule_after_answer(state, was_correct=True)
        self.assertEqual(state.box, 2)
        self.assertEqual(state.times_seen, 1)

    def test_wrong_answer_drops_back_to_box_one(self):
        state = get_or_create_schedule_state(self.student.id, self.question.id)
        # First push it up a couple of boxes with correct answers.
        update_schedule_after_answer(state, was_correct=True)
        update_schedule_after_answer(state, was_correct=True)
        self.assertEqual(state.box, 3)
        # Now a wrong answer should reset it to box 1.
        update_schedule_after_answer(state, was_correct=False)
        self.assertEqual(state.box, LOWEST_BOX)

    def test_box_never_goes_above_highest(self):
        state = get_or_create_schedule_state(self.student.id, self.question.id)
        for repeat in range(10):
            update_schedule_after_answer(state, was_correct=True)
        self.assertEqual(state.box, HIGHEST_BOX)

    def test_weak_question_has_higher_weight_than_strong_one(self):
        # A box 1 (weak), overdue question should weigh more than a box 5
        # (strong) question that is not due.
        weak_state = ScheduleState(
            user_id=self.student.id, question_id=self.question.id,
            box=1, due_at=datetime.now() - timedelta(days=1), times_seen=1,
        )
        strong_state = ScheduleState(
            user_id=self.student.id, question_id=self.question.id,
            box=5, due_at=datetime.now() + timedelta(days=10), times_seen=5,
        )
        weak_weight = calculate_weight(weak_state)
        strong_weight = calculate_weight(strong_state)
        self.assertGreater(weak_weight, strong_weight)


class ReportingTests(unittest.TestCase):

    def setUp(self):
        self.app = build_test_app()
        self.context = self.app.app_context()
        self.context.push()
        database.create_all()

        self.student = User(username="s", password_hash="x", role="student")
        self.topic = Topic(name="Test Topic")
        database.session.add(self.student)
        database.session.add(self.topic)
        database.session.commit()

        self.question = Question(
            topic_id=self.topic.id,
            question_text="Q",
            option_a="a", option_b="b", option_c="c", option_d="d",
            correct_option="A", difficulty=1,
        )
        database.session.add(self.question)
        database.session.commit()

    def tearDown(self):
        database.session.remove()
        database.drop_all()
        self.context.pop()

    def test_accuracy_with_no_answers_is_zero(self):
        percentage, number_answered = calculate_topic_accuracy(
            self.student.id, self.topic.id
        )
        self.assertEqual(percentage, 0)
        self.assertEqual(number_answered, 0)

    def test_accuracy_counts_correct_answers(self):
        # Two correct, one wrong => 2/3 => 67%.
        database.session.add(Response(
            user_id=self.student.id, question_id=self.question.id,
            was_correct=True, answered_at=datetime.now(),
        ))
        database.session.add(Response(
            user_id=self.student.id, question_id=self.question.id,
            was_correct=True, answered_at=datetime.now(),
        ))
        database.session.add(Response(
            user_id=self.student.id, question_id=self.question.id,
            was_correct=False, answered_at=datetime.now(),
        ))
        database.session.commit()

        percentage, number_answered = calculate_topic_accuracy(
            self.student.id, self.topic.id
        )
        self.assertEqual(number_answered, 3)
        self.assertEqual(percentage, 67)


if __name__ == "__main__":
    unittest.main()
