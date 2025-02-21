import psycopg2
from psycopg2.extras import RealDictCursor
from utils.exceptions import ValidationException
import os

class ConferencesManager:

    def get_db_connection(self):
        DB_CONFIG = {
            'dbname': os.getenv('DB_NAME', 'test_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        conn = psycopg2.connect(**DB_CONFIG)
        return conn

    def book(self, user_id, slot_id, conference_id):

        if not user_id or not slot_id:
            return ValidationException({'error': 'user_id and slot_id are required'}), 400

        # Step 1: Check if the slot has available slots
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT available_slots FROM conference_slots WHERE slot_id = %s and conference_id=%s FOR UPDATE",
                    (slot_id,conference_id,)
                )
                slot = cursor.fetchone()

                if not slot:
                    return ValidationException({'error': 'Slot not found'}), 404

                if slot['available_slots'] <= 0:
                    return ValidationException({'error': 'No available slots'}), 400

                # Step 2: Insert booking
                cursor.execute(
                    """
                    INSERT INTO bookings (conference_id, slot_id, user_id, booking_status)
                    VALUES (%s, %s, %s, 'booked')
                    RETURNING booking_id, booking_time
                    """,
                    (conference_id, slot_id, user_id)
                )
                booking = cursor.fetchone()

                # Step 3: Update available slots
                # taken care by trigger

                conn.commit()
            return {
                'message': 'Slot booked successfully',
                'booking_id': booking['booking_id'],
                'booking_time': booking['booking_time']
            }
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

    def add_conference(self, name, description, location, start_date, end_date):
        query = """
            INSERT INTO conferences (name, description, location, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING conference_id, name, start_date, end_date;
        """
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (name, description, location, start_date, end_date))
                conference = cursor.fetchone()
                conn.commit()
                return conference
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_conferences(self):
        query = "SELECT * FROM conferences ORDER BY start_date"
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                conferences = cursor.fetchall()
                return conferences
        except Exception as e:
            raise e
        finally:
            conn.close()


    def get_bookings_by_user(self, user_id):
        query = """
            SELECT 
                b.booking_id, 
                u.name as user_name, 
                u.email as user_email, 
                c.name as conference_name, 
                c.description as conference_description, 
                c.location as conference_location, 
                c.start_date, 
                c.end_date, 
                b.booking_status
            FROM 
                bookings b
            JOIN 
                users u ON b.user_id = u.user_id
            JOIN 
                conferences c ON b.conference_id = c.conference_id
            WHERE 
                b.user_id = %s;
        """
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (user_id,))
                bookings = cursor.fetchall()
                return bookings
        except Exception as e:
            raise e
        finally:
            conn.close()

    def cancel_booking(self, user_id, booking_id):
        query = """
            UPDATE bookings
            SET booking_status = 'canceled', canceled_time = CURRENT_TIMESTAMP
            WHERE booking_id = %s AND user_id = %s AND booking_status != 'canceled'
            RETURNING booking_id;
        """
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (booking_id, user_id))
                result = cursor.fetchone()
                if result:
                    return result[0]  # Return the booking_id of the canceled booking
                else:
                    return None  # If no rows were updated (wrong user, already canceled, or invalid booking)
        except Exception as e:
            raise e
        finally:
            conn.close()

