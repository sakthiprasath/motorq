from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from utils.exceptions import ValidationException, ApplicationException
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import asyncpg
from asyncpg.exceptions import UniqueViolationError
import os

from utils.registry import _registry
from utils.exceptions import ValidationException, ApplicationException
from utils.registry import _registry



class ConferencesManager:
    def __init__(self):
        self.app_logger = _registry.get('app_logger')

    async def get_db_connection(self):
        DB_CONFIG = {
            'database': os.getenv('DB_NAME', 'test_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        return await asyncpg.connect(**DB_CONFIG)

    async def book(self, user_id, slot_id, conference_id):

        if not user_id or not slot_id:
            raise ValueError({'error': 'user_id and slot_id are required'})

        conn = await self.get_db_connection()

        try:
            async with conn.transaction():
                # Step 1: Check if the slot has available slots
                slot = await conn.fetchrow(
                    "SELECT available_slots FROM conference_slots WHERE slot_id = $1 AND conference_id = $2 FOR UPDATE SKIP LOCKED",
                    slot_id, conference_id
                )

                if not slot:
                    raise ValidationException({'error': 'Slot not found'})

                if slot['available_slots'] <= 0:
                    raise ValueError({'error': 'No available slots'})

                # Step 2: Insert booking
                booking = await conn.fetchrow(
                    """
                    INSERT INTO bookings (conference_id, slot_id, user_id, booking_status)
                    VALUES ($1, $2, $3, 'booked')
                    RETURNING booking_id, booking_time
                    """,
                    conference_id, slot_id, user_id
                )

                # Step 3: Commit the transaction
                await conn.execute("COMMIT")

            return {
                'message': 'Slot booked successfully',
                'booking_id': booking['booking_id'],
                'booking_time': booking['booking_time']
            }

        except Exception as e:
            await conn.execute("ROLLBACK")
            raise e

        finally:
            await conn.close()

    async def add_conference(self, name, description, location, start_date, end_date):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        check_query = """
            SELECT 1 FROM conferences
            WHERE name = $1 AND start_date = $2 AND end_date = $3;
        """

        query = """
            INSERT INTO conferences (name, description, location, start_date, end_date)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING conference_id, name, start_date, end_date;
        """
        conn = await self.get_db_connection()
        try:
            async with conn.transaction():
                # Check if conference already exists
                existing_conference = await conn.fetchrow(check_query, name, start_date, end_date)
                if existing_conference:
                    raise ValueError(f"Conference with name '{name}' and the given dates already exists.")

                conference = await conn.fetchrow(query, name, description, location, start_date, end_date)
                res = {}
                for key, value in conference.items():
                    res[key] = value

                return res

        except Exception as e:
            self.app_logger.error(f"An error occurred: {str(e)}.")
            # Handle the unique violation error, e.g., inform the user, log the error, retry the operation, etc.
            raise ApplicationException(message=str(e))
        finally:
            await conn.close()

    async def add_conference_slot(self, conference_id, slot_time, available_slots, capacity):
        slot_time = datetime.strptime(slot_time, '%Y-%m-%d %H:%M:%S')
        # Check if the conference exists
        conference_check_query = """
              SELECT conference_id FROM conferences
              WHERE conference_id = $1;
          """

        # Check if there's an existing slot with the same conference_id and slot_time
        check_query = """
              SELECT slot_id FROM conference_slots
              WHERE conference_id = $1 AND slot_time = $2;
          """
        conn = await self.get_db_connection()

        try:
            async with conn.transaction():
                conference_exists = await conn.fetchrow(conference_check_query, conference_id)
                if not conference_exists:
                    raise ValueError(f'Conference with ID {conference_id} does not exist.')

                # First, check for an existing slot to prevent conflicts
                existing_slot = await conn.fetchrow(check_query, conference_id, slot_time)
                if existing_slot:
                    raise ApplicationException(message="Conference slot already exists for the given time.")

                insert_query = """
                    INSERT INTO conference_slots (conference_id, slot_time, capacity, available_slots)
                    VALUES ($1, $2, $3, $4)
                    RETURNING slot_id, created_at;
                """
                conn = await self.get_db_connection()


                slot = await conn.fetchrow(insert_query, conference_id, slot_time, capacity, available_slots)
                return {
                    'slot_id': slot['slot_id'],
                    'created_at': slot['created_at'],
                    'message': 'Conference slot created successfully'
                }
        except Exception as e:
            self.app_logger.error(f"An error occurred: {str(e)}.")
            # Handle the unique violation error, e.g., inform the user, log the error, retry the operation, etc.
            raise ApplicationException(message=str(e))

        finally:
            await conn.close()

    async def list_all_conference_slots(self):
        # Query to select all conference slots
        select_query = """
              SELECT 
                conference_slots.slot_id, 
                conference_slots.conference_id, 
                conference_slots.slot_time, 
                conference_slots.capacity, 
                conference_slots.available_slots,
                conference_slots.created_at,
                conferences.name AS conference_name
            FROM 
                conference_slots
            JOIN 
                conferences ON conference_slots.conference_id = conferences.conference_id;

          """
        conn = await self.get_db_connection()

        try:
            async with conn.transaction():
                # Retrieve all slots
                slots = await conn.fetch(select_query)

                # Transform rows into a list of dictionaries
                slots_list = []
                for slot in slots:
                    slots_list.append({
                        'slot_id': slot['slot_id'],
                        'conference_id': slot['conference_id'],
                        'slot_time': slot['slot_time'],
                        'capacity': slot['capacity'],
                        'available_slots': slot['available_slots'],
                        'created_at': slot['created_at'],
                        'conference_name': slot['conference_name'],

                    })
                return slots_list

        except Exception as e:
            self.app_logger.error(f"An error occurred while retrieving conference slots: {str(e)}.")
            raise ApplicationException(message=str(e))

        finally:
            await conn.close()

    async def get_conferences(self):
        query = "SELECT * FROM conferences ORDER BY start_date"
        conn = await self.get_db_connection()
        try:
            conferences = await conn.fetch(query)

            _conferences = []
            for conference in conferences:
                res = {}
                for key, value in conference.items():
                    res[key] = value
                _conferences.append(res)

            return _conferences
        except Exception as e:
            raise e
        finally:
            await conn.close()

    async def get_bookings_by_user(self, user_id):
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
                b.user_id = $1;
        """
        conn = await self.get_db_connection()
        try:
            bookings = await conn.fetch(query, user_id)
            _bookings = []
            for booking in bookings:
                res = {}
                for key, value in booking.items():
                    res[key] = value
                _bookings.append(res)

            return _bookings
        except Exception as e:
            raise e
        finally:
            await conn.close()

    async def cancel_booking(self, user_id, booking_id):
        query = """
            UPDATE bookings
            SET booking_status = 'canceled', canceled_time = CURRENT_TIMESTAMP
            WHERE booking_id = $1 AND user_id = $2 AND booking_status != 'canceled'
            RETURNING booking_id;
        """
        conn = await self.get_db_connection()
        try:
            async with conn.transaction():
                result = await conn.fetchrow(query, booking_id, user_id)
                return result['booking_id'] if result else None
        except Exception as e:
            raise e
        finally:
            await conn.close()



class InitDb:
    SQL_FILE_PATH = "db/relations.sql"
    def execute_sql_file(self, conn, path):
        """
        Executes the SQL statements in the given file.
        """
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        with open(path, 'r') as sql_file:
            sql_script = sql_file.read()
        # Splitting the script into separate commands based on semicolon and newline
        # sql_commands = sql_script.split(';')
        # for command in sql_commands:
        #     if command.strip() != '':
        cursor.execute(sql_script)
        conn.commit()
        cursor.close()

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

    def init_db(self, ):
        """
        The main entry of the application.
        """
        # Connect to the database
        conn = self.get_db_connection()
        if conn is not None:
            print("Connection successful.")
            # Execute SQL file
            self.execute_sql_file(conn, self.SQL_FILE_PATH)
            print("SQL script executed successfully.")
            # Close the connection
            conn.close()
        else:
            print("Failed to connect to the database.")
