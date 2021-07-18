import os
from flask import Flask, app, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# GET requests for questions including pagination (every 10 questions).
# This endpoint returns a list of questions, number of total questions,
# current category, categories.


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={r'/*': {'origins': '*'}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        categories_list = {}
        for category in categories:
            categories_list[category.id] = category.type

        return jsonify({
            'success': True,
            'categories': categories_list
        })

    @app.route('/questions')
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        categories = Category.query.all()
        categories_list = {}
        for category in categories:
            categories_list[category.id] = category.type

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': categories_list,
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                question_id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(question_id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
            })

        except BaseException:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(selection)
            })

        except BaseException:
            abort(422)

    # Create a POST endpoint to get questions based on a search term.

    @app.route("/search", methods=['POST'])
    def search_questions():
        body = request.get_json()
        search = body.get('searchTerm', None)
        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.title.ilike('%{}%'.format(search)))
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection.all())
                })
        except BaseException:
            abort(422)

    # Create a GET endpoint to get questions based on category.

    @app.route('/categories/<int:category_id>/questions')
    def questions_category(category_id):
        category = Category.query.filter_by(
            category_id=category_id).one_or_none()

        try:
            if category:
                questions_by_category = Question.query.filter_by(
                    category=str(id)).all()
                current_questions = paginate_questions(
                    request, questions_by_category)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(questions_by_category),
                    'current_category': category.type
                })

        except BaseException:
            abort(422)

    # Create a POST endpoint to get questions to play the quiz.

    @app.route('/quizes', methods=['POST'])
    def quizes():
        body = request.get_json()
        previous_questions = body['previous_questions']
        category = body['quiz_category']
        category_id = int(category['id'])
        try:
            if category_id == 0:
                questions = Question.query.all()
            else:
                questions = Question.query.filter(
                    Question.category == category_id).filter(
                    Question.id.notin_(previous_questions)).all()

            if len(questions) == 0:
                return jsonify({
                    'success': True,
                })

            question = random.choice(questions)
            return jsonify({
                'success': True,
                'question': {
                    "answer": question.answer,
                    "category": question.category,
                    "difficulty": question.difficulty,
                    "id": question.id,
                    "question": question.question
                },
                'previousQuestion': previous_questions
            })

        except BaseException:
            abort(404)

    # Create error handlers for all expected errors

    @ app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @ app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @ app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    return app
