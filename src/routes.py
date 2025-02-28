from flask import Flask, request, jsonify
import asyncio
import threading
from flask import jsonify
from flask_smorest import Blueprint

from auth_manager import token_required
from utils.registry import _registry
from conferences_manager import ConferencesManager, InitDb

import psycopg2
from flask import Flask, request, jsonify
from psycopg2 import sql
from psycopg2.extras import RealDictCursor


conference_booking_route = Blueprint('conference-service', __name__, url_prefix='/api/conferences')


@conference_booking_route.route('book', methods=['POST'])
@token_required
async def book_slot(user_id):
    data = request.get_json(force=True)
    user_id = data.get('user_id')
    slot_id = data.get('slot_id')
    conference_id = data.get('conference_id')

    conferences_manager = ConferencesManager()
    res = await conferences_manager.book(user_id, slot_id, conference_id)

    return res


@conference_booking_route.route('', methods=['POST'])
@token_required
async def add_conference(user_id):
    data = request.json
    name = data.get('name')
    description = data.get('description')
    location = data.get('location')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    # Validate required fields
    if not all([name, start_date, end_date]):
        return jsonify({'error': 'Name, start_date, and end_date are required fields'}), 400

    try:
        conferences_manager = ConferencesManager()
        # Call the ConferencesManager to add the conference
        conference = await conferences_manager.add_conference(name, description, location, start_date, end_date)
        return jsonify({
            'message': 'Conference added successfully',
            'conference': conference
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conference_booking_route.route('slots', methods=['POST'])
@token_required
async def create_conference_slot(user_id):
    data = request.json

    # Extract values from request body
    conference_id = data.get('conference_id')
    slot_time = data.get('slot_time')
    capacity = data.get('capacity')
    available_slots = data.get('available_slots')

    if not conference_id or not slot_time or not capacity or available_slots is None:
        return jsonify({'error': 'Missing required fields'}), 400

    conferences_manager = ConferencesManager()
    res = await conferences_manager.add_conference_slot(conference_id, slot_time, available_slots, capacity)
    return res


@conference_booking_route.route('', methods=['GET'])
@token_required
async def list_conferences(user_id):
    conferences_manager = ConferencesManager()
    conferences = await conferences_manager.get_conferences()
    return jsonify({
        'conferences': conferences
    }), 200


@conference_booking_route.route('/slots', methods=['GET'])
@token_required
async def list_conference_slots(user_id):
    try:
        conferences_manager = ConferencesManager()  # Assuming this manager exists
        slots = await conferences_manager.list_all_conference_slots()
        return jsonify({
            'conference_slots': slots
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conference_booking_route.route('bookings/<int:_user_id>', methods=['GET'])
@token_required
async def list_bookings_by_user(user_id, _user_id):
    if user_id != _user_id:
        raise ValueError("You are not allowed to see other people's bookings")
    conferences_manager = ConferencesManager()
    # Fetch bookings for the given user_id
    bookings = await conferences_manager.get_bookings_by_user(user_id)

    if not bookings:
        return jsonify({'message': 'No bookings found for the specified user'}), 404

    return jsonify({
        'bookings': bookings
    }), 200



@conference_booking_route.route('bookings/<int:booking_id>/cancel', methods=['POST'])
@token_required
async def cancel_booking(user_id, booking_id):
    # Get user_id from request body (assuming JSON input)
    user_id = request.json.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    # Call the cancel booking function in ConferencesManager
    conferences_manager = ConferencesManager()
    canceled_booking_id = await conferences_manager.cancel_booking(user_id, booking_id)

    if canceled_booking_id:
        return jsonify({
            'message': 'Booking canceled successfully',
            'booking_id': canceled_booking_id
        }), 200
    else:
        return jsonify({
            'message': 'Booking not found or already canceled, or you are not the owner of this booking'
        }), 404


@conference_booking_route.route('/init-db', methods=['POST'])
def initialize_database():
    try:
        init_db = InitDb()
        init_db.init_db()  # Assuming this method does not return anything
        return jsonify({"message": "Database initialization completed successfully."}), 201
    except Exception as e:
        # Log the exception, if there's a logging setup
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
