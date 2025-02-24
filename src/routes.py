from flask import Flask, request, jsonify
import asyncio
import threading
from flask import jsonify
from flask_smorest import Blueprint
from utils.registry import _registry
from conferences_manager import ConferencesManager

import psycopg2
from flask import Flask, request, jsonify
from psycopg2 import sql
from psycopg2.extras import RealDictCursor


conference_booking_route = Blueprint('conference-service', __name__, url_prefix='/api/conferences')

conferences = {
    1: {"name": "TechConf", "seats": 50, "booked_seats": 0},
    2: {"name": "AI Summit", "seats": 100, "booked_seats": 0},
}

lock = threading.Lock()  # Use a lock for thread safety


@conference_booking_route.route('book', methods=['POST'])
def book_slot():
    data = request.get_json(force=True)
    user_id = data.get('user_id')
    slot_id = data.get('slot_id')
    conference_id = data.get('conference_id')

    conferences_manager = ConferencesManager()
    res = conferences_manager.book(user_id, slot_id, conference_id)

    return res


@conference_booking_route.route('', methods=['POST'])
def add_conference():
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
        conference = conferences_manager.add_conference(name, description, location, start_date, end_date)
        return jsonify({
            'message': 'Conference added successfully',
            'conference': conference
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conference_booking_route.route('slots', methods=['POST'])
def create_conference_slot():
    data = request.json

    # Extract values from request body
    conference_id = data.get('conference_id')
    slot_time = data.get('slot_time')
    capacity = data.get('capacity')
    available_slots = data.get('available_slots')

    if not conference_id or not slot_time or not capacity or available_slots is None:
        return jsonify({'error': 'Missing required fields'}), 400

    conferences_manager = ConferencesManager()
    res = conferences_manager.add_conference_slot(conference_id, slot_time, available_slots, capacity)
    return res


@conference_booking_route.route('', methods=['GET'])
def list_conferences():
    try:
        conferences_manager = ConferencesManager()
        conferences = conferences_manager.get_conferences()
        return jsonify({
            'conferences': conferences
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conference_booking_route.route('bookings/<int:user_id>', methods=['GET'])
def list_bookings_by_user(user_id):
    try:
        conferences_manager = ConferencesManager()
        # Fetch bookings for the given user_id
        bookings = conferences_manager.get_bookings_by_user(user_id)

        if not bookings:
            return jsonify({'message': 'No bookings found for the specified user'}), 404

        return jsonify({
            'bookings': bookings
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conference_booking_route.route('bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    try:
        # Get user_id from request body (assuming JSON input)
        user_id = request.json.get('user_id')

        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        # Call the cancel booking function in ConferencesManager
        conferences_manager = ConferencesManager()
        canceled_booking_id = conferences_manager.cancel_booking(user_id, booking_id)

        if canceled_booking_id:
            return jsonify({
                'message': 'Booking canceled successfully',
                'booking_id': canceled_booking_id
            }), 200
        else:
            return jsonify({
                'message': 'Booking not found or already canceled, or you are not the owner of this booking'
            }), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Root endpoint
@conference_booking_route.route('/')
def index():
    return jsonify({"message": "Welcome to the Conference Booking API!"})
